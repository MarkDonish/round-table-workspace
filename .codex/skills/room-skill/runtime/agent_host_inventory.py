#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]


CANDIDATES: list[dict[str, Any]] = [
    {
        "id": "claude_code",
        "display_name": "Claude Code",
        "executable": "claude",
        "version_args": ["--version"],
        "auth_args": ["auth", "status"],
        "adapter_command": 'claude -p --input-format text --output-format text --no-session-persistence --tools ""',
    },
    {
        "id": "gemini_cli",
        "display_name": "Gemini CLI",
        "executable": "gemini",
        "version_args": ["--version"],
    },
    {
        "id": "opencode",
        "display_name": "OpenCode",
        "executable": "opencode",
        "version_args": ["--version"],
    },
    {
        "id": "aider",
        "display_name": "Aider",
        "executable": "aider",
        "version_args": ["--version"],
    },
    {
        "id": "goose",
        "display_name": "Goose",
        "executable": "goose",
        "version_args": ["--version"],
    },
    {
        "id": "cursor_agent",
        "display_name": "Cursor Agent",
        "executable": "cursor-agent",
        "version_args": ["--version"],
    },
]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_inventory(timeout_seconds=args.timeout_seconds)
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory local agent hosts that may run the generic adapter contract.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=10,
        help="Timeout for lightweight version/auth preflight commands.",
    )
    parser.add_argument("--output-json", help="Optional path to persist the inventory report.")
    return parser


def build_inventory(*, timeout_seconds: int) -> dict[str, Any]:
    hosts = [inspect_candidate(candidate, timeout_seconds=timeout_seconds) for candidate in CANDIDATES]
    installed_hosts = [host["id"] for host in hosts if host["installed"]]
    live_ready_hosts = [host["id"] for host in hosts if host["live_readiness"] == "ready_for_live_validation"]
    blocked_hosts = [host for host in hosts if host["live_readiness"].startswith("blocked")]
    return {
        "ok": True,
        "action": "agent-host-inventory",
        "repo_root": str(REPO_ROOT),
        "generated_at": utc_now_iso(),
        "hosts": hosts,
        "summary": {
            "installed_hosts": installed_hosts,
            "live_ready_hosts": live_ready_hosts,
            "blocked_hosts": [{"id": host["id"], "reason": host.get("blocker")} for host in blocked_hosts],
            "missing_hosts": [host["id"] for host in hosts if not host["installed"]],
        },
        "next_validation_command": (
            "python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py "
            "--agent-label <host_id> --agent-command '<agent command>'"
        ),
    }


def inspect_candidate(candidate: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    executable = candidate["executable"]
    executable_path = shutil.which(executable)
    host: dict[str, Any] = {
        "id": candidate["id"],
        "display_name": candidate["display_name"],
        "executable": executable,
        "executable_path": executable_path,
        "installed": executable_path is not None,
        "adapter_command": candidate.get("adapter_command"),
        "json_wrapper_command": build_json_wrapper_command(candidate.get("adapter_command")),
        "live_readiness": "missing_cli",
        "blocker": "cli_not_found",
    }
    if executable_path is None:
        return host

    version = run_command([executable_path, *candidate.get("version_args", [])], timeout_seconds=timeout_seconds)
    host["version"] = version
    host["live_readiness"] = "installed_needs_agent_contract_validation"
    host["blocker"] = "live_validation_not_run"

    auth_args = candidate.get("auth_args")
    if auth_args:
        auth = run_command([executable_path, *auth_args], timeout_seconds=timeout_seconds)
        auth_payload = parse_json(auth["stdout"])
        host["auth"] = auth_payload if isinstance(auth_payload, dict) else auth
        if isinstance(auth_payload, dict) and auth_payload.get("loggedIn") is True:
            host["live_readiness"] = "ready_for_live_validation"
            host["blocker"] = None
        elif isinstance(auth_payload, dict) and auth_payload.get("loggedIn") is False:
            host["live_readiness"] = "blocked_auth"
            host["blocker"] = "not_logged_in"
        elif auth["returncode"] != 0:
            host["live_readiness"] = "blocked_auth_unknown"
            host["blocker"] = "auth_preflight_failed"
    return host


def build_json_wrapper_command(adapter_command: str | None) -> str | None:
    if not adapter_command:
        return None
    return (
        "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py "
        f"--agent-command {shlex.quote(adapter_command)}"
    )


def run_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "").strip(),
            "stderr": (completed.stderr or "").strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "timeout_seconds": timeout_seconds,
            "stdout": ensure_text(exc.stdout).strip(),
            "stderr": ensure_text(exc.stderr).strip(),
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "launch_failed": True,
        }


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
