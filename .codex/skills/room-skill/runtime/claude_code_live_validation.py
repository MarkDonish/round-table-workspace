#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import generic_agent_executor as generic_executor
import room_debate_e2e_validation as integration_validation
import room_e2e_validation as room_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "claude-code-live-validation"
DEFAULT_CLAUDE_CODE_AGENT_COMMAND = (
    'claude -p --input-format text --output-format text --no-session-persistence --tools ""'
)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = run_validation(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "blocked": True, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a real Claude Code local CLI preflight and, when authenticated, "
            "the checked-in /room -> /debate validation through the claude_code host adapter."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted Claude Code validation evidence.",
    )
    parser.add_argument("--run-id", help="Optional stable validation run id.")
    parser.add_argument(
        "--agent-command",
        default=DEFAULT_CLAUDE_CODE_AGENT_COMMAND,
        help=(
            "Claude Code command for the local agent adapter. The adapter passes the prompt on stdin and expects JSON "
            "on stdout or {output_file}."
        ),
    )
    parser.add_argument(
        "--agent-timeout-seconds",
        type=int,
        default=300,
        help="Timeout for each Claude Code prompt call.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Only write CLI/auth preflight evidence and skip smoke/integration execution.",
    )
    parser.add_argument(
        "--skip-auth-check",
        action="store_true",
        help="Attempt smoke/integration even if `claude auth status` reports loggedIn=false.",
    )
    parser.add_argument(
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="The initial /room topic to validate.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=room_validation.DEFAULT_FOLLOW_UP,
        help="The second-step follow-up input for /room.",
    )
    parser.add_argument(
        "--scenario",
        default="reject_followup",
        choices=["allow", "reject_followup"],
        help="Which checked-in /debate path to validate after /room produces the packet.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"claude-code-live-{uuid.uuid4().hex[:8]}"
    run_dir = state_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    agent_command = generic_executor.resolve_agent_command(executor_name="claude_code", command=args.agent_command)
    preflight = build_preflight(agent_command=agent_command)
    report: dict[str, Any] = {
        "ok": False,
        "blocked": False,
        "action": "claude-code-live-validation",
        "run_id": run_id,
        "state_root": str(state_root),
        "run_dir": str(run_dir),
        "agent_command": agent_command,
        "agent_timeout_seconds": args.agent_timeout_seconds,
        "preflight": preflight,
    }

    if args.preflight_only:
        report.update(
            {
                "ok": preflight["cli_available"] and preflight["auth"].get("loggedIn") is True,
                "blocked": preflight["auth"].get("loggedIn") is not True,
                "blocker": None if preflight["auth"].get("loggedIn") is True else "claude_code_not_logged_in",
                "next_action": None if preflight["auth"].get("loggedIn") is True else "Run `claude auth login`, then rerun this wrapper.",
            }
        )
        write_json(run_dir / "claude-code-live-validation-report.json", report)
        return report

    if not preflight["cli_available"]:
        report.update(
            {
                "blocked": True,
                "blocker": "claude_code_cli_missing",
                "next_action": "Install Claude Code CLI and make `claude` available on PATH.",
            }
        )
        write_json(run_dir / "claude-code-live-validation-report.json", report)
        return report

    if not args.skip_auth_check and preflight["auth"].get("loggedIn") is not True:
        report.update(
            {
                "blocked": True,
                "blocker": "claude_code_not_logged_in",
                "next_action": "Run `claude auth login`, then rerun this wrapper.",
            }
        )
        write_json(run_dir / "claude-code-live-validation-report.json", report)
        return report

    try:
        smoke = generic_executor.check_agent_exec(
            repo_root=REPO_ROOT,
            command=agent_command,
            host_name="claude_code",
            timeout_seconds=args.agent_timeout_seconds,
        )
    except generic_executor.GenericAgentExecutorError as exc:
        report.update(
            {
                "blocked": True,
                "blocker": "claude_code_smoke_failed",
                "error": str(exc),
                "error_details": exc.details,
            }
        )
        write_json(run_dir / "claude-code-live-validation-report.json", report)
        return report

    integration_args = argparse.Namespace(
        executor="claude_code",
        room_env_file=None,
        debate_env_file=None,
        room_fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
        debate_fixtures_dir=str(integration_validation.debate_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(run_dir / "integration"),
        flow_id=f"{run_id}-integration",
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
        agent_command=agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
    )
    try:
        integration_report = integration_validation.run_validation(integration_args)
    except Exception as exc:
        report.update(
            {
                "blocked": False,
                "blocker": "claude_code_integration_failed",
                "error": str(exc),
                "smoke": smoke,
            }
        )
        write_json(run_dir / "claude-code-live-validation-report.json", report)
        return report

    report.update(
        {
            "ok": bool(integration_report.get("pass_criteria", {}).get("full_chain_passed")),
            "blocked": False,
            "smoke": smoke,
            "integration": {
                "flow_id": integration_report.get("flow_id"),
                "room_id": integration_report.get("room_id"),
                "debate_id": integration_report.get("debate_id"),
                "pass_criteria": integration_report.get("pass_criteria"),
                "artifacts": integration_report.get("artifacts"),
            },
        }
    )
    write_json(run_dir / "claude-code-live-validation-report.json", report)
    return report


def build_preflight(*, agent_command: str) -> dict[str, Any]:
    claude_path = shutil.which("claude")
    preflight: dict[str, Any] = {
        "cli_available": bool(claude_path),
        "claude_path": claude_path,
        "agent_command": agent_command,
    }
    if not claude_path:
        preflight["version"] = None
        preflight["auth"] = {"loggedIn": False, "authMethod": "none", "apiProvider": None}
        return preflight

    version_result = run_command(["claude", "--version"], timeout_seconds=20)
    preflight["version"] = {
        "ok": version_result["returncode"] == 0,
        "stdout": version_result["stdout"].strip(),
        "stderr": version_result["stderr"].strip(),
        "returncode": version_result["returncode"],
    }

    auth_result = run_command(["claude", "auth", "status"], timeout_seconds=20)
    auth_payload: dict[str, Any]
    try:
        parsed = json.loads(auth_result["stdout"])
        auth_payload = parsed if isinstance(parsed, dict) else {"raw": parsed}
    except json.JSONDecodeError:
        auth_payload = {
            "loggedIn": False,
            "authMethod": "unknown",
            "apiProvider": None,
            "raw_stdout": auth_result["stdout"].strip(),
            "raw_stderr": auth_result["stderr"].strip(),
        }
    auth_payload["returncode"] = auth_result["returncode"]
    preflight["auth"] = auth_payload
    return preflight


def run_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        cwd=str(REPO_ROOT),
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
