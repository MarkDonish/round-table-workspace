from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from roundtable_core.commands import (
    build_stub_payload as service_build_stub_payload,
    resolve_cli_state_root,
    run_agent_disable,
    run_agent_enable,
    run_agent_list,
    run_agent_register,
    run_agent_validate,
    run_debate_fixture,
    run_golden_demo,
    run_room_fixture,
    validate_schema_files,
)
from roundtable_core.runtime.paths import UnsafePathError, assert_no_symlink_components

REPO_ROOT = Path(__file__).resolve().parents[1]

ROOM_SELF_CHECK = ".codex/skills/room-skill/runtime/agent_consumer_self_check.py"
LIVE_LANE_EVIDENCE = ".codex/skills/room-skill/runtime/live_lane_evidence_report.py"
LOCAL_CODEX_REGRESSION = ".codex/skills/room-skill/runtime/local_codex_regression.py"
RELEASE_CHECK = "scripts/release_check.py"
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_USAGE_OR_CONFIG = 2
EXIT_RUNTIME_ERROR = 3


class UnsafeOutputPathError(ValueError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return dispatch(args, parser)
    except UnsafeOutputPathError as exc:
        return handle_output_path_error(args, str(exc))
    except UnsafePathError as exc:
        return handle_output_path_error(args, str(exc))


def dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
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
    if args.command == "ship-check":
        return run_ship_check(args)
    if args.command == "launch-kit":
        return run_launch_kit(args)
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
    add_output_args(parser, suppress_defaults=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor",
        help="Run the clone-friendly consumer self-check.",
    )
    doctor.add_argument("--quick", action="store_true", help="Run the fast self-check path.")
    doctor.add_argument("--state-root", help="Directory for generated doctor evidence.")
    doctor.add_argument("--timeout-seconds", type=int, default=30)
    add_output_args(doctor, suppress_defaults=True)

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
    add_output_args(validate, suppress_defaults=True)

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
    add_output_args(evidence, suppress_defaults=True)

    room = subparsers.add_parser(
        "room",
        help="Natural-language /room entrypoint backed by checked-in local fixtures.",
    )
    room.add_argument("question", nargs="+", help="Question to explore with /room.")
    room.add_argument("--state-root", help="Directory for generated /room runtime output.")
    room.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")
    add_output_args(room, suppress_defaults=True)

    debate = subparsers.add_parser(
        "debate",
        help="Natural-language /debate entrypoint backed by checked-in local fixtures.",
    )
    debate.add_argument("question", nargs="+", help="Question to review with /debate.")
    debate.add_argument("--state-root", help="Directory for generated /debate runtime output.")
    debate.add_argument("--stub", action="store_true", help="Show the old claim-safe stub instead of running fixtures.")
    add_output_args(debate, suppress_defaults=True)

    ship_check = subparsers.add_parser(
        "ship-check",
        help="Run a local ship/revise/reject decision gate for AI-generated work.",
    )
    ship_check.add_argument("question", nargs="+", help="Change, feature, or launch decision to review before shipping.")
    add_output_args(ship_check, suppress_defaults=True)

    launch_kit = subparsers.add_parser(
        "launch-kit",
        help="Print the public launch assets, links, and GitHub topic checklist.",
    )
    add_output_args(launch_kit, suppress_defaults=True)

    release_check = subparsers.add_parser(
        "release-check",
        help="Aggregate v0.2.0 release checks without replacing legacy release reports.",
    )
    release_check.add_argument("--state-root", help="Directory for release-check reports.")
    release_check.add_argument("--include-fixtures", action="store_true")
    release_check.add_argument("--strict-git-clean", action="store_true")
    release_check.add_argument("--timeout-seconds", type=int, default=30)
    add_output_args(release_check, suppress_defaults=True)

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
    add_output_args(demo, suppress_defaults=True)

    agent = subparsers.add_parser(
        "agent",
        help="Manage Agent Factory manifests and registry entries.",
    )
    agent.add_argument("--registry", help="Registry JSON path. Defaults to config/agent-registry.json.")
    add_output_args(agent, suppress_defaults=True)
    agent_subparsers = agent.add_subparsers(dest="agent_command", required=True)

    agent_list = agent_subparsers.add_parser("list", help="List Agent Factory registry entries.")
    add_agent_registry_arg(agent_list)
    agent_list.add_argument("--status", help="Optional status filter.")
    add_output_args(agent_list, suppress_defaults=True)

    agent_validate = agent_subparsers.add_parser("validate", help="Validate registry or one manifest/bundle.")
    add_agent_registry_arg(agent_validate)
    agent_validate.add_argument("target", nargs="?", help="Optional manifest path or registry agent_id.")
    agent_validate.add_argument("--profile", help="Profile path when validating a manifest bundle.")
    add_output_args(agent_validate, suppress_defaults=True)

    agent_register = agent_subparsers.add_parser("register", help="Register an agent manifest.")
    add_agent_registry_arg(agent_register)
    agent_register.add_argument("manifest", help="Path to manifest JSON.")
    agent_register.add_argument("--replace", action="store_true", help="Replace existing agent_id.")
    agent_register.add_argument("--enable", action="store_true", help="Register directly as enabled.")
    add_output_args(agent_register, suppress_defaults=True)

    agent_enable = agent_subparsers.add_parser("enable", help="Enable a registered agent.")
    add_agent_registry_arg(agent_enable)
    agent_enable.add_argument("agent_id")
    agent_enable.add_argument("--allow-missing-skill", action="store_true", help="Allow enable without local skill dir.")
    add_output_args(agent_enable, suppress_defaults=True)

    agent_disable = agent_subparsers.add_parser("disable", help="Disable a registered agent.")
    add_agent_registry_arg(agent_disable)
    agent_disable.add_argument("agent_id")
    add_output_args(agent_disable, suppress_defaults=True)

    return parser


def add_output_args(parser: argparse.ArgumentParser, *, suppress_defaults: bool = False) -> None:
    bool_kwargs = {"default": argparse.SUPPRESS} if suppress_defaults else {}
    value_kwargs = {"default": argparse.SUPPRESS} if suppress_defaults else {}
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit stable JSON output when the command supports structured output.",
        **bool_kwargs,
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human/stdout output; exit code remains authoritative.",
        **bool_kwargs,
    )
    parser.add_argument(
        "--output-json",
        help="Write structured command output to this JSON file when available.",
        **value_kwargs,
    )
    parser.add_argument(
        "--output-markdown",
        help="Write a Markdown summary to this file when available.",
        **value_kwargs,
    )


def add_agent_registry_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--registry",
        default=argparse.SUPPRESS,
        help="Registry JSON path. Defaults to config/agent-registry.json.",
    )


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
        emit_payload(args, schema_usage_error("--quick cannot be combined with --schema validation."))
        return EXIT_USAGE_OR_CONFIG

    if not args.schema or not args.fixture:
        emit_payload(args, schema_usage_error("--schema and at least one --fixture are required together."))
        return EXIT_USAGE_OR_CONFIG

    payload = validate_schema_files(schema=args.schema, fixtures=list(args.fixture))
    emit_payload(args, payload, markdown=render_payload_summary(payload))
    return EXIT_SUCCESS if payload["ok"] else EXIT_VALIDATION_FAILURE


def schema_usage_error(message: str) -> dict[str, object]:
    return {
        "ok": False,
        "action": "schema-validation",
        "error": message,
        "results": [],
    }


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
    if args.agent_command == "list":
        payload = run_agent_list(registry=args.registry, status=args.status)
    elif args.agent_command == "validate":
        payload = run_agent_validate(registry=args.registry, target=args.target, profile=args.profile)
    elif args.agent_command == "register":
        payload = run_agent_register(
            registry=args.registry,
            manifest=args.manifest,
            replace=args.replace,
            enable=args.enable,
        )
    elif args.agent_command == "enable":
        payload = run_agent_enable(
            registry=args.registry,
            agent_id=args.agent_id,
            allow_missing_skill=args.allow_missing_skill,
        )
    elif args.agent_command == "disable":
        payload = run_agent_disable(registry=args.registry, agent_id=args.agent_id)
    else:
        return EXIT_USAGE_OR_CONFIG
    emit_payload(args, payload, markdown=render_payload_summary(payload))
    return exit_code_for_payload(payload)


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


def run_ship_check(args: argparse.Namespace) -> int:
    question = " ".join(args.question)
    payload = build_ship_check_payload(question)
    emit_payload(args, payload, markdown=render_ship_check_summary(payload))
    return exit_code_for_payload(payload)


def run_launch_kit(args: argparse.Namespace) -> int:
    payload = build_launch_kit_payload()
    emit_payload(args, payload, markdown=render_launch_kit_summary(payload))
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
        write_text_file(path, (markdown or render_payload_summary(payload)).rstrip() + "\n")
    if getattr(args, "quiet", False):
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_output_path_error(args: argparse.Namespace, message: str) -> int:
    payload = {
        "ok": False,
        "action": str(getattr(args, "command", "rtw")),
        "error": message,
    }
    if getattr(args, "quiet", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return EXIT_USAGE_OR_CONFIG


def render_payload_summary(payload: dict[str, object]) -> str:
    lines = [
        f"# {str(payload.get('action', 'rtw')).replace('-', ' ').title()}",
        "",
        f"- Result: `{'PASS' if payload.get('ok') is not False else 'FAIL'}`",
    ]
    if "state_root" in payload:
        lines.append(f"- State root: `{payload['state_root']}`")
    if "run_dir" in payload:
        lines.append(f"- Run dir: `{payload['run_dir']}`")
    if "release_blockers" in payload:
        blockers = payload.get("release_blockers")
        lines.append(f"- Release blockers: `{blockers}`")
    if "blocked_items" in payload:
        lines.append(f"- Blocked items: `{payload.get('blocked_items')}`")
    append_payload_issues(lines, payload)
    outputs = payload.get("outputs")
    if isinstance(outputs, dict):
        lines.extend(["", "## Outputs", ""])
        for name, path in outputs.items():
            lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def append_payload_issues(lines: list[str], payload: dict[str, object]) -> None:
    issues = collect_payload_issues(payload)
    if not issues:
        return
    lines.extend(["", "## Issues", ""])
    for issue in issues[:12]:
        lines.append(f"- {issue}")


def collect_payload_issues(payload: dict[str, object]) -> list[str]:
    issues: list[str] = []
    add_issue(issues, payload.get("error"))
    add_list_issues(issues, payload.get("errors"))
    add_list_issues(issues, payload.get("blocked_items"), prefix="blocked: ")
    add_list_issues(issues, payload.get("release_blockers"), prefix="release blocker: ")
    add_list_issues(issues, payload.get("warnings"), prefix="warning: ")
    add_check_issues(issues, payload.get("results"))
    add_check_issues(issues, payload.get("checks"))
    add_check_issues(issues, payload.get("schema_validation"))
    add_issue(issues, payload.get("stderr"), prefix="stderr: ")
    return dedupe_preserving_order(issues)


def add_check_issues(issues: list[str], value: object, *, prefix: str = "") -> None:
    if isinstance(value, dict):
        if value.get("ok") is False:
            add_list_issues(issues, value.get("errors"), prefix=prefix)
            add_issue(issues, value.get("error"), prefix=prefix)
            add_issue(issues, value.get("stderr"), prefix=f"{prefix}stderr: ")
        for name, child in value.items():
            if isinstance(child, (dict, list)):
                add_check_issues(issues, child, prefix=f"{prefix}{name}: ")
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                add_check_issues(issues, item, prefix=prefix)
            else:
                add_issue(issues, item, prefix=prefix)


def add_list_issues(issues: list[str], value: object, *, prefix: str = "") -> None:
    if not isinstance(value, list):
        return
    for item in value:
        add_issue(issues, item, prefix=prefix)


def add_issue(issues: list[str], value: object, *, prefix: str = "") -> None:
    if value in (None, "", []):
        return
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    issues.append(f"{prefix}{text}")


def dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def build_ship_check_payload(question: str) -> dict[str, object]:
    panel_votes = [
        {
            "agent": "product",
            "vote": "revise",
            "reason": "The user value should be stated as an observable outcome before shipping.",
        },
        {
            "agent": "engineering",
            "vote": "ship",
            "reason": "The change is small enough to ship when tests and local validation pass.",
        },
        {
            "agent": "risk",
            "vote": "revise",
            "reason": "Claim boundaries and rollback notes should be explicit before launch copy is promoted.",
        },
        {
            "agent": "user-advocate",
            "vote": "revise",
            "reason": "The public README should show a concrete before/after example, not only architecture language.",
        },
    ]
    return {
        "ok": True,
        "action": "ship-check",
        "status": "fixture_backed",
        "question": question,
        "decision": "revise",
        "confidence": "medium",
        "summary": "Useful enough to continue, but revise positioning, evidence, and user-facing examples before claiming it is launch-ready.",
        "panel_votes": panel_votes,
        "risks": [
            "Overclaiming host-live or provider-live behavior without fresh validation evidence.",
            "README positioning may stay too abstract for first-time visitors.",
            "A single-agent answer can miss product, risk, and user-readiness tradeoffs.",
        ],
        "missing_evidence": [
            "Fresh test run for the current checkout.",
            "A visible demo transcript or screenshot for the public launch surface.",
            "A short rollback or revision path if launch feedback is weak.",
        ],
        "next_actions": [
            "Run ./rtw doctor --quick and the unit test suite.",
            "Add one concrete demo transcript or screenshot to the README.",
            "Keep public claims local-first unless host-live/provider-live evidence exists.",
        ],
        "claim_boundary": [
            "ship-check is a fixture-backed local ship/revise/reject decision gate, not a host-live or provider-live agent execution claim.",
            "Use it as a pre-ship review scaffold; verify with project-specific tests before merging or releasing.",
        ],
    }


def render_ship_check_summary(payload: dict[str, object]) -> str:
    lines = [
        "# Ship Check",
        "",
        f"- Decision: `{payload.get('decision')}`",
        f"- Confidence: `{payload.get('confidence')}`",
        f"- Summary: {payload.get('summary')}",
        "",
        "## Panel Votes",
        "",
    ]
    panel_votes = payload.get("panel_votes")
    if isinstance(panel_votes, list):
        for vote in panel_votes:
            if isinstance(vote, dict):
                lines.append(f"- `{vote.get('agent')}`: `{vote.get('vote')}` — {vote.get('reason')}")
    lines.extend(["", "## Next Actions", ""])
    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list):
        for action in next_actions:
            lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def build_launch_kit_payload() -> dict[str, object]:
    topics = [
        "ai-agents",
        "multi-agent",
        "codex",
        "claude-code",
        "developer-tools",
        "local-first",
        "decision-making",
        "ai-coding",
        "ai-code-review",
        "cli",
        "python",
        "agent-workflow",
        "agentic-workflow",
        "code-review",
        "ship-check",
        "round-table",
        "vibe-coding",
        "openai",
        "llm",
    ]
    assets = [
        "README.md",
        "docs/index.html",
        "docs/robots.txt",
        "docs/sitemap.xml",
        "docs/llms.txt",
        "docs/one-minute-demo.html",
        "docs/one-minute-demo.md",
        "docs/use-cases.html",
        "docs/use-cases.md",
        "docs/repo-card.html",
        "docs/repo-card.png",
        "docs/launch-copy.md",
        "docs/community-share-kit.md",
        "docs/directory-submission-kit.md",
        "docs/distribution-checklist.md",
        "docs/public-submission-targets.md",
        "docs/developer-forum-feedback-kit.md",
        "docs/show-hn-submission-draft.md",
        "docs/newsletter-roundup-pitch-kit.md",
        "docs/product-hunt-launch-kit.md",
        "docs/promotion-feedback-template.md",
        "docs/comparison-guide.md",
        "docs/ai-failure-modes.md",
        "docs/demo-recording-guide.md",
        "docs/short-video-script-kit.md",
        "docs/application-packet.md",
        "docs/credits-application-answers.md",
        "docs/reviewer-checklist.md",
        "docs/competitive-insights.md",
        "docs/demo.html",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/claim_boundary.yml",
        ".github/ISSUE_TEMPLATE/workflow_example.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "CONTRIBUTING.md",
        "LICENSE",
    ]
    asset_status = [
        {
            "path": asset,
            "exists": (REPO_ROOT / asset).exists(),
        }
        for asset in assets
    ]
    missing_assets = [item["path"] for item in asset_status if not item["exists"]]
    return {
        "ok": not missing_assets,
        "action": "launch-kit",
        "positioning": "Make your AI agents argue before they ship.",
        "repository": "https://github.com/MarkDonish/round-table-workspace",
        "pages_url": "https://markdonish.github.io/round-table-workspace/",
        "repo_card": "https://markdonish.github.io/round-table-workspace/repo-card.html",
        "repo_card_image": "https://markdonish.github.io/round-table-workspace/repo-card.png",
        "application_packet": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/application-packet.md",
        "credits_application_answers": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/credits-application-answers.md",
        "reviewer_checklist": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/reviewer-checklist.md",
        "competitive_insights": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/competitive-insights.md",
        "community_share_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/community-share-kit.md",
        "directory_submission_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/directory-submission-kit.md",
        "distribution_checklist": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/distribution-checklist.md",
        "public_submission_targets": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/public-submission-targets.md",
        "developer_forum_feedback_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/developer-forum-feedback-kit.md",
        "show_hn_submission_draft": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/show-hn-submission-draft.md",
        "newsletter_roundup_pitch_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/newsletter-roundup-pitch-kit.md",
        "product_hunt_launch_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/product-hunt-launch-kit.md",
        "promotion_feedback_template": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/promotion-feedback-template.md",
        "comparison_guide": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/comparison-guide.md",
        "ai_failure_modes": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/ai-failure-modes.md",
        "demo_recording_guide": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/demo-recording-guide.md",
        "short_video_script_kit": "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/short-video-script-kit.md",
        "workflow_example_issue": "https://github.com/MarkDonish/round-table-workspace/issues/new?template=workflow_example.yml",
        "assets": assets,
        "asset_status": asset_status,
        "missing_assets": missing_assets,
        "topics": topics,
        "commands": [
            "./rtw ship-check \"Should we merge this AI-generated feature?\"",
            "./rtw room \"What is the smallest useful MVP for this idea?\"",
            "./rtw debate \"Is this launch ready?\"",
            "./rtw doctor --quick",
        ],
        "claim_boundary": [
            "The launch kit is a public packaging checklist for the local-first fixture-backed project surface.",
            "It does not claim new host-live or provider-live support.",
        ],
    }


def render_launch_kit_summary(payload: dict[str, object]) -> str:
    lines = [
        "# Launch Kit",
        "",
        f"- Positioning: {payload.get('positioning')}",
        f"- Repository: {payload.get('repository')}",
        f"- Pages demo: {payload.get('pages_url')}",
        f"- Repo card: {payload.get('repo_card')}",
        f"- Repo card image: {payload.get('repo_card_image')}",
        f"- Application packet: {payload.get('application_packet')}",
        f"- Credits application answers: {payload.get('credits_application_answers')}",
        f"- Reviewer checklist: {payload.get('reviewer_checklist')}",
        f"- Competitive insights: {payload.get('competitive_insights')}",
        f"- Community share kit: {payload.get('community_share_kit')}",
        f"- Directory submission kit: {payload.get('directory_submission_kit')}",
        f"- Distribution checklist: {payload.get('distribution_checklist')}",
        f"- Public submission targets: {payload.get('public_submission_targets')}",
        f"- Developer forum feedback kit: {payload.get('developer_forum_feedback_kit')}",
        f"- Show HN submission draft: {payload.get('show_hn_submission_draft')}",
        f"- Newsletter roundup pitch kit: {payload.get('newsletter_roundup_pitch_kit')}",
        f"- Product Hunt launch kit: {payload.get('product_hunt_launch_kit')}",
        f"- Promotion feedback template: {payload.get('promotion_feedback_template')}",
        f"- Comparison guide: {payload.get('comparison_guide')}",
        f"- AI failure modes: {payload.get('ai_failure_modes')}",
        f"- Demo recording guide: {payload.get('demo_recording_guide')}",
        f"- Short video script kit: {payload.get('short_video_script_kit')}",
        f"- Workflow example issue form: {payload.get('workflow_example_issue')}",
        "",
        "## Assets",
        "",
    ]
    assets = payload.get("assets")
    if isinstance(assets, list):
        for asset in assets:
            lines.append(f"- `{asset}`")
    lines.extend(["", "## Topics", ""])
    topics = payload.get("topics")
    if isinstance(topics, list):
        lines.append(", ".join(str(topic) for topic in topics))
    return "\n".join(lines).rstrip() + "\n"


def exit_code_for_payload(payload: dict[str, object]) -> int:
    if payload.get("ok"):
        return EXIT_SUCCESS
    status = str(payload.get("status", ""))
    if "failed" in status:
        return EXIT_RUNTIME_ERROR
    return EXIT_VALIDATION_FAILURE


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
    return write_text_file(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_text_file(path: Path, text: str) -> Path:
    ensure_safe_output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def ensure_safe_output_path(path: Path) -> None:
    if path.exists() and path.is_symlink():
        raise UnsafeOutputPathError(f"refusing to write output through symlink: {path}")
    try:
        assert_no_symlink_components(path, include_leaf=False)
    except ValueError as exc:
        raise UnsafeOutputPathError(str(exc)) from exc


def resolve_state_root(explicit_state_root: str | None, command: str) -> str:
    return resolve_cli_state_root(explicit_state_root, command, timestamp=utc_timestamp())


def utc_timestamp() -> str:
    import uuid

    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def print_stub(action: str, question: str, state_root: str | None, *, args: argparse.Namespace | None = None) -> int:
    payload = build_stub_payload(action=action, question=question, state_root=state_root)
    if args:
        emit_payload(args, payload, markdown=render_payload_summary(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code_for_payload(payload)


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
