from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from roundtable_core.runtime import resolve_state_root as core_resolve_state_root

REPO_ROOT = Path(__file__).resolve().parents[1]

ROOM_SELF_CHECK = ".codex/skills/room-skill/runtime/agent_consumer_self_check.py"
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
        return print_stub("room", " ".join(args.question), args.state_root)
    if args.command == "debate":
        return print_stub("debate", " ".join(args.question), args.state_root)

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
        help="Natural-language /room entrypoint. Currently a claim-safe stub.",
    )
    room.add_argument("question", nargs="+", help="Question to explore with /room.")
    room.add_argument("--state-root", help="Reserved for future /room runtime output.")

    debate = subparsers.add_parser(
        "debate",
        help="Natural-language /debate entrypoint. Currently a claim-safe stub.",
    )
    debate.add_argument("question", nargs="+", help="Question to review with /debate.")
    debate.add_argument("--state-root", help="Reserved for future /debate runtime output.")

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
    print("Boundary: /room and /debate are safe stubs in this CLI until full host runtime wiring is complete.")
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
    from roundtable_core.runtime import create_run_dir, write_input, write_output, write_summary

    state_root = Path(resolve_state_root(args.state_root, "demo"))
    run = create_run_dir(state_root, "demo", run_id=f"demo-{args.demo_name}")
    input_payload = {
        "demo": args.demo_name,
        "mode": "fixture_mock",
        "claim_boundary": "not host-live or provider-live validation evidence",
    }
    write_input(run.run_dir, input_payload)

    room_transcript = REPO_ROOT / "examples" / "transcripts" / "room-startup-idea.md"
    handoff_fixture = REPO_ROOT / "examples" / "fixtures" / "room-to-debate-handoff.valid.json"
    debate_result = REPO_ROOT / "examples" / "fixtures" / "debate-result.valid.json"

    shutil.copyfile(room_transcript, run.run_dir / "room-transcript.md")
    shutil.copyfile(handoff_fixture, run.run_dir / "handoff-packet.json")
    shutil.copyfile(debate_result, run.run_dir / "debate-result.json")
    quality = render_demo_quality_self_check()
    (run.run_dir / "decision-quality-self-check.md").write_text(quality, encoding="utf-8")
    summary = {
        "ok": True,
        "action": "golden-demo",
        "demo": args.demo_name,
        "mode": "fixture_mock",
        "run_dir": str(run.run_dir),
        "outputs": {
            "room_transcript": str(run.run_dir / "room-transcript.md"),
            "handoff_packet": str(run.run_dir / "handoff-packet.json"),
            "debate_result": str(run.run_dir / "debate-result.json"),
            "decision_quality_self_check": str(run.run_dir / "decision-quality-self-check.md"),
        },
        "claim_boundary": [
            "This is a fixture/mock demo.",
            "It is not host-live validation and not provider-live validation.",
        ],
    }
    write_output(run.run_dir, summary)
    write_summary(run.run_dir, render_demo_summary(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=REPO_ROOT)
    return result.returncode


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
                "./rtw room is present as a natural-language CLI entrypoint, but the full /room "
                "host runtime is not wired to this command yet."
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
            "./rtw debate is present as a natural-language CLI entrypoint, but the full /debate "
            "host runtime is not wired to this command yet."
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


def render_demo_quality_self_check() -> str:
    return """# Decision Quality Self Check

- Mode: `fixture_mock`
- Rubric: `docs/decision-quality-rubric.md`
- Result: `PASS`
- Total score: `13/14`
- Blocking dimensions: `[]`

This demo output includes problem reframing, key variables, assumption
separation, substantive opposition, risk-to-action conversion, a next testable
step, and explicit uncertainty disclosure.

Claim boundary: this is not host-live validation and not provider-live
validation evidence.
"""


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
