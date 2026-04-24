#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import agent_host_inventory


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path("/tmp") / "round-table-local-agent-host-validation-matrix"
VALIDATION_SCRIPT = ".codex/skills/room-skill/runtime/generic_agent_adapter_validation.py"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_matrix(args)
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else Path(report["artifacts"]["json"])
    output_markdown = (
        Path(args.output_markdown).expanduser().resolve()
        if args.output_markdown
        else Path(report["artifacts"]["markdown"])
    )
    write_json(output_json, report)
    write_text(output_markdown, render_markdown(report))
    report["artifacts"]["json"] = str(output_json)
    report["artifacts"]["markdown"] = str(output_markdown)
    write_json(output_json, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a host validation matrix for local third-party agent CLIs. "
            "By default this is safe: it inventories hosts and records blocked/missing/pending status "
            "without forcing live agent execution."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for validation matrix evidence and optional live runs.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout for lightweight inventory version/auth preflight commands.",
    )
    parser.add_argument(
        "--agent-timeout-seconds",
        type=int,
        default=900,
        help="Timeout for each prompt call when --run-live-ready is enabled.",
    )
    parser.add_argument(
        "--run-live-ready",
        action="store_true",
        help="Run generic adapter validation for hosts whose inventory status is ready_for_live_validation.",
    )
    parser.add_argument(
        "--run-installed",
        action="store_true",
        help=(
            "Also run generic adapter validation for installed hosts with installed_needs_agent_contract_validation. "
            "Auth-blocked hosts are still skipped unless --force-host is used."
        ),
    )
    parser.add_argument(
        "--force-host",
        action="append",
        default=[],
        help="Force live validation for a specific host id even if inventory reports it as blocked or pending.",
    )
    parser.add_argument(
        "--agent-command",
        action="append",
        default=[],
        metavar="HOST_ID=COMMAND",
        help=(
            "Override the validation command for a host. Example: "
            "--agent-command claude_code='python3 .../generic_agent_json_wrapper.py --agent-command ...'"
        ),
    )
    parser.add_argument("--output-json", help="Optional path to write the validation matrix JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write the validation matrix Markdown.")
    return parser


def build_matrix(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    command_overrides = parse_command_overrides(args.agent_command)
    forced_hosts = set(args.force_host or [])
    inventory = agent_host_inventory.build_inventory(timeout_seconds=args.timeout_seconds)
    rows = []
    for host in inventory["hosts"]:
        row = build_host_row(
            host,
            state_root=state_root,
            command_overrides=command_overrides,
            forced_hosts=forced_hosts,
            run_live_ready=args.run_live_ready,
            run_installed=args.run_installed,
            agent_timeout_seconds=args.agent_timeout_seconds,
        )
        rows.append(row)

    summary = summarize_rows(rows)
    p0_blockers = []
    if any(row["matrix_status"] == "live_failed" for row in rows):
        p0_blockers.append("host_live_validation_failed")

    report = {
        "ok": not p0_blockers,
        "action": "local-agent-host-validation-matrix",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "run_policy": {
            "run_live_ready": args.run_live_ready,
            "run_installed": args.run_installed,
            "forced_hosts": sorted(forced_hosts),
            "live_execution_default": "disabled",
        },
        "summary": summary,
        "p0_blockers": p0_blockers,
        "interpretation": {
            "current_launch_scope": "Codex local mainline is not blocked by missing third-party host live validation.",
            "multi_host_claim_rule": "Only rows with matrix_status=live_passed may be claimed as real host-live support.",
            "fixture_rule": "Fixture and wrapper validation prove the adapter contract, not a specific third-party host.",
        },
        "inventory": {
            "summary": inventory.get("summary"),
            "next_validation_command": inventory.get("next_validation_command"),
        },
        "hosts": rows,
        "artifacts": {
            "json": str(state_root / "local-agent-host-validation-matrix.json"),
            "markdown": str(state_root / "local-agent-host-validation-matrix.md"),
        },
    }
    return report


def build_host_row(
    host: dict[str, Any],
    *,
    state_root: Path,
    command_overrides: dict[str, str],
    forced_hosts: set[str],
    run_live_ready: bool,
    run_installed: bool,
    agent_timeout_seconds: int,
) -> dict[str, Any]:
    host_id = host["id"]
    command = command_overrides.get(host_id) or host.get("json_wrapper_command") or host.get("adapter_command")
    validation_command = build_validation_command(host_id, command, state_root)
    row: dict[str, Any] = {
        "id": host_id,
        "display_name": host.get("display_name"),
        "installed": host.get("installed") is True,
        "executable_path": host.get("executable_path"),
        "inventory_readiness": host.get("live_readiness"),
        "inventory_blocker": host.get("blocker"),
        "adapter_command": host.get("adapter_command"),
        "json_wrapper_command": host.get("json_wrapper_command"),
        "selected_agent_command": command,
        "recommended_validation_command": validation_command,
        "matrix_status": "pending",
        "severity": "P1",
        "claim": "not_live_validated",
        "next_action": None,
        "evidence": {},
    }

    readiness = host.get("live_readiness")
    if not host.get("installed"):
        row.update(
            {
                "matrix_status": "missing_cli",
                "severity": "P2",
                "claim": "not_available_on_this_machine",
                "next_action": f"Install `{host.get('executable')}` or skip this host on this machine.",
            }
        )
        return row

    if readiness and str(readiness).startswith("blocked") and host_id not in forced_hosts:
        row.update(
            {
                "matrix_status": "blocked",
                "severity": "P1",
                "claim": "installed_but_not_live_validated",
                "next_action": next_action_for_blocked_host(host),
            }
        )
        return row

    should_run = host_id in forced_hosts
    should_run = should_run or (run_live_ready and readiness == "ready_for_live_validation")
    should_run = should_run or (run_installed and readiness == "installed_needs_agent_contract_validation")

    if not should_run:
        row.update(
            {
                "matrix_status": "pending_live_validation",
                "severity": "P1",
                "claim": "installed_but_validation_not_run",
                "next_action": "Run the recommended validation command, or rerun this matrix with --run-live-ready/--run-installed.",
            }
        )
        return row

    if not command:
        row.update(
            {
                "matrix_status": "blocked",
                "severity": "P1",
                "claim": "installed_but_no_agent_command",
                "next_action": "Provide --agent-command HOST_ID=COMMAND for this host.",
            }
        )
        return row

    validation = run_validation(
        host_id=host_id,
        command=command,
        state_root=state_root / host_id,
        timeout_seconds=agent_timeout_seconds,
    )
    row["evidence"]["validation"] = validation
    if validation["returncode"] == 0 and validation.get("report", {}).get("ok") is True:
        row.update(
            {
                "matrix_status": "live_passed",
                "severity": "clear",
                "claim": "real_host_live_validated",
                "next_action": "This host can be claimed as live validated for the current command.",
            }
        )
    else:
        row.update(
            {
                "matrix_status": "live_failed",
                "severity": "P0_for_this_host_lane",
                "claim": "real_host_live_validation_failed",
                "next_action": "Inspect validation stdout/stderr and the persisted validation report before claiming support.",
            }
        )
    return row


def parse_command_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid --agent-command value {value!r}; expected HOST_ID=COMMAND.")
        host_id, command = value.split("=", 1)
        host_id = host_id.strip()
        command = command.strip()
        if not host_id or not command:
            raise SystemExit(f"Invalid --agent-command value {value!r}; expected HOST_ID=COMMAND.")
        overrides[host_id] = command
    return overrides


def build_validation_command(host_id: str, command: str | None, state_root: Path) -> str | None:
    if not command:
        return None
    return (
        f"python3 {VALIDATION_SCRIPT} "
        f"--agent-label {shlex.quote(host_id)} "
        f"--agent-command {shlex.quote(command)} "
        f"--state-root {shlex.quote(str(state_root / host_id))}"
    )


def run_validation(*, host_id: str, command: str, state_root: Path, timeout_seconds: int) -> dict[str, Any]:
    output_json = state_root / "generic-agent-adapter-validation-report.json"
    validation_command = [
        sys.executable,
        VALIDATION_SCRIPT,
        "--agent-label",
        host_id,
        "--agent-command",
        command,
        "--state-root",
        str(state_root),
        "--timeout-seconds",
        str(timeout_seconds),
        "--output-json",
        str(output_json),
    ]
    completed = subprocess.run(
        validation_command,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    report = read_json_if_exists(output_json)
    return {
        "command": validation_command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "report_path": str(output_json),
        "report": report,
    }


def next_action_for_blocked_host(host: dict[str, Any]) -> str:
    if host.get("id") == "claude_code" and host.get("blocker") == "not_logged_in":
        return "Run `claude auth login` on this machine, then rerun the matrix with --run-live-ready."
    return "Clear the inventory blocker, then run the recommended validation command."


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["matrix_status"]] = counts.get(row["matrix_status"], 0) + 1
    return {
        "total_hosts": len(rows),
        "live_passed_hosts": [row["id"] for row in rows if row["matrix_status"] == "live_passed"],
        "blocked_hosts": [row["id"] for row in rows if row["matrix_status"] == "blocked"],
        "missing_hosts": [row["id"] for row in rows if row["matrix_status"] == "missing_cli"],
        "pending_hosts": [row["id"] for row in rows if row["matrix_status"] == "pending_live_validation"],
        "failed_hosts": [row["id"] for row in rows if row["matrix_status"] == "live_failed"],
        "counts": counts,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Local Agent Host Validation Matrix",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- State root: `{report['state_root']}`",
        f"- Current launch scope: {report['interpretation']['current_launch_scope']}",
        f"- Multi-host claim rule: {report['interpretation']['multi_host_claim_rule']}",
        "",
        "| Host | Matrix Status | Severity | Claim | Inventory Readiness | Blocker | Next Action |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in report["hosts"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_md(row["id"]),
                    escape_md(row["matrix_status"]),
                    escape_md(row["severity"]),
                    escape_md(row["claim"]),
                    escape_md(str(row.get("inventory_readiness"))),
                    escape_md(str(row.get("inventory_blocker"))),
                    escape_md(str(row.get("next_action"))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Commands",
            "",
        ]
    )
    for row in report["hosts"]:
        command = row.get("recommended_validation_command")
        if not command:
            continue
        lines.extend([f"### {row['id']}", "", "```bash", command, "```", ""])
    return "\n".join(lines) + "\n"


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
