#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-agent-consumer-self-check"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.runtime import (
    RunRecord,
    build_run_evidence,
    create_run_dir,
    write_evidence,
    write_input,
    write_output,
    write_summary,
)


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(args)
    markdown = render_markdown(report)

    output_json = (
        Path(args.output_json).expanduser().resolve()
        if args.output_json
        else Path(report["artifacts"]["json"])
    )
    output_markdown = (
        Path(args.output_markdown).expanduser().resolve()
        if args.output_markdown
        else Path(report["artifacts"]["markdown"])
    )
    report["artifacts"]["json"] = str(output_json)
    report["artifacts"]["markdown"] = str(output_markdown)
    write_json(output_json, report)
    write_text(output_markdown, markdown)
    write_json(Path(report["artifacts"]["standard_json"]), report)
    write_text(Path(report["artifacts"]["standard_markdown"]), markdown)
    run_record = RunRecord(
        state_root=Path(report["run"]["state_root"]),
        run_dir=Path(report["run"]["run_dir"]),
        run_id=report["run"]["run_id"],
        workflow=report["run"]["workflow"],
        created_at=report["run"]["created_at"],
    )
    write_output(Path(report["run"]["run_dir"]), report)
    write_evidence(
        Path(report["run"]["run_dir"]),
        build_run_evidence(
            run=run_record,
            action="agent-consumer-self-check",
            input_data=report["input"],
            claim_boundary=report["claim_boundary"],
            host="local",
            provider_lane="not_required",
        ),
    )
    write_summary(Path(report["run"]["run_dir"]), markdown)
    write_json(output_json, report)
    write_json(Path(report["artifacts"]["standard_json"]), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a clone-friendly consumer self-check for Codex, Claude Code, and other local agent hosts. "
            "This command does not require provider URLs and does not require third-party account login."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for generated self-check evidence.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip fixture-backed adapter/wrapper runs and only run lightweight preflights.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout passed to lightweight readiness subprocess checks.",
    )
    parser.add_argument("--output-json", help="Optional path to write the self-check JSON report.")
    parser.add_argument("--output-markdown", help="Optional path to write the self-check Markdown report.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    run_input = {
        "quick": args.quick,
        "timeout_seconds": args.timeout_seconds,
        "state_root": str(state_root),
    }
    run = create_run_dir(state_root, "self-check")
    write_input(run.run_dir, run_input)

    source_audit = run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/source_boundary_audit.py",
            "--output-json",
            str(state_root / "source-boundary-audit.json"),
        ],
        timeout_seconds=max(60, args.timeout_seconds),
    )

    readiness_command = [
        sys.executable,
        ".codex/skills/room-skill/runtime/release_readiness_check.py",
        "--state-root",
        str(state_root / "release-readiness"),
        "--output-json",
        str(state_root / "release-readiness.json"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if not args.quick:
        readiness_command.append("--include-fixture-runs")

    release_readiness = run_json_command(
        readiness_command,
        timeout_seconds=max(360, args.timeout_seconds * 12),
    )
    source_consistency = run_json_command(
        [
            sys.executable,
            "scripts/check_source_truth_consistency.py",
            "--output-json",
            str(state_root / "source-truth-consistency.json"),
            "--output-markdown",
            str(state_root / "source-truth-consistency.md"),
        ],
        timeout_seconds=max(60, args.timeout_seconds),
    )
    skill_drift = run_json_command(
        [
            sys.executable,
            "scripts/check_skill_drift.py",
            "--output-json",
            str(state_root / "skill-drift.json"),
            "--output-markdown",
            str(state_root / "skill-drift.md"),
        ],
        timeout_seconds=max(60, args.timeout_seconds),
    )

    summary = build_summary(
        source_audit=source_audit,
        release_readiness=release_readiness,
        quick=args.quick,
    )
    ok = (
        source_audit.get("ok") is True
        and release_readiness.get("ok") is True
        and source_consistency.get("ok") is True
        and skill_drift.get("ok") is True
        and not summary["p0_blockers"]
    )
    warnings = list(summary.get("non_blocking_gap_ids", []))
    claim_boundary = {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": [
            "Self-check proves local-first repository readiness only.",
            "It does not claim universal host-live or provider-live support.",
        ],
    }

    return {
        "ok": ok,
        "overall_status": "pass" if ok else "fail",
        "action": "agent-consumer-self-check",
        "generated_at": utc_now_iso(),
        "created_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "run": run.to_dict(),
        "input": run_input,
        "mode": "quick" if args.quick else "offline_full",
        "claimable_support": [
            "Codex local-first mainline readiness when all P0 checks pass",
            "checked-in protocol, schema, skill, runtime, and validation source",
        ],
        "blocked_items": summary["p0_blockers"],
        "warnings": warnings,
        "claim_boundary": claim_boundary,
        "summary": summary,
        "checks": {
            "source_boundary_audit": summarize_source_audit(source_audit),
            "release_readiness": summarize_release_readiness(release_readiness),
            "source_truth_consistency": summarize_generic_check(source_consistency),
            "skill_drift": summarize_generic_check(skill_drift),
        },
        "consumer_interpretation": {
            "provider_url_required": False,
            "paid_third_party_account_required_for_this_check": False,
            "reports_and_artifacts_are_source": False,
            "host_live_support_claim_rule": (
                "Only local_agent_host_validation_matrix rows with matrix_status=live_passed, or the full "
                "claude_code_live_validation.py wrapper with claimable_as_default_claude_code_host_live=true, "
                "may be claimed as real host-live support."
            ),
            "fixture_rule": "Offline fixture validation proves the adapter contract, not a specific third-party model account.",
        },
        "next_commands": next_commands(),
        "artifacts": {
            "json": str(state_root / "agent-consumer-self-check.json"),
            "markdown": str(state_root / "agent-consumer-self-check.md"),
            "standard_json": str(state_root / "self-check.json"),
            "standard_markdown": str(state_root / "self-check.md"),
            "run_dir": str(run.run_dir),
            "source_boundary_audit_json": str(state_root / "source-boundary-audit.json"),
            "release_readiness_json": str(state_root / "release-readiness.json"),
            "source_truth_consistency_json": str(state_root / "source-truth-consistency.json"),
            "skill_drift_json": str(state_root / "skill-drift.json"),
        },
    }


def build_summary(
    *,
    source_audit: dict[str, Any],
    release_readiness: dict[str, Any],
    quick: bool,
) -> dict[str, Any]:
    readiness_payload = release_readiness.get("payload") if isinstance(release_readiness.get("payload"), dict) else {}
    pass_criteria = readiness_payload.get("pass_criteria") if isinstance(readiness_payload, dict) else {}
    release_scope = readiness_payload.get("release_scope") if isinstance(readiness_payload, dict) else {}
    p0_blockers = readiness_payload.get("p0_blockers") if isinstance(readiness_payload, dict) else []
    p0_blockers = p0_blockers if isinstance(p0_blockers, list) else ["release_readiness_p0_parse_error"]
    non_blocking_gaps = readiness_payload.get("non_blocking_gaps") if isinstance(readiness_payload, dict) else []
    non_blocking_gap_ids = [
        gap.get("id")
        for gap in non_blocking_gaps
        if isinstance(gap, dict) and gap.get("id")
    ]
    host_summary = extract_host_summary(readiness_payload)
    provider_summary = extract_provider_summary(readiness_payload)
    live_lane_summary = extract_live_lane_summary(readiness_payload)
    source_summary = {}
    if isinstance(source_audit.get("payload"), dict):
        source_summary = source_audit["payload"].get("summary", {})

    return {
        "ship_decision": release_scope.get("ship_decision"),
        "local_first_mainline_ready": not p0_blockers,
        "source_boundary_ok": source_audit.get("ok") is True,
        "release_readiness_ok": release_readiness.get("ok") is True,
        "offline_fixture_runs_included": not quick,
        "provider_url_required": False,
        "paid_third_party_account_required": False,
        "p0_blockers": p0_blockers,
        "non_blocking_gap_ids": non_blocking_gap_ids,
        "pass_criteria": pass_criteria,
        "host_summary": host_summary,
        "provider_summary": provider_summary,
        "live_lane_summary": live_lane_summary,
        "source_boundary_summary": source_summary,
    }


def extract_host_summary(readiness_payload: dict[str, Any]) -> dict[str, Any]:
    checks = readiness_payload.get("checks", {}) if isinstance(readiness_payload, dict) else {}
    matrix = checks.get("local_agent_host_validation_matrix", {}) if isinstance(checks, dict) else {}
    matrix_payload = matrix.get("payload", {}) if isinstance(matrix, dict) else {}
    summary = matrix_payload.get("summary", {}) if isinstance(matrix_payload, dict) else {}
    hosts = matrix_payload.get("hosts", []) if isinstance(matrix_payload, dict) else []
    checked_evidence = readiness_payload.get("checked_in_host_live_evidence", [])
    checked_evidence = checked_evidence if isinstance(checked_evidence, list) else []
    checked_live_hosts = sorted(
        {
            item.get("host_id")
            for item in checked_evidence
            if isinstance(item, dict) and item.get("host_id")
        }
    )
    matrix_live_hosts = summary.get("live_passed_hosts", [])
    matrix_live_hosts = matrix_live_hosts if isinstance(matrix_live_hosts, list) else []
    live_passed_hosts = sorted(set(matrix_live_hosts) | set(checked_live_hosts))
    pending_hosts = summary.get("pending_hosts", [])
    pending_hosts = pending_hosts if isinstance(pending_hosts, list) else []
    return {
        "counts": summary.get("counts", {}),
        "live_passed_hosts": live_passed_hosts,
        "matrix_live_passed_hosts": matrix_live_hosts,
        "checked_in_host_live_evidence": checked_evidence,
        "blocked_hosts": summary.get("blocked_hosts", []),
        "missing_hosts": summary.get("missing_hosts", []),
        "pending_hosts": [host_id for host_id in pending_hosts if host_id not in set(checked_live_hosts)],
        "matrix_pending_hosts": pending_hosts,
        "failed_hosts": summary.get("failed_hosts", []),
        "host_rows": [
            {
                "id": host.get("id"),
                "display_name": host.get("display_name"),
                "matrix_status": host.get("matrix_status"),
                "claim": host.get("claim"),
                "next_action": host.get("next_action"),
            }
            for host in hosts
            if isinstance(host, dict)
        ],
    }


def extract_provider_summary(readiness_payload: dict[str, Any]) -> dict[str, Any]:
    checks = readiness_payload.get("checks", {}) if isinstance(readiness_payload, dict) else {}
    provider = checks.get("provider_readiness", {}) if isinstance(checks, dict) else {}
    payload = provider.get("payload", {}) if isinstance(provider, dict) else {}
    provider_lane = payload.get("provider_lane", {}) if isinstance(payload, dict) else {}
    return {
        "local_mainline_requires_provider_url": provider_lane.get("local_mainline_requires_provider_url", False),
        "ready_for_live_run": payload.get("pass_criteria", {}).get("ready_for_live_run")
        if isinstance(payload.get("pass_criteria"), dict)
        else None,
        "next_action": payload.get("next_action") if isinstance(payload, dict) else None,
    }


def extract_live_lane_summary(readiness_payload: dict[str, Any]) -> dict[str, Any]:
    checks = readiness_payload.get("checks", {}) if isinstance(readiness_payload, dict) else {}
    live_lane = checks.get("live_lane_evidence_report", {}) if isinstance(checks, dict) else {}
    payload = live_lane.get("payload", {}) if isinstance(live_lane, dict) else {}
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    release_impact = payload.get("release_impact", {}) if isinstance(payload, dict) else {}
    return {
        "claimable_host_live": summary.get("claimable_host_live", []),
        "missing_host_cli": summary.get("missing_host_cli", []),
        "blocked_host_live": summary.get("blocked_host_live", []),
        "pending_host_live": summary.get("pending_host_live", []),
        "provider_live_ready": summary.get("provider_live_ready"),
        "provider_url_required_for_local_mainline": summary.get("provider_url_required_for_local_mainline"),
        "blocks_current_launch_scope": release_impact.get("blocks_current_launch_scope"),
    }


def summarize_source_audit(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ok": result.get("ok"),
        "summary": payload.get("summary") if isinstance(payload, dict) else None,
        "missing_required_roots": payload.get("missing_required_roots") if isinstance(payload, dict) else None,
    }


def summarize_release_readiness(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ok": result.get("ok"),
        "ship_decision": payload.get("release_scope", {}).get("ship_decision")
        if isinstance(payload.get("release_scope"), dict)
        else None,
        "p0_blockers": payload.get("p0_blockers") if isinstance(payload, dict) else None,
        "pass_criteria": payload.get("pass_criteria") if isinstance(payload, dict) else None,
    }


def summarize_generic_check(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ok": result.get("ok"),
        "payload": payload,
        "stderr": result.get("stderr"),
    }


def next_commands() -> dict[str, list[str]]:
    return {
        "clone_or_update": [
            "git pull origin main",
            "python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py --state-root /tmp/round-table-agent-consumer-self-check",
        ],
        "codex_local_mainline": [
            "python3 .codex/skills/room-skill/runtime/local_codex_regression.py --state-root /tmp/round-table-local-codex-regression",
        ],
        "claude_code_without_paid_account": [
            "python3 .claude/scripts/validate_project_skills.py",
            "python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py --executor claude_code --agent-command \"python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py\" --state-root /tmp/round-table-claude-code-adapter-fixture",
        ],
        "claude_code_live_after_login": [
            "python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py --preflight-only --state-root /tmp/round-table-claude-code-live-preflight",
            "python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py --smoke-only --state-root /tmp/round-table-claude-code-live-smoke",
            "python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py --state-root /tmp/round-table-claude-code-live",
        ],
        "generic_third_party_agent": [
            "python3 .codex/skills/room-skill/runtime/agent_host_inventory.py --output-json /tmp/round-table-agent-host-inventory.json",
            "python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py --state-root /tmp/round-table-local-agent-host-validation-matrix",
            "python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py --state-root /tmp/round-table-live-lane-evidence",
            "python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py --agent-label <host_id> --agent-command \"python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'\" --state-root /tmp/round-table-<host-id>-validation",
        ],
    }


def run_json_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        payload = parse_json_object(completed.stdout)
        return {
            "command": command,
            "returncode": completed.returncode,
            "json_parse_ok": isinstance(payload, dict),
            "ok": completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is not False,
            "payload": payload,
            "stderr": completed.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "json_parse_ok": False,
            "ok": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "stdout": ensure_text(exc.stdout).strip(),
            "stderr": ensure_text(exc.stderr).strip(),
        }
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "json_parse_ok": False,
            "ok": False,
            "launch_failed": True,
            "stderr": str(exc),
        }


def parse_json_object(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    host_summary = summary.get("host_summary", {})
    provider_summary = summary.get("provider_summary", {})
    status = "PASS" if report["ok"] else "FAIL"
    lines = [
        "# Agent Consumer Self Check",
        "",
        f"- Result: `{status}`",
        f"- Mode: `{report['mode']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Local-first mainline ready: `{summary['local_first_mainline_ready']}`",
        f"- Provider URL required: `{summary['provider_url_required']}`",
        f"- Paid third-party account required for this check: `{summary['paid_third_party_account_required']}`",
        "",
        "## What This Proves",
        "",
        "- The repository source-truth roots are present.",
        "- Reports and artifacts are not treated as active implementation source.",
        "- The release readiness gate can classify P0 blockers versus non-blocking host/provider gaps.",
    ]
    if summary.get("offline_fixture_runs_included"):
        lines.append("- The generic local agent adapter and JSON wrapper passed offline fixture-backed validation.")
    else:
        lines.append("- Fixture-backed adapter and wrapper validation were skipped because `--quick` was used.")

    lines.extend(
        [
            "",
            "## Current Host Status",
            "",
            f"- Live-passed hosts: `{host_summary.get('live_passed_hosts', [])}`",
            f"- Matrix live-passed hosts: `{host_summary.get('matrix_live_passed_hosts', [])}`",
            f"- Checked-in host-live evidence: `{host_summary.get('checked_in_host_live_evidence', [])}`",
            f"- Blocked hosts: `{host_summary.get('blocked_hosts', [])}`",
            f"- Missing hosts: `{host_summary.get('missing_hosts', [])}`",
            f"- Pending hosts: `{host_summary.get('pending_hosts', [])}`",
            f"- Failed hosts: `{host_summary.get('failed_hosts', [])}`",
            "",
            "Only hosts with `matrix_status=live_passed`, or checked-in machine/account-scoped evidence from the full Claude Code wrapper, may be claimed as real host-live support.",
            "",
            "## Provider Lane",
            "",
            f"- Local mainline requires provider URL: `{provider_summary.get('local_mainline_requires_provider_url')}`",
            f"- Provider live ready: `{provider_summary.get('ready_for_live_run')}`",
            f"- Next action: {provider_summary.get('next_action')}",
            "",
            "## Next Commands",
            "",
        ]
    )
    for group, commands in report["next_commands"].items():
        lines.append(f"### {group}")
        lines.append("")
        for command in commands:
            lines.append("```bash")
            lines.append(command)
            lines.append("```")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
