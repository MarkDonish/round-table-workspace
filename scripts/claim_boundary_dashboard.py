#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKDOWN = REPO_ROOT / "reports" / "claim-boundary-dashboard.md"
DEFAULT_JSON = REPO_ROOT / "reports" / "claim-boundary-dashboard.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a claim boundary dashboard.")
    parser.add_argument("--state-root", default=str(Path(tempfile.gettempdir()) / "round-table-claim-boundary-dashboard"))
    parser.add_argument("--output-markdown", default=str(DEFAULT_MARKDOWN))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    report = build_report(args)
    markdown = render_markdown(report)
    write_json(Path(args.output_json).expanduser().resolve(), report)
    write_text(Path(args.output_markdown).expanduser().resolve(), markdown)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = iso_now()
    stale_after = iso_after(days=7)
    source_commit = git_commit()
    live_report = run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/live_lane_evidence_report.py",
            "--state-root",
            args.state_root,
            "--timeout-seconds",
            str(args.timeout_seconds),
        ],
        timeout_seconds=args.timeout_seconds + 30,
    )
    payload = live_report.get("payload") if isinstance(live_report.get("payload"), dict) else {}
    host_lanes = payload.get("host_live_lanes", []) if isinstance(payload, dict) else []
    provider_lane = payload.get("provider_live_lane", {}) if isinstance(payload, dict) else {}
    rows = [
        {
            "lane": "local_mainline",
            "status": "supported",
            "claim": "Codex local-first mainline when release readiness has no P0 blockers",
            "evidence": "release_readiness_check.py / agent_consumer_self_check.py",
            "evidence_record": build_evidence_record(
                lane="local_mainline",
                status="supported",
                generated_at=generated_at,
                stale_after=stale_after,
                source_commit=source_commit,
                claimable=True,
                claim_text="Local-first fixture/runtime mainline supported when release-check has no P0 blockers.",
            ),
        }
    ]
    for lane in host_lanes:
        rows.append(
            {
                "lane": f"host:{lane.get('host_id')}",
                "status": normalize_status(lane.get("evidence_status")),
                "claim": lane.get("claim"),
                "evidence": sanitize(lane.get("checked_in_evidence") or lane.get("next_action")),
                "evidence_record": build_evidence_record(
                    lane=f"host:{lane.get('host_id')}",
                    status=normalize_status(lane.get("evidence_status")),
                    generated_at=generated_at,
                    stale_after=stale_after,
                    source_commit=source_commit,
                    host_id=lane.get("host_id"),
                    claimable=normalize_status(lane.get("evidence_status")) == "live_passed",
                    claim_text=str(lane.get("claim") or "not_claimed"),
                ),
            }
        )
    rows.append(
        {
            "lane": "provider:chat_completions",
            "status": normalize_status(provider_lane.get("evidence_status")),
            "claim": provider_lane.get("claim"),
            "evidence": sanitize(provider_lane.get("next_action") or provider_lane.get("blockers")),
            "evidence_record": build_evidence_record(
                lane="provider:chat_completions",
                status=normalize_status(provider_lane.get("evidence_status")),
                generated_at=generated_at,
                stale_after=stale_after,
                source_commit=source_commit,
                provider_id="chat_completions",
                claimable=normalize_status(provider_lane.get("evidence_status")) == "live_passed",
                claim_text=str(provider_lane.get("claim") or "not_claimed"),
            ),
        }
    )
    return {
        "ok": live_report.get("ok") is True,
        "action": "claim-boundary-dashboard",
        "generated_at": generated_at,
        "source_commit": source_commit,
        "stale_after": stale_after,
        "machine_scope": platform.node() or "unknown-local-machine",
        "account_scope": "not_collected",
        "source": {
            "command": live_report.get("command"),
            "returncode": live_report.get("returncode"),
            "ok": live_report.get("ok"),
            "summary": payload.get("summary") if isinstance(payload, dict) else None,
            "stderr": live_report.get("stderr"),
        },
        "matrix": rows,
        "claim_boundary": [
            "Fixture, mock-provider, wrapper, inventory, and config preflight evidence is not live support.",
            "Only live_passed host/provider evidence may be claimed as live support.",
        ],
    }


def normalize_status(status: Any) -> str:
    status_text = str(status or "unknown")
    if status_text.startswith("live_passed"):
        return "live_passed"
    if status_text in {"fixture_only", "fixture_passed"}:
        return "fixture_passed"
    if "blocked" in status_text or "failed" in status_text:
        return "blocked"
    if "missing" in status_text or "not_configured" in status_text:
        return "not_configured"
    if "pending" in status_text or "ready" in status_text:
        return "pending_live_validation"
    return "unsupported"


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(str(REPO_ROOT), "<repo>")
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    return value


def build_evidence_record(
    *,
    lane: str,
    status: str,
    generated_at: str,
    stale_after: str,
    source_commit: str,
    claimable: bool,
    claim_text: str,
    host_id: Any = None,
    provider_id: Any = None,
) -> dict[str, Any]:
    return {
        "evidence_kind": "claim_boundary_lane",
        "evidence_source": "scripts/claim_boundary_dashboard.py",
        "validator": "live_lane_evidence_report.py",
        "lane": lane,
        "status": status,
        "host_id": host_id,
        "provider_id": provider_id,
        "machine_scope": platform.node() or "unknown-local-machine",
        "account_scope": "not_collected",
        "generated_at": generated_at,
        "stale_after": stale_after,
        "source_commit": source_commit,
        "artifact_paths": [],
        "claimable": claimable,
        "claim_text": claim_text,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Claim Boundary Dashboard",
        "",
        "> Generated by `scripts/claim_boundary_dashboard.py`.",
        "> This dashboard is evidence classification, not a live-support claim by itself.",
        f"> generated_at: `{report.get('generated_at')}`",
        f"> source_commit: `{report.get('source_commit')}`",
        f"> stale_after: `{report.get('stale_after')}`",
        f"> machine_scope: `{report.get('machine_scope')}`",
        f"> account_scope: `{report.get('account_scope')}`",
        "",
        "| Lane | Status | Claim | Evidence / Missing Reason |",
        "|---|---|---|---|",
    ]
    for row in report["matrix"]:
        evidence = json.dumps(row["evidence"], ensure_ascii=False) if isinstance(row["evidence"], (dict, list)) else str(row["evidence"])
        lines.append(f"| `{row['lane']}` | `{row['status']}` | `{row['claim']}` | {evidence} |")
    lines.extend(["", "## Claim Boundary", ""])
    for item in report["claim_boundary"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def run_json_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout_seconds, check=False)
    payload = extract_json(completed.stdout)
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is not False,
        "payload": payload,
        "stderr": completed.stderr.strip(),
    }


def extract_json(text: str) -> Any:
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


def git_commit() -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "unknown"
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    suffix = "+dirty" if status.returncode == 0 and status.stdout.strip() else ""
    return completed.stdout.strip() + suffix


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_after(*, days: int) -> str:
    return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
