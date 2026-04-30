from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from roundtable_core.protocol.debate_result_builder import build_debate_result_from_artifacts
from roundtable_core.protocol.projections import project_debate_artifacts_to_session, project_room_state_to_session
from roundtable_core.runtime import create_run_dir, resolve_state_root, write_evidence, write_input, write_output, write_summary
from roundtable_core.runtime.state_store import build_run_evidence
from roundtable_core.validation import validate_file


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOM_RUNTIME = ".codex/skills/room-skill/runtime/room_runtime.py"
DEBATE_RUNTIME = ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py"


def resolve_cli_state_root(explicit_state_root: str | None, command: str, *, timestamp: str | None = None) -> str:
    return str(resolve_state_root(explicit_state_root, command, timestamp=timestamp or utc_timestamp()))


def validate_schema_files(*, schema: str, fixtures: list[str]) -> dict[str, Any]:
    schema_path = resolve_repo_path(schema)
    results = [
        validate_file(schema_path=schema_path, instance_path=resolve_repo_path(fixture))
        for fixture in fixtures
    ]
    return {
        "ok": all(result.ok for result in results),
        "action": "schema-validation",
        "schema": schema,
        "fixtures": fixtures,
        "results": [result.to_dict() for result in results],
    }


def run_room_fixture(*, question: str, state_root: str | Path, run_id: str | None = None) -> dict[str, Any]:
    run = create_run_dir(state_root, "room", run_id=run_id)
    input_payload = {
        "question": question,
        "mode": "fixture_backed",
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
    }
    write_input(run.run_dir, input_payload)
    room_id = f"room-{uuid.uuid4().hex[:8]}"
    legacy_root = run.run_dir / "legacy-runtime"
    command_result = run_json_command(
        [
            sys.executable,
            ROOM_RUNTIME,
            "validate-canonical",
            "--state-root",
            str(legacy_root),
            "--room-id",
            room_id,
        ]
    )
    if not command_result["ok"]:
        return finalize_failed_run(run, input_payload, "room", command_result)

    report = command_result["payload"]
    state_path = Path(str(report["state_path"]))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    artifacts = dict(report.get("artifacts", {}))
    room_session = project_room_state_to_session(state, artifacts)
    room_session_path = run.run_dir / "room-session.json"
    write_json_file(room_session_path, room_session)
    portable_handoff_path = run.run_dir / "portable-handoff-packet.json"
    if room_session.get("handoff_packet") is not None:
        write_json_file(portable_handoff_path, room_session["handoff_packet"])

    validation = validate_file(
        schema_path=REPO_ROOT / "schemas" / "room-session.schema.json",
        instance_path=room_session_path,
    )
    outputs = {
        "run_dir": str(run.run_dir),
        "run_json": str(run.run_dir / "run.json"),
        "input_json": str(run.run_dir / "input.json"),
        "output_json": str(run.run_dir / "output.json"),
        "evidence_json": str(run.run_dir / "evidence.json"),
        "summary_md": str(run.run_dir / "summary.md"),
        "room_session": str(room_session_path),
        "portable_handoff_packet": str(portable_handoff_path),
        "legacy_runtime_report": str(Path(str(artifacts.get("room_dir", legacy_root))) / "validation-report.json"),
        "legacy_state": str(state_path),
    }
    payload = {
        "ok": validation.ok,
        "action": "room",
        "status": "fixture_backed",
        "question": question,
        "run_id": run.run_id,
        "run_dir": str(run.run_dir),
        "room_id": room_id,
        "outputs": outputs,
        "schema_validation": validation.to_dict(),
        "runtime": command_result,
        "claim_boundary": claim_boundary_text(),
    }
    finalize_successful_run(run, input_payload, payload, outputs)
    return payload


def run_debate_fixture(*, question: str, state_root: str | Path, run_id: str | None = None) -> dict[str, Any]:
    run = create_run_dir(state_root, "debate", run_id=run_id)
    input_payload = {
        "question": question,
        "mode": "fixture_backed",
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
    }
    write_input(run.run_dir, input_payload)
    legacy_root = run.run_dir / "legacy-runtime"
    command_result = run_json_command(
        [
            sys.executable,
            DEBATE_RUNTIME,
            "validate-canonical-execution",
            "--state-root",
            str(legacy_root),
        ]
    )
    if not command_result["ok"]:
        return finalize_failed_run(run, input_payload, "debate", command_result)

    report = command_result["payload"]
    artifacts = dict(report.get("artifacts", {}))
    debate_artifacts = {
        "launch_bundle": artifacts["launch_bundle"],
        "roundtable_record": artifacts["roundtable_record"],
        "review_packet": artifacts["review_packet"],
        "review_result": artifacts["review_result"],
        "legacy_handoff_packet": str(
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "fixtures" / "canonical" / "upgrade.json"
        ),
    }
    debate_session = project_debate_artifacts_to_session(debate_artifacts)
    debate_result = build_debate_result_from_artifacts(debate_artifacts)
    debate_session_path = run.run_dir / "debate-session.json"
    debate_result_path = run.run_dir / "debate-result.json"
    write_json_file(debate_session_path, debate_session)
    write_json_file(debate_result_path, debate_result)

    session_validation = validate_file(
        schema_path=REPO_ROOT / "schemas" / "debate-session.schema.json",
        instance_path=debate_session_path,
    )
    result_validation = validate_file(
        schema_path=REPO_ROOT / "schemas" / "debate-result.schema.json",
        instance_path=debate_result_path,
    )
    outputs = {
        "run_dir": str(run.run_dir),
        "run_json": str(run.run_dir / "run.json"),
        "input_json": str(run.run_dir / "input.json"),
        "output_json": str(run.run_dir / "output.json"),
        "evidence_json": str(run.run_dir / "evidence.json"),
        "summary_md": str(run.run_dir / "summary.md"),
        "debate_session": str(debate_session_path),
        "debate_result": str(debate_result_path),
        "legacy_runtime_report": str(Path(str(artifacts.get("debate_dir", legacy_root))) / "validation-report.json"),
        "launch_bundle": artifacts["launch_bundle"],
        "review_packet": artifacts["review_packet"],
        "review_result": artifacts["review_result"],
    }
    payload = {
        "ok": session_validation.ok and result_validation.ok,
        "action": "debate",
        "status": "fixture_backed",
        "question": question,
        "run_id": run.run_id,
        "run_dir": str(run.run_dir),
        "debate_id": report["debate_id"],
        "outputs": outputs,
        "schema_validation": {
            "debate_session": session_validation.to_dict(),
            "debate_result": result_validation.to_dict(),
        },
        "runtime": command_result,
        "claim_boundary": claim_boundary_text(),
    }
    finalize_successful_run(run, input_payload, payload, outputs)
    return payload


def run_golden_demo(*, demo_name: str, state_root: str | Path) -> dict[str, Any]:
    run = create_run_dir(state_root, "demo", run_id=f"demo-{demo_name}")
    input_payload = {
        "demo": demo_name,
        "mode": "fixture_mock",
        "claim_boundary": "not host-live or provider-live validation evidence",
    }
    write_input(run.run_dir, input_payload)

    room_run = run_room_fixture(
        question="我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进",
        state_root=run.run_dir / "runtime-room",
        run_id="demo-room",
    )
    debate_run = run_debate_fixture(
        question="这个创业方向值不值得做",
        state_root=run.run_dir / "runtime-debate",
        run_id="demo-debate",
    )
    quality_json = run.run_dir / "decision-quality-self-check.json"
    quality_md = run.run_dir / "decision-quality-self-check.md"
    quality_run = run_json_command(
        [
            sys.executable,
            "evals/decision_quality/run_decision_evals.py",
            "--output-json",
            str(quality_json),
            "--output-markdown",
            str(quality_md),
        ]
    )
    if room_run["ok"]:
        shutil.copyfile(room_run["outputs"]["room_session"], run.run_dir / "room-session.json")
        shutil.copyfile(room_run["outputs"]["portable_handoff_packet"], run.run_dir / "handoff-packet.json")
    if debate_run["ok"]:
        shutil.copyfile(debate_run["outputs"]["debate_session"], run.run_dir / "debate-session.json")
        shutil.copyfile(debate_run["outputs"]["debate_result"], run.run_dir / "debate-result.json")

    ok = bool(room_run["ok"] and debate_run["ok"] and quality_run["ok"])
    outputs = {
        "room_session": str(run.run_dir / "room-session.json"),
        "handoff_packet": str(run.run_dir / "handoff-packet.json"),
        "debate_session": str(run.run_dir / "debate-session.json"),
        "debate_result": str(run.run_dir / "debate-result.json"),
        "decision_quality_self_check": str(quality_md),
        "decision_quality_self_check_json": str(quality_json),
    }
    summary = {
        "ok": ok,
        "action": "golden-demo",
        "demo": demo_name,
        "mode": "fixture_mock",
        "run_dir": str(run.run_dir),
        "outputs": outputs,
        "runtime": {
            "room": room_run,
            "debate": debate_run,
            "decision_quality": quality_run,
        },
        "claim_boundary": [
            "This is a fixture/mock demo.",
            "It is not host-live validation and not provider-live validation.",
        ],
    }
    write_output(run.run_dir, summary)
    write_evidence(
        run.run_dir,
        build_run_evidence(
            run=run,
            action="golden-demo",
            input_data=input_payload,
            claim_boundary={
                "local_first": True,
                "host_live": "not_claimed",
                "provider_live": "not_claimed",
                "notes": summary["claim_boundary"],
            },
            artifact_paths=outputs,
        ),
    )
    write_summary(run.run_dir, render_demo_summary(summary))
    return summary


def finalize_successful_run(run: Any, input_payload: dict[str, Any], payload: dict[str, Any], outputs: dict[str, str]) -> None:
    write_output(run.run_dir, payload)
    write_evidence(
        run.run_dir,
        build_run_evidence(
            run=run,
            action=str(payload["action"]),
            input_data=input_payload,
            claim_boundary=claim_boundary_object(payload["claim_boundary"]),
            artifact_paths=outputs,
        ),
    )
    write_summary(run.run_dir, render_runtime_summary(payload))


def finalize_failed_run(run: Any, input_payload: dict[str, Any], action: str, command_result: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "ok": False,
        "action": action,
        "status": "fixture_backed_failed",
        "run_id": run.run_id,
        "run_dir": str(run.run_dir),
        "runtime": command_result,
        "claim_boundary": claim_boundary_text(),
    }
    write_output(run.run_dir, payload)
    write_evidence(
        run.run_dir,
        build_run_evidence(
            run=run,
            action=action,
            input_data=input_payload,
            claim_boundary=claim_boundary_object(payload["claim_boundary"]),
            artifact_paths={"run_dir": str(run.run_dir)},
        ),
    )
    write_summary(run.run_dir, render_runtime_summary(payload))
    return payload


def run_json_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    payload = parse_json_output(completed.stdout)
    parsed_payload = isinstance(payload, dict)
    return {
        "ok": completed.returncode == 0 and parsed_payload and payload.get("ok") is not False,
        "command": command,
        "returncode": completed.returncode,
        "payload": payload,
        "stdout": "" if parsed_payload else completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def parse_json_output(text: str) -> object | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def build_stub_payload(action: str, question: str, state_root: str | None) -> dict[str, Any]:
    if action == "room":
        return {
            "ok": False,
            "action": "room",
            "status": "safe_stub",
            "question": question,
            "state_root": state_root,
            "message": (
                "./rtw room --stub shows the boundary-only response. Run ./rtw room without "
                "--stub for the fixture-backed local runtime path."
            ),
            "claim_boundary": [
                "This is not host-live validation and not provider-live validation.",
                "The checked-in room runtime bridge and canonical fixtures remain available for local validation.",
            ],
            "next_commands": [
                "python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical --state-root <state-root>",
                "python3 .codex/skills/room-skill/runtime/room_e2e_validation.py --executor fixture --state-root <state-root>",
            ],
        }
    return {
        "ok": False,
        "action": "debate",
        "status": "safe_stub",
        "question": question,
        "state_root": state_root,
        "message": (
            "./rtw debate --stub shows the boundary-only response. Run ./rtw debate without "
            "--stub for the fixture-backed local runtime path."
        ),
        "claim_boundary": [
            "This is not provider-live validation and not host-live validation.",
            "The checked-in debate runtime bridge and canonical fixtures remain available for local validation.",
        ],
        "next_commands": [
            "python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py validate-canonical --state-root <state-root>",
            "python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py --executor fixture --state-root <state-root>",
        ],
    }


def write_json_file(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def claim_boundary_text() -> list[str]:
    return [
        "This is fixture-backed local runtime output.",
        "It is not host-live validation and not provider-live validation.",
    ]


def claim_boundary_object(notes: list[str]) -> dict[str, Any]:
    return {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": notes,
    }


def render_runtime_summary(payload: dict[str, Any]) -> str:
    lines = [
        f"# {str(payload['action']).title()} Fixture Runtime Summary",
        "",
        f"- Result: `{'PASS' if payload.get('ok') else 'FAIL'}`",
        "- Mode: `fixture_backed`",
        "- Host-live: `not_claimed`",
        "- Provider-live: `not_claimed`",
        "",
        "## Outputs",
        "",
    ]
    outputs = payload.get("outputs", {})
    if isinstance(outputs, dict):
        for name, path in outputs.items():
            lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def render_demo_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Golden Demo Summary",
        "",
        "- Mode: `fixture_mock`",
        "- Host-live: `not_claimed`",
        "- Provider-live: `not_claimed`",
        "",
        "## Outputs",
        "",
    ]
    outputs = summary["outputs"]
    if isinstance(outputs, dict):
        for name, path in outputs.items():
            lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
