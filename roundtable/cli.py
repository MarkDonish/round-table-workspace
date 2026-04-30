from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from roundtable_core.commands import (
    build_stub_payload as service_build_stub_payload,
    resolve_cli_state_root,
    run_debate_fixture,
    run_golden_demo,
    run_room_fixture,
    validate_schema_files,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

ROOM_SELF_CHECK = ".codex/skills/room-skill/runtime/agent_consumer_self_check.py"
ROOM_RUNTIME = ".codex/skills/room-skill/runtime/room_runtime.py"
DEBATE_RUNTIME = ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py"
LIVE_LANE_EVIDENCE = ".codex/skills/room-skill/runtime/live_lane_evidence_report.py"
LOCAL_CODEX_REGRESSION = ".codex/skills/room-skill/runtime/local_codex_regression.py"
RELEASE_CHECK = "scripts/release_check.py"
AGENT_REGISTRY_RUNTIME = ".codex/skills/agent-builder-skill/runtime/agent_registry.py"
AGENT_BUNDLE_VALIDATOR = ".codex/skills/agent-builder-skill/runtime/validate_agent_bundle.py"
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_USAGE_OR_CONFIG = 2
EXIT_RUNTIME_ERROR = 3


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
    if args.command == "agent":
        return run_agent(args)
    if args.command == "room":
        if args.stub:
            return print_stub("room", " ".join(args.question), args.state_root, args=args)
        return run_room(args)
    if args.command == "debate":
        if args.stub:
            return print_stub("debate", " ".join(args.question), args.state_root, args=args)
        return run_debate(args)

    parser.error("unsupported command")
    return EXIT_USAGE_OR_CONFIG


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
    add_output_args(doctor)

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
    add_output_args(validate)

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
    add_output_args(evidence)

    room = subparsers.add_parser(
        "room",
        help="Natural-language /room entrypoint backed by checked-in local fixtures.",
    )
    room.add_argument("question", nargs="+", help="Question to explore with /room.")
    room.add_argument("--state-root", help="Directory for generated /room runtime output.")
    room.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")
    add_output_args(room)

    debate = subparsers.add_parser(
        "debate",
        help="Natural-language /debate entrypoint backed by checked-in local fixtures.",
    )
    debate.add_argument("question", nargs="+", help="Question to review with /debate.")
    debate.add_argument("--state-root", help="Directory for generated /debate runtime output.")
    debate.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")
    add_output_args(debate)

    release_check = subparsers.add_parser(
        "release-check",
        help="Aggregate v0.2.0 release checks without replacing legacy release reports.",
    )
    release_check.add_argument("--state-root", help="Directory for release-check reports.")
    release_check.add_argument("--include-fixtures", action="store_true")
    release_check.add_argument("--strict-git-clean", action="store_true")
    release_check.add_argument("--timeout-seconds", type=int, default=30)
    add_output_args(release_check)

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
    add_output_args(demo)

    agent = subparsers.add_parser(
        "agent",
        help="Manage Agent Factory manifests and registry entries.",
    )
    agent.add_argument("--registry", help="Registry JSON path. Defaults to config/agent-registry.json.")
    add_output_args(agent)
    agent_subparsers = agent.add_subparsers(dest="agent_command", required=True)

    agent_list = agent_subparsers.add_parser("list", help="List Agent Factory registry entries.")
    agent_list.add_argument("--status", help="Optional status filter.")

    agent_validate = agent_subparsers.add_parser("validate", help="Validate registry or one manifest/bundle.")
    agent_validate.add_argument("target", nargs="?", help="Optional manifest path or registry agent_id.")
    agent_validate.add_argument("--profile", help="Profile path when validating a manifest bundle.")

    agent_register = agent_subparsers.add_parser("register", help="Register an agent manifest.")
    agent_register.add_argument("manifest", help="Path to manifest JSON.")
    agent_register.add_argument("--replace", action="store_true", help="Replace existing agent_id.")
    agent_register.add_argument("--enable", action="store_true", help="Register directly as enabled.")

    agent_enable = agent_subparsers.add_parser("enable", help="Enable a registered agent.")
    agent_enable.add_argument("agent_id")
    agent_enable.add_argument("--allow-missing-skill", action="store_true", help="Allow enable without local skill dir.")

    agent_disable = agent_subparsers.add_parser("disable", help="Disable a registered agent.")
    agent_disable.add_argument("agent_id")

    return parser


def add_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit stable JSON output when the command supports structured output.")
    parser.add_argument("--quiet", action="store_true", help="Suppress human/stdout output; exit code remains authoritative.")
    parser.add_argument("--output-json", help="Write structured command output to this JSON file when available.")
    parser.add_argument("--output-markdown", help="Write a Markdown summary to this file when available.")


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
    return run_command(command, args=args)


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
    return run_command(command, args=args)


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
        return EXIT_USAGE_OR_CONFIG

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
        return EXIT_USAGE_OR_CONFIG

    payload = validate_schema_files(schema=args.schema, fixtures=list(args.fixture))
    emit_payload(args, payload, markdown=render_payload_summary(payload))
    return EXIT_SUCCESS if payload["ok"] else EXIT_VALIDATION_FAILURE


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
    return run_command(command, args=args)


def run_agent(args: argparse.Namespace) -> int:
    registry_args = ["--registry", args.registry] if args.registry else []
    if args.agent_command == "list":
        command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "list"]
        if args.status:
            command.extend(["--status", args.status])
    elif args.agent_command == "validate":
        if args.target and looks_like_manifest_path(args.target):
            command = [sys.executable, AGENT_BUNDLE_VALIDATOR, args.target]
            if args.profile:
                command.extend(["--profile", args.profile])
        elif args.target:
            command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "validate", "--agent-id", args.target]
        else:
            command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "validate"]
    elif args.agent_command == "register":
        command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "register", args.manifest]
        if args.replace:
            command.append("--replace")
        if args.enable:
            command.append("--enable")
    elif args.agent_command == "enable":
        command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "enable", args.agent_id]
        if args.allow_missing_skill:
            command.append("--allow-missing-skill")
    elif args.agent_command == "disable":
        command = [sys.executable, AGENT_REGISTRY_RUNTIME, *registry_args, "disable", args.agent_id]
    else:
        return EXIT_USAGE_OR_CONFIG
    return run_captured_command(command, args=args)


def run_room(args: argparse.Namespace) -> int:
    payload = run_room_fixture(
        question=" ".join(args.question),
        state_root=Path(resolve_state_root(args.state_root, "room")),
    )
    emit_payload(args, payload, markdown=render_payload_summary(payload))
    return exit_code_for_payload(payload)


def run_debate(args: argparse.Namespace) -> int:
    payload = run_debate_fixture(
        question=" ".join(args.question),
        state_root=Path(resolve_state_root(args.state_root, "debate")),
    )
    emit_payload(args, payload, markdown=render_payload_summary(payload))
    return exit_code_for_payload(payload)


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
    return run_command(command, args=args)


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
    summary = run_golden_demo(
        demo_name=args.demo_name,
        state_root=Path(resolve_state_root(args.state_root, "demo")),
    )
    emit_payload(args, summary, markdown=render_demo_summary(summary))
    return exit_code_for_payload(summary)


def run_command(command: list[str], *, args: argparse.Namespace | None = None) -> int:
    if args and has_structured_output_request(args):
        return run_captured_command(command, args=args)
    result = subprocess.run(command, cwd=REPO_ROOT)
    return result.returncode


def run_captured_command(command: list[str], *, args: argparse.Namespace | None = None) -> int:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if args and has_structured_output_request(args):
        payload = parse_json_output(stdout)
        if not isinstance(payload, dict):
            payload = {
                "ok": result.returncode == 0,
                "action": "subprocess-command",
                "command": command,
                "returncode": result.returncode,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
            }
        emit_payload(args, payload, markdown=render_payload_summary(payload))
    else:
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, file=sys.stderr, end="")
    return result.returncode


def has_structured_output_request(args: argparse.Namespace) -> bool:
    return bool(
        getattr(args, "quiet", False)
        or getattr(args, "json", False)
        or getattr(args, "output_json", None)
        or getattr(args, "output_markdown", None)
    )


def emit_payload(args: argparse.Namespace, payload: dict[str, object], *, markdown: str | None = None) -> None:
    if getattr(args, "output_json", None):
        write_json_file(Path(args.output_json).expanduser(), payload)
    if getattr(args, "output_markdown", None):
        path = Path(args.output_markdown).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((markdown or render_payload_summary(payload)).rstrip() + "\n", encoding="utf-8")
    if getattr(args, "quiet", False):
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def render_payload_summary(payload: dict[str, object]) -> str:
    lines = [
        f"# {str(payload.get('action', 'rtw')).replace('-', ' ').title()}",
        "",
        f"- Result: `{'PASS' if payload.get('ok') is not False else 'FAIL'}`",
    ]
    if "run_dir" in payload:
        lines.append(f"- Run dir: `{payload['run_dir']}`")
    if "release_blockers" in payload:
        blockers = payload.get("release_blockers")
        lines.append(f"- Release blockers: `{blockers}`")
    outputs = payload.get("outputs")
    if isinstance(outputs, dict):
        lines.extend(["", "## Outputs", ""])
        for name, path in outputs.items():
            lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def exit_code_for_payload(payload: dict[str, object]) -> int:
    if payload.get("ok"):
        return EXIT_SUCCESS
    status = str(payload.get("status", ""))
    if "failed" in status:
        return EXIT_RUNTIME_ERROR
    return EXIT_VALIDATION_FAILURE


def looks_like_manifest_path(target: str) -> bool:
    return target.endswith(".json") or "/" in target or "\\" in target


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
    return resolve_cli_state_root(explicit_state_root, command, timestamp=utc_timestamp())


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def print_stub(action: str, question: str, state_root: str | None, *, args: argparse.Namespace | None = None) -> int:
    payload = build_stub_payload(action=action, question=question, state_root=state_root)
    if args:
        emit_payload(args, payload, markdown=render_payload_summary(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_stub_payload(action: str, question: str, state_root: str | None) -> dict[str, object]:
    return service_build_stub_payload(action, question, state_root)


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
