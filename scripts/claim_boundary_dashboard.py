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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.runtime.paths import assert_no_symlink_components, resolve_checked_path

RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from secret_redaction import redact_sensitive_text, redact_sensitive_value

DEFAULT_MARKDOWN = REPO_ROOT / "reports" / "claim-boundary-dashboard.md"
DEFAULT_JSON = REPO_ROOT / "reports" / "claim-boundary-dashboard.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a claim boundary dashboard.")
    parser.add_argument("--state-root", default=str(Path(tempfile.gettempdir()) / "round-table-claim-boundary-dashboard"))
    parser.add_argument("--output-markdown", default=str(DEFAULT_MARKDOWN))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument(
        "--strict-git-clean",
        action="store_true",
        help="Require the release-readiness gate to treat a dirty worktree as a local-mainline blocker.",
    )
    args = parser.parse_args()

    report = build_report(args)
    markdown = render_markdown(report)
    write_json(resolve_checked_path(args.output_json), report)
    write_text(resolve_checked_path(args.output_markdown), markdown)
    print(json.dumps(redact_sensitive_value(report), ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = iso_now()
    stale_after = iso_after(days=7)
    source_commit = git_commit()
    state_root = resolve_state_root(args.state_root)
    machine_scope = portable_machine_scope()
    live_report = run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/live_lane_evidence_report.py",
            "--state-root",
            str(state_root),
            "--timeout-seconds",
            str(args.timeout_seconds),
        ],
        timeout_seconds=args.timeout_seconds + 30,
    )
    payload = live_report.get("payload") if isinstance(live_report.get("payload"), dict) else {}
    host_lanes = payload.get("host_live_lanes", []) if isinstance(payload, dict) else []
    provider_lane = payload.get("provider_live_lane", {}) if isinstance(payload, dict) else {}
    release_check = run_release_check(args, state_root=state_root)
    release_payload = release_check.get("payload") if isinstance(release_check.get("payload"), dict) else {}
    release_blockers = release_payload.get("release_blockers", []) if isinstance(release_payload, dict) else []
    local_mainline_claimable = release_check.get("ok") is True and isinstance(release_blockers, list) and not release_blockers
    local_mainline_status = "supported" if local_mainline_claimable else "blocked"
    release_artifacts = artifact_paths_from_payload(release_payload, state_root=state_root)
    live_artifacts = artifact_paths_from_payload(payload, state_root=state_root)
    rows = [
        {
            "lane": "local_mainline",
            "status": local_mainline_status,
            "claim": "Codex local-first mainline when aggregate release-check has no blockers",
            "evidence": {
                "release_check": summarize_release_check(release_check, state_root=state_root),
            },
            "evidence_record": build_evidence_record(
                lane="local_mainline",
                status=local_mainline_status,
                generated_at=generated_at,
                stale_after=stale_after,
                source_commit=source_commit,
                machine_scope=machine_scope,
                claimable=local_mainline_claimable,
                claim_text="Local-first fixture/runtime mainline supported when release-check has no blockers.",
                artifact_paths=release_artifacts,
            ),
        }
    ]
    for lane in host_lanes:
        rows.append(
            {
                "lane": f"host:{lane.get('host_id')}",
                "status": normalize_status(lane.get("evidence_status")),
                "claim": lane.get("claim"),
                "evidence": sanitize(lane.get("checked_in_evidence") or lane.get("next_action"), state_root=state_root),
                "evidence_record": build_evidence_record(
                    lane=f"host:{lane.get('host_id')}",
                    status=normalize_status(lane.get("evidence_status")),
                    generated_at=generated_at,
                    stale_after=stale_after,
                    source_commit=source_commit,
                    machine_scope=machine_scope,
                    host_id=lane.get("host_id"),
                    claimable=normalize_status(lane.get("evidence_status")) == "live_passed",
                    claim_text=str(lane.get("claim") or "not_claimed"),
                    artifact_paths=host_artifact_paths(lane, live_artifacts),
                    source_evidence=sanitize(lane.get("checked_in_evidence"), state_root=state_root),
                ),
            }
        )
    rows.append(
        {
            "lane": "provider:chat_completions",
            "status": normalize_status(provider_lane.get("evidence_status")),
            "claim": provider_lane.get("claim"),
            "evidence": sanitize(provider_lane.get("next_action") or provider_lane.get("blockers"), state_root=state_root),
            "evidence_record": build_evidence_record(
                lane="provider:chat_completions",
                status=normalize_status(provider_lane.get("evidence_status")),
                generated_at=generated_at,
                stale_after=stale_after,
                source_commit=source_commit,
                machine_scope=machine_scope,
                provider_id="chat_completions",
                claimable=normalize_status(provider_lane.get("evidence_status")) == "live_passed",
                claim_text=str(provider_lane.get("claim") or "not_claimed"),
                artifact_paths=live_artifacts,
            ),
        }
    )
    return sanitize({
        "ok": live_report.get("ok") is True and release_check.get("ok") is True,
        "action": "claim-boundary-dashboard",
        "generated_at": generated_at,
        "source_commit": source_commit,
        "stale_after": stale_after,
        "machine_scope": machine_scope,
        "account_scope": "not_collected",
        "source": {
            "command": live_report.get("command"),
            "returncode": live_report.get("returncode"),
            "ok": live_report.get("ok"),
            "summary": payload.get("summary") if isinstance(payload, dict) else None,
            "stderr": live_report.get("stderr"),
        },
        "release_gate": summarize_release_check(release_check, state_root=state_root),
        "matrix": rows,
        "claim_boundary": [
            "Fixture, mock-provider, wrapper, inventory, and config preflight evidence is not live support.",
            "Local-mainline support is claimable only when aggregate ./rtw release-check --include-fixtures returns no blockers.",
            "Only live_passed host/provider evidence may be claimed as live support.",
        ],
    }, state_root=state_root)


def run_release_check(args: argparse.Namespace, *, state_root: Path | None = None) -> dict[str, Any]:
    state_root = state_root or resolve_state_root(args.state_root)
    command = [
        sys.executable,
        "scripts/release_check.py",
        "--include-fixtures",
        "--skip-claim-dashboard",
        "--state-root",
        str(state_root / "release-check"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.strict_git_clean:
        command.append("--strict-git-clean")
    return run_json_command(command, timeout_seconds=args.timeout_seconds + 240)


def summarize_release_check(result: dict[str, Any], *, state_root: Path) -> dict[str, Any]:
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    release_blockers = payload.get("release_blockers", []) if isinstance(payload, dict) else []
    release_warnings = payload.get("release_warnings", []) if isinstance(payload, dict) else []
    return {
        "command": sanitize(result.get("command"), state_root=state_root),
        "returncode": result.get("returncode"),
        "ok": result.get("ok"),
        "release_blockers": release_blockers if isinstance(release_blockers, list) else [],
        "release_warnings": release_warnings if isinstance(release_warnings, list) else [],
        "artifacts": sanitize(payload.get("artifacts"), state_root=state_root) if isinstance(payload, dict) else None,
        "stderr": sanitize(result.get("stderr"), state_root=state_root),
    }


def normalize_status(status: Any) -> str:
    status_text = str(status or "unknown")
    if status_text.startswith("live_passed"):
        return "live_passed"
    if status_text in {"fixture_only", "fixture_passed"}:
        return "fixture_passed"
    if "blocked" in status_text or "failed" in status_text:
        return "blocked"
    if "historical" in status_text:
        return "historical_only"
    if "missing" in status_text or "not_configured" in status_text:
        return "not_configured"
    if "pending" in status_text or "ready" in status_text:
        return "pending_live_validation"
    return "unsupported"


def sanitize(value: Any, *, state_root: Path | None = None) -> Any:
    if isinstance(value, str):
        return sanitize_text(value, state_root=state_root)
    if isinstance(value, list):
        return [sanitize(item, state_root=state_root) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, state_root=state_root) for key, item in value.items()}
    return value


def sanitize_text(value: str, *, state_root: Path | None = None) -> str:
    sanitized = value.replace(str(REPO_ROOT), "<repo>")
    if state_root is not None:
        for candidate in path_aliases(state_root):
            sanitized = sanitized.replace(candidate, "<state-root>")
    temp_dir = Path(tempfile.gettempdir()).resolve()
    sanitized = sanitized.replace(str(temp_dir), "<tmp>")
    node = platform.node()
    if node:
        sanitized = sanitized.replace(node, portable_machine_scope())
    return redact_sensitive_text(sanitized)


def path_aliases(path: Path) -> list[str]:
    text = str(path)
    aliases = [text]
    private_tmp_prefix = "/private/tmp/"
    tmp_prefix = "/tmp/"
    if text.startswith(private_tmp_prefix):
        aliases.append(tmp_prefix + text[len(private_tmp_prefix) :])
    elif text.startswith(tmp_prefix):
        aliases.append(private_tmp_prefix + text[len(tmp_prefix) :])
    return aliases


def portable_machine_scope() -> str:
    return "local-machine-redacted"


def resolve_state_root(value: str | Path) -> Path:
    raw_path = Path(value).expanduser()
    assert_no_symlink_components(raw_path, include_leaf=True)
    return raw_path.resolve()


def build_evidence_record(
    *,
    lane: str,
    status: str,
    generated_at: str,
    stale_after: str,
    source_commit: str,
    claimable: bool,
    claim_text: str,
    machine_scope: str,
    host_id: Any = None,
    provider_id: Any = None,
    artifact_paths: list[str] | None = None,
    source_evidence: Any = None,
) -> dict[str, Any]:
    return {
        "evidence_kind": "claim_boundary_lane",
        "evidence_source": "scripts/claim_boundary_dashboard.py",
        "validator": "live_lane_evidence_report.py",
        "lane": lane,
        "status": status,
        "host_id": host_id,
        "provider_id": provider_id,
        "machine_scope": machine_scope,
        "account_scope": "not_collected",
        "generated_at": generated_at,
        "stale_after": stale_after,
        "source_commit": source_commit,
        "artifact_paths": artifact_paths or [],
        "source_evidence": source_evidence,
        "claimable": claimable,
        "claim_text": claim_text,
    }


def artifact_paths_from_payload(payload: dict[str, Any], *, state_root: Path) -> list[str]:
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
    if not isinstance(artifacts, dict):
        return []
    return [sanitize_text(str(value), state_root=state_root) for value in artifacts.values() if value]


def host_artifact_paths(lane: dict[str, Any], live_artifacts: list[str]) -> list[str]:
    paths = list(live_artifacts)
    checked_in_evidence = lane.get("checked_in_evidence")
    if isinstance(checked_in_evidence, dict) and checked_in_evidence.get("report"):
        paths.append(str(checked_in_evidence["report"]))
    return paths


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
    return redact_sensitive_value({
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is True,
        "payload": payload,
        "stderr": completed.stderr.strip(),
    })


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
    assert_no_symlink_components(path, include_leaf=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_sensitive_value(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    assert_no_symlink_components(path, include_leaf=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
