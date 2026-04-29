from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from roundtable_core.runtime import resolve_state_root as core_resolve_state_root

REPO_ROOT = Path(__file__).resolve().parents[1]

ROOM_SELF_CHECK = ".codex/skills/room-skill/runtime/agent_consumer_self_check.py"
ROOM_RUNTIME = ".codex/skills/room-skill/runtime/room_runtime.py"
DEBATE_RUNTIME = ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py"
LIVE_LANE_EVIDENCE = ".codex/skills/room-skill/runtime/live_lane_evidence_report.py"
LOCAL_CODEX_REGRESSION = ".codex/skills/room-skill/runtime/local_codex_regression.py"
RELEASE_CHECK = "scripts/release_check.py"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "evidence":
        return run_evidence(args)
    if args.command == "release-check":
        return run_release_check(args)
    if args.command == "interactive":
        return run_interactive(args)
    if args.command == "demo":
        return run_demo(args)
    if args.command == "room":
        if args.stub:
            return print_stub("room", " ".join(args.question), args.state_root)
        return run_room(args)
    if args.command == "debate":
        if args.stub:
            return print_stub("debate", " ".join(args.question), args.state_root)
        return run_debate(args)

    parser.error("unsupported command")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtw",
        description="Unified local-first CLI for Round Table Workspace.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor",
        help="Run the clone-friendly consumer self-check.",
    )
    doctor.add_argument("--quick", action="store_true", help="Run the fast self-check path.")
    doctor.add_argument("--state-root", help="Directory for generated doctor evidence.")
    doctor.add_argument("--timeout-seconds", type=int, default=30)

    validate = subparsers.add_parser(
        "validate",
        help="Run local validation. Use --quick for a lightweight preflight.",
    )
    validate.add_argument("--quick", action="store_true", help="Run quick self-check instead of local Codex regression.")
    validate.add_argument("--state-root", help="Directory for generated validation evidence.")
    validate.add_argument("--timeout-seconds", type=int, default=30)
    validate.add_argument("--schema", help="Validate fixture JSON against a checked-in JSON Schema file.")
    validate.add_argument(
        "--fixture",
        action="append",
        help="Fixture JSON file to validate. Can be passed more than once.",
    )

    evidence = subparsers.add_parser(
        "evidence",
        help="Generate a claim-safe host/provider live-lane evidence report.",
    )
    evidence.add_argument("--state-root", help="Directory for generated evidence.")
    evidence.add_argument("--timeout-seconds", type=int, default=30)
    evidence.add_argument(
        "--skip-host",
        action="append",
        default=[],
        metavar="HOST_ID=REASON",
        help="Pass an explicit host skip reason to the live-lane evidence report.",
    )

    room = subparsers.add_parser(
        "room",
        help="Natural-language /room entrypoint backed by checked-in local fixtures.",
    )
    room.add_argument("question", nargs="+", help="Question to explore with /room.")
    room.add_argument("--state-root", help="Directory for generated /room runtime output.")
    room.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")

    debate = subparsers.add_parser(
        "debate",
        help="Natural-language /debate entrypoint backed by checked-in local fixtures.",
    )
    debate.add_argument("question", nargs="+", help="Question to review with /debate.")
    debate.add_argument("--state-root", help="Directory for generated /debate runtime output.")
    debate.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")

    release_check = subparsers.add_parser(
        "release-check",
        help="Aggregate v0.2.0 release checks without replacing legacy release reports.",
    )
    release_check.add_argument("--state-root", help="Directory for release-check reports.")
    release_check.add_argument("--include-fixtures", action="store_true")
    release_check.add_argument("--strict-git-clean", action="store_true")
    release_check.add_argument("--timeout-seconds", type=int, default=30)

    interactive = subparsers.add_parser(
        "interactive",
        help="Run a lightweight interactive /room and /debate command loop.",
    )
    interactive.add_argument("--state-root", help="Reserved for future interactive state output.")

    demo = subparsers.add_parser(
        "demo",
        help="Run fixture/mock golden demos.",
    )
    demo.add_argument("demo_name", choices=["startup-idea"])
    demo.add_argument("--state-root", help="Directory for generated demo output.")

    return parser


def run_doctor(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        ROOM_SELF_CHECK,
        "--state-root",
        resolve_state_root(args.state_root, "doctor"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.quick:
        command.append("--quick")
    return run_command(command)


def run_validate(args: argparse.Namespace) -> int:
    if args.schema or args.fixture:
        return run_schema_validation(args)

    if args.quick:
        command = [
            sys.executable,
            ROOM_SELF_CHECK,
            "--quick",
            "--state-root",
            resolve_state_root(args.state_root, "validate"),
            "--timeout-seconds",
            str(args.timeout_seconds),
        ]
    else:
        command = [
            sys.executable,
            LOCAL_CODEX_REGRESSION,
            "--state-root",
            resolve_state_root(args.state_root, "validate"),
        ]
    return run_command(command)


def run_schema_validation(args: argparse.Namespace) -> int:
    if args.quick:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "--quick cannot be combined with --schema validation.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    if not args.schema or not args.fixture:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "--schema and at least one --fixture are required together.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    from roundtable_core.validation import validate_file

    schema_path = resolve_repo_path(args.schema)
    results = [
        validate_file(schema_path=schema_path, instance_path=resolve_repo_path(fixture))
        for fixture in args.fixture
    ]
    payload = {
        "ok": all(result.ok for result in results),
        "action": "schema-validation",
        "schema": args.schema,
        "fixtures": args.fixture,
        "results": [result.to_dict() for result in results],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


def run_evidence(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        LIVE_LANE_EVIDENCE,
        "--state-root",
        resolve_state_root(args.state_root, "evidence"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    for skip_host in args.skip_host:
        command.extend(["--skip-host", skip_host])
    return run_command(command)


def run_room(args: argparse.Namespace) -> int:
    payload = build_room_fixture_run(
        question=" ".join(args.question),
        state_root=Path(resolve_state_root(args.state_root, "room")),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


def run_debate(args: argparse.Namespace) -> int:
    payload = build_debate_fixture_run(
        question=" ".join(args.question),
        state_root=Path(resolve_state_root(args.state_root, "debate")),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


def run_release_check(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        RELEASE_CHECK,
        "--state-root",
        resolve_state_root(args.state_root, "release-check"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.include_fixtures:
        command.append("--include-fixtures")
    if args.strict_git_clean:
        command.append("--strict-git-clean")
    return run_command(command)


def run_interactive(args: argparse.Namespace) -> int:
    print("Round Table Workspace interactive mode")
    print("Commands: /help, /room <question>, /debate <question>, /exit")
    print("Boundary: interactive mode returns boundary-only stubs; use top-level ./rtw room/debate for fixture-backed runtime.")
    while True:
        try:
            line = input("rtw> ").strip()
        except EOFError:
            print()
            return 0
        if not line:
            continue
        if line in {"/exit", "exit", "quit"}:
            print("bye")
            return 0
        if line == "/help":
            print("Use /room <question> to explore, /debate <question> to review, /exit to leave.")
            continue
        if line.startswith("/room "):
            print(json.dumps(build_stub_payload("room", line[len("/room ") :], args.state_root), ensure_ascii=False, indent=2))
            continue
        if line.startswith("/debate "):
            print(json.dumps(build_stub_payload("debate", line[len("/debate ") :], args.state_root), ensure_ascii=False, indent=2))
            continue
        print("Unknown input. Use /help, /room <question>, /debate <question>, or /exit.")


def run_demo(args: argparse.Namespace) -> int:
    from roundtable_core.runtime import create_run_dir, write_evidence, write_input, write_output, write_summary
    from roundtable_core.runtime.state_store import build_run_evidence

    state_root = Path(resolve_state_root(args.state_root, "demo"))
    run = create_run_dir(state_root, "demo", run_id=f"demo-{args.demo_name}")
    input_payload = {
        "demo": args.demo_name,
        "mode": "fixture_mock",
        "claim_boundary": "not host-live or provider-live validation evidence",
    }
    write_input(run.run_dir, input_payload)

    room_run = build_room_fixture_run(
        question="我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进",
        state_root=run.run_dir / "runtime-room",
        run_id="demo-room",
    )
    debate_run = build_debate_fixture_run(
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
        "demo": args.demo_name,
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
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=REPO_ROOT)
    return result.returncode


def build_room_fixture_run(*, question: str, state_root: Path, run_id: str | None = None) -> dict[str, object]:
    from roundtable_core.protocol.projections import project_room_state_to_session
    from roundtable_core.runtime import create_run_dir, write_evidence, write_input, write_output, write_summary
    from roundtable_core.runtime.state_store import build_run_evidence
    from roundtable_core.validation import validate_file

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
    write_output(run.run_dir, payload)
    write_evidence(
        run.run_dir,
        build_run_evidence(
            run=run,
            action="room",
            input_data=input_payload,
            claim_boundary=claim_boundary_object(payload["claim_boundary"]),
            artifact_paths=outputs,
        ),
    )
    write_summary(run.run_dir, render_runtime_summary(payload))
    return payload


def build_debate_fixture_run(*, question: str, state_root: Path, run_id: str | None = None) -> dict[str, object]:
    from roundtable_core.protocol.projections import project_debate_artifacts_to_result, project_debate_artifacts_to_session
    from roundtable_core.runtime import create_run_dir, write_evidence, write_input, write_output, write_summary
    from roundtable_core.runtime.state_store import build_run_evidence
    from roundtable_core.validation import validate_file

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
        "legacy_handoff_packet": str(REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "fixtures" / "canonical" / "upgrade.json"),
    }
    debate_session = project_debate_artifacts_to_session(debate_artifacts)
    debate_result = project_debate_artifacts_to_result(debate_artifacts)
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
    write_output(run.run_dir, payload)
    write_evidence(
        run.run_dir,
        build_run_evidence(
            run=run,
            action="debate",
            input_data=input_payload,
            claim_boundary=claim_boundary_object(payload["claim_boundary"]),
            artifact_paths=outputs,
        ),
    )
    write_summary(run.run_dir, render_runtime_summary(payload))
    return payload


def finalize_failed_run(run: object, input_payload: dict[str, object], action: str, command_result: dict[str, object]) -> dict[str, object]:
    from roundtable_core.runtime import write_output, write_summary

    run_dir = getattr(run, "run_dir")
    payload = {
        "ok": False,
        "action": action,
        "status": "fixture_backed_failed",
        "run_id": getattr(run, "run_id"),
        "run_dir": str(run_dir),
        "runtime": command_result,
        "claim_boundary": claim_boundary_text(),
    }
    write_output(run_dir, payload)
    write_summary(run_dir, render_runtime_summary(payload))
    return payload


def run_json_command(command: list[str]) -> dict[str, object]:
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


def write_json_file(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def claim_boundary_text() -> list[str]:
    return [
        "This is fixture-backed local runtime output.",
        "It is not host-live validation and not provider-live validation.",
    ]


def claim_boundary_object(notes: list[str]) -> dict[str, object]:
    return {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": notes,
    }


def render_runtime_summary(payload: dict[str, object]) -> str:
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


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def resolve_state_root(explicit_state_root: str | None, command: str) -> str:
    return str(core_resolve_state_root(explicit_state_root, command, timestamp=utc_timestamp()))


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def print_stub(action: str, question: str, state_root: str | None) -> int:
    payload = build_stub_payload(action=action, question=question, state_root=state_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_stub_payload(action: str, question: str, state_root: str | None) -> dict[str, object]:
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
                "python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical --state-root /tmp/round-table-room-canonical",
                "python3 .codex/skills/room-skill/runtime/room_e2e_validation.py --executor fixture --state-root /tmp/round-table-room-e2e",
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
            "python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py validate-canonical --state-root /tmp/round-table-debate-canonical",
            "python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py --executor fixture --state-root /tmp/round-table-debate-e2e",
        ],
    }


def render_demo_summary(summary: dict[str, object]) -> str:
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
