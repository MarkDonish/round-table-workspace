#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import release_readiness_check


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-live-lane-evidence"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_report(args)

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
            "Generate a claim-safe host/provider live-lane evidence report. "
            "This command does not run real provider calls and does not force third-party agent live execution."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for generated evidence. Defaults outside the repository.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout for lightweight host inventory and provider readiness commands.",
    )
    parser.add_argument("--output-json", help="Optional path to write the report JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write the report Markdown.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)

    host_matrix = release_readiness_check.run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py",
            "--timeout-seconds",
            str(args.timeout_seconds),
            "--state-root",
            str(state_root / "local-agent-host-validation-matrix"),
        ],
        timeout_seconds=args.timeout_seconds + 10,
    )
    provider_readiness = release_readiness_check.run_json_command(
        [sys.executable, ".codex/skills/room-skill/runtime/chat_completions_readiness.py"],
        timeout_seconds=args.timeout_seconds,
    )
    checked_in_host_live_evidence = release_readiness_check.collect_checked_in_host_live_evidence()

    host_matrix_payload = command_payload(host_matrix)
    provider_payload = command_payload(provider_readiness)
    host_lanes = build_host_lanes(host_matrix_payload, checked_in_host_live_evidence)
    provider_lane = build_provider_lane(provider_payload)
    tooling_ok = release_readiness_check.command_ok(host_matrix) and release_readiness_check.command_ok(provider_readiness)

    report = {
        "ok": tooling_ok,
        "action": "live-lane-evidence-report",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "release_impact": {
            "current_launch_scope": "Codex local mainline",
            "local_mainline_requires_provider_url": False,
            "blocks_current_launch_scope": False if tooling_ok else True,
            "decision": "live_lanes_classified" if tooling_ok else "live_lane_tooling_failed",
        },
        "claim_boundary": [
            "Provider URLs are not meeting-room URLs and are not required for the local /room or /debate mainline.",
            "A provider-live claim requires non-mock .env.room and .env.debate plus chat_completions_live_validation.py success.",
            "A third-party local-agent host claim requires matrix_status=live_passed or a checked-in host-live evidence report with claimable=true.",
            "Fixture, mock-provider, inventory, and config-readiness passes are useful evidence but not real provider/host live passes.",
        ],
        "summary": build_summary(host_lanes, provider_lane),
        "host_live_lanes": host_lanes,
        "provider_live_lane": provider_lane,
        "p0_blockers": build_p0_blockers(tooling_ok, host_matrix, provider_readiness),
        "next_actions": build_next_actions(host_lanes, provider_lane),
        "source_reports": {
            "host_validation_matrix": release_readiness_check.summarize_command(host_matrix),
            "provider_readiness": release_readiness_check.summarize_command(provider_readiness),
        },
        "artifacts": {
            "json": str(state_root / "live-lane-evidence-report.json"),
            "markdown": str(state_root / "live-lane-evidence-report.md"),
        },
    }
    return report


def build_host_lanes(
    host_matrix_payload: dict[str, Any],
    checked_in_host_live_evidence: list[dict[str, str]],
) -> list[dict[str, Any]]:
    checked_by_host = {item["host_id"]: item for item in checked_in_host_live_evidence}
    rows = host_matrix_payload.get("hosts", []) if isinstance(host_matrix_payload, dict) else []
    lanes: list[dict[str, Any]] = []
    for row in rows:
        host_id = row.get("id")
        checked_evidence = checked_by_host.get(host_id)
        matrix_status = row.get("matrix_status")
        evidence_status = derive_host_evidence_status(matrix_status, checked_evidence)
        lane = {
            "host_id": host_id,
            "display_name": row.get("display_name"),
            "matrix_status": matrix_status,
            "inventory_readiness": row.get("inventory_readiness"),
            "evidence_status": evidence_status,
            "claim": host_claim(evidence_status, checked_evidence),
            "installed": row.get("installed") is True,
            "checked_in_evidence": checked_evidence,
            "recommended_validation_argv": row.get("recommended_validation_argv"),
            "recommended_validation_command": row.get("recommended_validation_command"),
            "next_action": host_next_action(evidence_status, row),
        }
        lanes.append(lane)

    matrix_host_ids = {lane["host_id"] for lane in lanes}
    for host_id, evidence in checked_by_host.items():
        if host_id in matrix_host_ids:
            continue
        lanes.append(
            {
                "host_id": host_id,
                "display_name": host_id,
                "matrix_status": None,
                "inventory_readiness": None,
                "evidence_status": "live_passed_checked_in_evidence",
                "claim": "claimable_for_checked_in_evidence_scope",
                "installed": None,
                "checked_in_evidence": evidence,
                "recommended_validation_argv": None,
                "recommended_validation_command": None,
                "next_action": "Rerun host-specific live validation on every new machine/account before extending this claim.",
            }
        )
    return lanes


def derive_host_evidence_status(matrix_status: Any, checked_evidence: dict[str, str] | None) -> str:
    if checked_evidence:
        return "live_passed_checked_in_evidence"
    if matrix_status == "live_passed":
        return "live_passed_current_matrix_run"
    if matrix_status == "live_failed":
        return "live_failed_current_matrix_run"
    if matrix_status == "blocked":
        return "blocked"
    if matrix_status == "missing_cli":
        return "missing_cli"
    if matrix_status == "pending_live_validation":
        return "pending_live_validation"
    return str(matrix_status or "unknown")


def host_claim(evidence_status: str, checked_evidence: dict[str, str] | None) -> str:
    if evidence_status == "live_passed_checked_in_evidence":
        return f"claimable_for_scope:{checked_evidence.get('scope')}" if checked_evidence else "claimable"
    if evidence_status == "live_passed_current_matrix_run":
        return "claimable_for_current_command_and_machine"
    return "not_claimed"


def host_next_action(evidence_status: str, row: dict[str, Any]) -> str:
    if evidence_status == "live_passed_checked_in_evidence":
        return "Keep the claim machine/account-scoped; rerun live validation on new machines."
    if evidence_status == "live_passed_current_matrix_run":
        return "Persist or cite the matrix artifact before making this host-live claim."
    if evidence_status == "missing_cli":
        return row.get("next_action") or "Install the host CLI or skip this host on this machine."
    if evidence_status == "blocked":
        return row.get("next_action") or "Clear auth/config blocker before live validation."
    if evidence_status == "pending_live_validation":
        return row.get("next_action") or "Run the recommended validation command before claiming support."
    if evidence_status == "live_failed_current_matrix_run":
        return row.get("next_action") or "Inspect failed live evidence before claiming support."
    return row.get("next_action") or "Review the host matrix row."


def build_provider_lane(provider_payload: dict[str, Any]) -> dict[str, Any]:
    criteria = provider_payload.get("pass_criteria", {}) if isinstance(provider_payload, dict) else {}
    checks = provider_payload.get("checks", {}) if isinstance(provider_payload, dict) else {}
    ready_for_live_run = criteria.get("ready_for_live_run") is True
    blockers = []
    for scope in ("room", "debate"):
        check = checks.get(scope, {}) if isinstance(checks, dict) else {}
        if not check.get("ready"):
            blockers.append(
                {
                    "scope": scope,
                    "blocker": check.get("blocker") or "unknown",
                    "error": check.get("error") or "信息缺失",
                }
            )
    return {
        "evidence_status": "ready_for_live_validation" if ready_for_live_run else "blocked_or_not_configured",
        "claim": "not_claimed" if not ready_for_live_run else "ready_to_attempt_live_validation_not_yet_live_passed",
        "local_mainline_requires_provider_url": False,
        "ready_for_live_run": ready_for_live_run,
        "room_provider_ready": criteria.get("room_provider_ready") is True,
        "debate_provider_ready": criteria.get("debate_provider_ready") is True,
        "blockers": blockers,
        "next_action": provider_payload.get("next_action") or "Run chat_completions_readiness.py before provider live validation.",
        "live_validation_command": provider_payload.get("live_validation_command"),
    }


def build_summary(host_lanes: list[dict[str, Any]], provider_lane: dict[str, Any]) -> dict[str, Any]:
    return {
        "claimable_host_live": [
            lane["host_id"] for lane in host_lanes if str(lane.get("claim", "")).startswith("claimable")
        ],
        "missing_host_cli": [
            lane["host_id"] for lane in host_lanes if lane.get("evidence_status") == "missing_cli"
        ],
        "blocked_host_live": [
            lane["host_id"] for lane in host_lanes if lane.get("evidence_status") == "blocked"
        ],
        "pending_host_live": [
            lane["host_id"] for lane in host_lanes if lane.get("evidence_status") == "pending_live_validation"
        ],
        "failed_host_live": [
            lane["host_id"] for lane in host_lanes if lane.get("evidence_status") == "live_failed_current_matrix_run"
        ],
        "provider_live_ready": provider_lane.get("ready_for_live_run") is True,
        "provider_live_claimed": False,
        "provider_url_required_for_local_mainline": False,
    }


def build_p0_blockers(
    tooling_ok: bool,
    host_matrix: dict[str, Any],
    provider_readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    if tooling_ok:
        return []
    blockers = []
    if not release_readiness_check.command_ok(host_matrix):
        blockers.append(
            {
                "id": "host_matrix_tooling_failed",
                "detail": release_readiness_check.command_failure_detail(host_matrix),
            }
        )
    if not release_readiness_check.command_ok(provider_readiness):
        blockers.append(
            {
                "id": "provider_readiness_tooling_failed",
                "detail": release_readiness_check.command_failure_detail(provider_readiness),
            }
        )
    return blockers


def build_next_actions(host_lanes: list[dict[str, Any]], provider_lane: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if any(lane.get("evidence_status") == "live_failed_current_matrix_run" for lane in host_lanes):
        actions.append(
            {
                "priority": "P1",
                "task": "Investigate failed host-live validation rows",
                "why": "A failed live run blocks that specific host claim until the persisted evidence is understood.",
            }
        )
    if any(lane.get("evidence_status") == "pending_live_validation" for lane in host_lanes):
        actions.append(
            {
                "priority": "P2",
                "task": "Run pending installed-host live validation",
                "why": "Installed hosts cannot be claimed until the recommended validation command passes.",
            }
        )
    if any(lane.get("evidence_status") == "missing_cli" for lane in host_lanes):
        actions.append(
            {
                "priority": "P2",
                "task": "Install or explicitly skip missing local agent CLIs",
                "why": "Missing CLIs block only their own host lanes, not the Codex local mainline.",
            }
        )
    if provider_lane.get("ready_for_live_run") is not True:
        actions.append(
            {
                "priority": "P2",
                "task": "Configure provider env files only if provider-live support will be claimed",
                "why": "Provider URL is optional fallback infrastructure, not the local meeting room.",
            }
        )
    if not actions:
        actions.append(
            {
                "priority": "P3",
                "task": "Keep live lane evidence fresh before each support claim",
                "why": "Host/provider claims are environment-scoped and can drift over time.",
            }
        )
    return actions


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live Lane Evidence Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Decision: `{report['release_impact']['decision']}`",
        f"- Blocks current launch scope: `{str(report['release_impact']['blocks_current_launch_scope']).lower()}`",
        f"- Local mainline requires provider URL: `{str(report['release_impact']['local_mainline_requires_provider_url']).lower()}`",
        "",
        "## Summary",
        "",
        "| Category | Value |",
        "|---|---|",
        row("Claimable host-live lanes", ", ".join(report["summary"]["claimable_host_live"]) or "none"),
        row("Missing host CLIs", ", ".join(report["summary"]["missing_host_cli"]) or "none"),
        row("Blocked host-live lanes", ", ".join(report["summary"]["blocked_host_live"]) or "none"),
        row("Pending host-live lanes", ", ".join(report["summary"]["pending_host_live"]) or "none"),
        row("Provider live ready", str(report["summary"]["provider_live_ready"]).lower()),
        row("Provider URL required for local mainline", str(report["summary"]["provider_url_required_for_local_mainline"]).lower()),
        "",
        "## Claim Boundary",
        "",
    ]
    lines.extend([f"- {item}" for item in report["claim_boundary"]])
    lines.extend(
        [
            "",
            "## Host Live Lanes",
            "",
            "| Host | Evidence Status | Claim | Evidence | Next Action |",
            "|---|---|---|---|---|",
        ]
    )
    for lane in report["host_live_lanes"]:
        evidence = lane.get("checked_in_evidence") or {}
        evidence_text = evidence.get("report") or lane.get("matrix_status") or "none"
        lines.append(
            row(
                lane.get("host_id") or "unknown",
                lane.get("evidence_status") or "unknown",
                lane.get("claim") or "not_claimed",
                evidence_text,
                lane.get("next_action") or "",
            )
        )
    provider = report["provider_live_lane"]
    lines.extend(
        [
            "",
            "## Provider Live Lane",
            "",
            "| Field | Value |",
            "|---|---|",
            row("Evidence status", provider.get("evidence_status")),
            row("Claim", provider.get("claim")),
            row("Ready for live run", str(provider.get("ready_for_live_run")).lower()),
            row("Room provider ready", str(provider.get("room_provider_ready")).lower()),
            row("Debate provider ready", str(provider.get("debate_provider_ready")).lower()),
            row("Next action", provider.get("next_action")),
            "",
            "### Provider Blockers",
            "",
            "| Scope | Blocker | Error |",
            "|---|---|---|",
        ]
    )
    if provider.get("blockers"):
        for blocker in provider["blockers"]:
            lines.append(row(blocker.get("scope"), blocker.get("blocker"), blocker.get("error")))
    else:
        lines.append(row("none", "none", "none"))
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "| Priority | Task | Why |",
            "|---|---|---|",
        ]
    )
    for action in report["next_actions"]:
        lines.append(row(action.get("priority"), action.get("task"), action.get("why")))
    lines.append("")
    return "\n".join(lines)


def command_payload(summary: dict[str, Any]) -> dict[str, Any]:
    payload = summary.get("json") if isinstance(summary, dict) else None
    return payload if isinstance(payload, dict) else {}


def row(*values: Any) -> str:
    return "| " + " | ".join(escape_cell(value) for value in values) + " |"


def escape_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


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
