#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import generic_agent_executor as generic_executor
import room_debate_e2e_validation as integration_validation
import room_e2e_validation as room_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEBATE_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"
if str(DEBATE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(DEBATE_RUNTIME_DIR))

import debate_e2e_validation as debate_validation


DEFAULT_AGENT_COMMAND = "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py"
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-generic-agent-adapter-validation"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = run_validation(args)
    except Exception as exc:  # Keep the command usable by third-party agent authors.
        report = {
            "ok": False,
            "action": "generic-agent-adapter-validation",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
        if args.output_json:
            write_json(Path(args.output_json).expanduser().resolve(), report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    output_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    else:
        sys.stdout.write(output_text)
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate any local agent CLI against the round-table generic adapter contract. "
            "The default command uses the checked-in fixture agent, so this script can be run offline."
        )
    )
    parser.add_argument(
        "--agent-command",
        default=DEFAULT_AGENT_COMMAND,
        help=(
            "Local agent command. It receives the full task prompt on stdin and may use "
            "{prompt_file}, {input_file}, {output_file}, and {repo_root} placeholders."
        ),
    )
    parser.add_argument(
        "--agent-label",
        default="generic_cli",
        help="Human-readable label for the candidate local agent in the validation report.",
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted validation evidence. Defaults outside the repository.",
    )
    parser.add_argument("--flow-id", help="Optional stable /room -> /debate integration flow id.")
    parser.add_argument(
        "--scenario",
        default="reject_followup",
        choices=["allow", "reject_followup"],
        help="Debate path to validate after /room produces the handoff packet.",
    )
    parser.add_argument(
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for adapter validation.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=room_validation.DEFAULT_FOLLOW_UP,
        help="Second /room input before upgrade.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=generic_executor.DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for each local agent CLI prompt call.",
    )
    parser.add_argument("--output-json", help="Optional path to write the validation report JSON.")
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    command = args.agent_command.strip()
    started_at = utc_now_iso()
    smoke = generic_executor.check_agent_exec(
        repo_root=REPO_ROOT,
        command=command,
        host_name=args.agent_label,
        timeout_seconds=args.timeout_seconds,
    )
    integration_args = argparse.Namespace(
        executor="generic_cli",
        room_env_file=None,
        debate_env_file=None,
        room_fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
        debate_fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(state_root),
        flow_id=args.flow_id,
        topic=args.topic,
        follow_up_input=args.follow_up_input,
        scenario=args.scenario,
        temperature=0.1,
        local_codex_preset=integration_validation.DEFAULT_LOCAL_CODEX_PRESET,
        local_codex_model=None,
        local_codex_fallback_models=None,
        local_codex_profile=None,
        local_codex_reasoning_effort=None,
        local_codex_sandbox=None,
        local_codex_timeout_seconds=None,
        local_codex_timeout_retries=None,
        local_codex_retry_timeout_multiplier=None,
        local_codex_persist_session=False,
        agent_command=command,
        agent_timeout_seconds=args.timeout_seconds,
    )
    integration = integration_validation.run_validation(integration_args)
    pass_criteria = {
        "agent_smoke_ready": smoke.get("ready") is True,
        "room_flow_passed": integration.get("pass_criteria", {}).get("room_flow_passed") is True,
        "handoff_packet_forwarded": integration.get("pass_criteria", {}).get("handoff_packet_forwarded") is True,
        "debate_flow_passed": integration.get("pass_criteria", {}).get("debate_flow_passed") is True,
        "full_chain_passed": integration.get("pass_criteria", {}).get("full_chain_passed") is True,
    }
    report = {
        "ok": all(pass_criteria.values()),
        "action": "generic-agent-adapter-validation",
        "agent_label": args.agent_label,
        "agent_command": command,
        "state_root": str(state_root),
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "smoke": smoke,
        "integration": integration,
        "pass_criteria": pass_criteria,
        "artifacts": {
            "validation_report": str(state_root / "generic-agent-adapter-validation-report.json"),
            "integration_report": integration.get("artifacts", {}).get("integration_report"),
        },
    }
    write_json(state_root / "generic-agent-adapter-validation-report.json", report)
    return report


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
