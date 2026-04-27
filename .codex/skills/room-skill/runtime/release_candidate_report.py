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
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-release-candidate"


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
            "Generate a release candidate support-scope report. "
            "This command wraps the checked-in release gate and renders a claim-safe Markdown summary."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for release candidate evidence. Defaults outside the repository.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout for lightweight readiness checks.",
    )
    parser.add_argument(
        "--include-fixture-runs",
        action="store_true",
        help="Include fixture-backed generic adapter and JSON wrapper validations.",
    )
    parser.add_argument(
        "--strict-git-clean",
        action="store_true",
        help="Treat a dirty working tree as a release candidate blocker.",
    )
    parser.add_argument("--output-json", help="Optional path to write the release candidate JSON report.")
    parser.add_argument("--output-markdown", help="Optional path to write the release candidate Markdown report.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)

    release_args = argparse.Namespace(
        state_root=str(state_root / "release-readiness"),
        output_json=None,
        timeout_seconds=args.timeout_seconds,
        include_fixture_runs=args.include_fixture_runs,
        strict_git_clean=args.strict_git_clean,
    )
    release_report = release_readiness_check.build_release_report(release_args)
    p0_blockers = release_report.get("p0_blockers") or []
    checks = release_report.get("checks", {})
    git_state = checks.get("git_state", {})
    host_matrix = command_payload(checks.get("local_agent_host_validation_matrix"))
    provider = command_payload(checks.get("provider_readiness"))

    support_scope = build_support_scope(release_report, host_matrix, provider)
    quality_gates = build_quality_gates(release_report)
    next_actions = build_next_actions(release_report, host_matrix, provider)

    report = {
        "ok": not p0_blockers,
        "action": "release-candidate-report",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "commit": git_state.get("head"),
        "git_branch": git_state.get("branch"),
        "release_decision": "ready_for_codex_local_mainline_scope" if not p0_blockers else "blocked",
        "p0_blockers": p0_blockers,
        "support_scope": support_scope,
        "quality_gates": quality_gates,
        "non_blocking_gaps": release_report.get("non_blocking_gaps", []),
        "next_actions": next_actions,
        "source_reports": {
            "release_readiness": release_report,
        },
        "artifacts": {
            "json": str(state_root / "release-candidate-report.json"),
            "markdown": str(state_root / "release-candidate-report.md"),
        },
    }
    return report


def build_support_scope(
    release_report: dict[str, Any],
    host_matrix: dict[str, Any],
    provider: dict[str, Any],
) -> dict[str, Any]:
    provider_criteria = provider.get("pass_criteria", {}) if isinstance(provider, dict) else {}
    host_summary = host_matrix.get("summary", {}) if isinstance(host_matrix, dict) else {}
    checked_live_evidence = collect_checked_in_host_live_evidence()
    matrix_live_hosts = host_summary.get("live_passed_hosts", [])
    real_host_live_passed = sorted(
        set([*matrix_live_hosts, *[item["host_id"] for item in checked_live_evidence]])
    )
    return {
        "ready_to_claim": release_report.get("release_scope", {}).get("ready_to_claim", []),
        "not_claimed": release_report.get("release_scope", {}).get("not_claimed", []),
        "real_host_live_passed": real_host_live_passed,
        "matrix_live_passed": matrix_live_hosts,
        "checked_in_host_live_evidence": checked_live_evidence,
        "real_host_blocked": host_summary.get("blocked_hosts", []),
        "real_host_missing": host_summary.get("missing_hosts", []),
        "provider_live_ready": provider_criteria.get("ready_for_live_run") is True,
        "claim_rules": [
            "Codex local mainline may be claimed only when the release gate has no P0 blockers.",
            "Fixture validation may be claimed only as adapter-contract evidence, not real host-live support.",
            "A third-party local agent may be claimed only when host matrix reports matrix_status=live_passed.",
            "A checked-in host-live evidence report may support a machine/account-scoped host claim only when it cites the checked-in validation command and claimable=true result.",
            "Provider live support may be claimed only after chat_completions_live_validation.py passes with real env files.",
        ],
    }


def collect_checked_in_host_live_evidence() -> list[dict[str, str]]:
    return release_readiness_check.collect_checked_in_host_live_evidence()


def build_quality_gates(release_report: dict[str, Any]) -> list[dict[str, Any]]:
    pass_criteria = release_report.get("pass_criteria", {})
    return [
        {
            "gate": key,
            "status": "pass" if value is True else "fail",
        }
        for key, value in pass_criteria.items()
    ]


def build_next_actions(
    release_report: dict[str, Any],
    host_matrix: dict[str, Any],
    provider: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if release_report.get("p0_blockers"):
        actions.append(
            {
                "priority": "P0",
                "task": "Clear release gate P0 blockers",
                "why": "The repository cannot honestly ship even the Codex local mainline until these are fixed.",
            }
        )
    host_summary = host_matrix.get("summary", {}) if isinstance(host_matrix, dict) else {}
    live_evidence = collect_checked_in_host_live_evidence()
    if not host_summary.get("live_passed_hosts") and not live_evidence:
        actions.append(
            {
                "priority": "P1",
                "task": "Run a real third-party local agent host live validation when an authenticated CLI is available",
                "why": "Multi-host support cannot be claimed from fixture evidence alone.",
            }
        )
    elif not set(host_summary.get("live_passed_hosts", [])).difference({"claude_code"}):
        actions.append(
            {
                "priority": "P2",
                "task": "Validate additional real local agent hosts when their CLIs are installed",
                "why": "Claude Code has machine/account-scoped evidence; Gemini/OpenCode/Aider/Goose/Cursor Agent still need their own host-live evidence.",
            }
        )
    provider_criteria = provider.get("pass_criteria", {}) if isinstance(provider, dict) else {}
    if provider_criteria.get("ready_for_live_run") is not True:
        actions.append(
            {
                "priority": "P2",
                "task": "Configure provider env files and run provider live validation if the fallback provider lane matters",
                "why": "Provider URLs are not required for local mainline, but they are required before provider-live claims.",
            }
        )
    actions.append(
        {
            "priority": "P2",
            "task": "Create a release tag after the support scope is accepted",
            "why": "A tag makes the launchable Codex-local scope reproducible for Mac, Windows, and future agent handoff.",
        }
    )
    return actions


def command_payload(summary: Any) -> dict[str, Any]:
    if isinstance(summary, dict) and isinstance(summary.get("payload"), dict):
        return summary["payload"]
    return {}


def render_markdown(report: dict[str, Any]) -> str:
    support = report["support_scope"]
    lines = [
        "# Release Candidate Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Commit: `{report.get('commit') or 'unknown'}`",
        f"- Decision: `{report['release_decision']}`",
        f"- Repo root: `{report['repo_root']}`",
        "",
        "## Current Support Scope",
        "",
        "| Category | Status | Evidence |",
        "|---|---|---|",
        row("Codex local mainline", "ready" if report["ok"] else "blocked", "Release gate P0 blockers are empty." if report["ok"] else "Release gate has P0 blockers."),
        row("Claude Code project skill discovery", "ready", "Project skill validator is part of the release gate."),
        row("Generic local agent adapter contract", "ready", "Fixture-backed adapter validation is included when --include-fixture-runs is used."),
        row("Third-party local agent host-live support", "ready" if support["real_host_live_passed"] else "not claimed", f"Live-passed hosts: {', '.join(support['real_host_live_passed']) or 'none'}."),
        row("Provider live support", "not claimed" if not support["provider_live_ready"] else "ready", "Provider readiness is false until real env files are valid." if not support["provider_live_ready"] else "Provider readiness reports ready."),
        "",
        "## Ready To Claim",
        "",
    ]
    lines.extend(f"- {item}" for item in support["ready_to_claim"])
    lines.extend(["", "## Not Claimed", ""])
    lines.extend(f"- {item}" for item in support["not_claimed"])
    lines.extend(["", "## Checked-In Host Live Evidence", ""])
    if support["checked_in_host_live_evidence"]:
        for item in support["checked_in_host_live_evidence"]:
            lines.append(f"- `{item['host_id']}`: {item['scope']} ({item['report']})")
    else:
        lines.append("- none")
    lines.extend(["", "## Quality Gates", "", "| Gate | Status |", "|---|---|"])
    for gate in report["quality_gates"]:
        lines.append(row(gate["gate"], gate["status"]))
    lines.extend(["", "## Non-Blocking Gaps", ""])
    if report["non_blocking_gaps"]:
        for gap in report["non_blocking_gaps"]:
            lines.append(f"- `{gap.get('id')}`: {gap.get('why_not_p0')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Rules", ""])
    lines.extend(f"- {item}" for item in support["claim_rules"])
    lines.extend(["", "## Next Actions", "", "| Priority | Task | Why |", "|---|---|---|"])
    for action in report["next_actions"]:
        lines.append(row(action["priority"], action["task"], action["why"]))
    return "\n".join(lines) + "\n"


def row(*values: str) -> str:
    return "| " + " | ".join(escape_md(str(value)) for value in values) + " |"


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


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
