#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-post-release-consumer-audit"
DEFAULT_REF = "v0.1.2"


class AuditError(Exception):
    pass


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = build_report(args)
    except AuditError as exc:
        report = build_error_report(args, str(exc))

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
    return 0 if report.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Clone a fresh release checkout and run the consumer-facing local-first audit. "
            "This proves the published source can be used without provider URLs or third-party paid accounts."
        )
    )
    parser.add_argument(
        "--source",
        default=str(REPO_ROOT),
        help="Git source to clone. Defaults to this local repository to avoid network requirements.",
    )
    parser.add_argument(
        "--ref",
        default=DEFAULT_REF,
        help="Git ref to audit, usually a release tag.",
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for audit worktrees and evidence.",
    )
    parser.add_argument("--run-id", help="Optional stable run id.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use quick consumer self-check and skip fixture-backed release runs.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout passed to lightweight readiness subprocess checks.",
    )
    parser.add_argument(
        "--keep-worktree",
        action="store_true",
        help="Keep the cloned checkout after the audit for manual inspection.",
    )
    parser.add_argument("--output-json", help="Optional path to write the audit JSON report.")
    parser.add_argument("--output-markdown", help="Optional path to write the audit Markdown report.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"post-release-consumer-audit-{uuid.uuid4().hex[:8]}"
    audit_dir = state_root / run_id
    evidence_dir = audit_dir / "evidence"
    checkout_dir = audit_dir / "checkout"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if checkout_dir.exists():
        raise AuditError(f"Checkout directory already exists: {checkout_dir}")

    clone_result = run_command(
        ["git", "clone", "--no-hardlinks", args.source, str(checkout_dir)],
        cwd=REPO_ROOT,
        timeout_seconds=max(120, args.timeout_seconds * 4),
    )
    if clone_result["returncode"] != 0:
        raise AuditError(f"git clone failed: {clone_result.get('stderr') or clone_result.get('stdout')}")

    checkout_result = run_command(
        ["git", "checkout", "--detach", args.ref],
        cwd=checkout_dir,
        timeout_seconds=max(60, args.timeout_seconds * 2),
    )
    if checkout_result["returncode"] != 0:
        raise AuditError(f"git checkout {args.ref} failed: {checkout_result.get('stderr') or checkout_result.get('stdout')}")

    metadata = collect_checkout_metadata(checkout_dir, args.ref)
    required_sources = check_required_sources(checkout_dir)

    self_check_command = [
        sys.executable,
        ".codex/skills/room-skill/runtime/agent_consumer_self_check.py",
        "--state-root",
        str(evidence_dir / "agent-consumer-self-check"),
        "--output-json",
        str(evidence_dir / "agent-consumer-self-check.json"),
        "--output-markdown",
        str(evidence_dir / "agent-consumer-self-check.md"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.quick:
        self_check_command.append("--quick")
    consumer_self_check = run_json_command(
        self_check_command,
        cwd=checkout_dir,
        timeout_seconds=max(420, args.timeout_seconds * 14),
    )

    claude_skills = run_json_command(
        [sys.executable, ".claude/scripts/validate_project_skills.py"],
        cwd=checkout_dir,
        timeout_seconds=max(60, args.timeout_seconds * 2),
    )

    readiness_command = [
        sys.executable,
        ".codex/skills/room-skill/runtime/release_readiness_check.py",
        "--strict-git-clean",
        "--state-root",
        str(evidence_dir / "release-readiness"),
        "--output-json",
        str(evidence_dir / "release-readiness.json"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if not args.quick:
        readiness_command.append("--include-fixture-runs")
    release_readiness = run_json_command(
        readiness_command,
        cwd=checkout_dir,
        timeout_seconds=max(420, args.timeout_seconds * 14),
    )

    summary = build_summary(
        required_sources=required_sources,
        consumer_self_check=consumer_self_check,
        claude_skills=claude_skills,
        release_readiness=release_readiness,
        quick=args.quick,
    )
    ok = (
        clone_result["returncode"] == 0
        and checkout_result["returncode"] == 0
        and required_sources["ok"]
        and consumer_self_check.get("ok") is True
        and claude_skills.get("ok") is True
        and release_readiness.get("ok") is True
        and not summary["p0_blockers"]
    )

    if ok and not args.keep_worktree:
        shutil.rmtree(checkout_dir)
        checkout_state = "removed_after_success"
    else:
        checkout_state = "kept_for_inspection"

    report = {
        "ok": ok,
        "action": "post-release-consumer-audit",
        "generated_at": utc_now_iso(),
        "source": args.source,
        "ref": args.ref,
        "run_id": run_id,
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "audit_dir": str(audit_dir),
        "checkout_dir": str(checkout_dir),
        "checkout_state": checkout_state,
        "metadata": metadata,
        "summary": summary,
        "checks": {
            "git_clone": clone_result,
            "git_checkout": checkout_result,
            "required_sources": required_sources,
            "agent_consumer_self_check": summarize_json_command(consumer_self_check),
            "claude_project_skills": summarize_json_command(claude_skills),
            "release_readiness": summarize_json_command(release_readiness),
        },
        "interpretation": {
            "provider_url_required": False,
            "third_party_paid_account_required": False,
            "fresh_checkout_rule": "The audit runs from a cloned checkout of the requested ref, not the current working tree.",
            "claim_boundary": (
                "A passing audit proves the release is usable for the checked-in local-first consumer path. "
                "It does not prove uninstalled third-party agent hosts or real provider-live execution."
            ),
        },
        "artifacts": {
            "json": str(audit_dir / "post-release-consumer-audit.json"),
            "markdown": str(audit_dir / "post-release-consumer-audit.md"),
            "evidence_dir": str(evidence_dir),
            "agent_consumer_self_check_json": str(evidence_dir / "agent-consumer-self-check.json"),
            "agent_consumer_self_check_markdown": str(evidence_dir / "agent-consumer-self-check.md"),
            "release_readiness_json": str(evidence_dir / "release-readiness.json"),
        },
    }
    return report


def build_error_report(args: argparse.Namespace, error: str) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"post-release-consumer-audit-{uuid.uuid4().hex[:8]}"
    audit_dir = state_root / run_id
    audit_dir.mkdir(parents=True, exist_ok=True)
    return {
        "ok": False,
        "action": "post-release-consumer-audit",
        "generated_at": utc_now_iso(),
        "source": args.source,
        "ref": args.ref,
        "run_id": run_id,
        "repo_root": str(REPO_ROOT),
        "state_root": str(state_root),
        "audit_dir": str(audit_dir),
        "error": error,
        "artifacts": {
            "json": str(audit_dir / "post-release-consumer-audit.json"),
            "markdown": str(audit_dir / "post-release-consumer-audit.md"),
        },
    }


def collect_checkout_metadata(checkout_dir: Path, requested_ref: str) -> dict[str, Any]:
    return {
        "requested_ref": requested_ref,
        "head": command_stdout(["git", "rev-parse", "HEAD"], checkout_dir),
        "status": command_stdout(["git", "status", "-sb"], checkout_dir),
        "latest_log": command_stdout(["git", "log", "--oneline", "-3"], checkout_dir).splitlines(),
        "tag_describe": command_stdout(["git", "describe", "--tags", "--exact-match", "HEAD"], checkout_dir),
        "remote": command_stdout(["git", "remote", "-v"], checkout_dir).splitlines(),
    }


def check_required_sources(checkout_dir: Path) -> dict[str, Any]:
    required = [
        "AGENTS.md",
        "README.md",
        "LAUNCH.md",
        "docs",
        "prompts",
        "examples",
        ".codex/skills/room-skill",
        ".codex/skills/debate-roundtable-skill",
        ".claude/skills",
    ]
    entries = [{"path": path, "exists": (checkout_dir / path).exists()} for path in required]
    missing = [entry["path"] for entry in entries if not entry["exists"]]
    return {"ok": not missing, "entries": entries, "missing": missing}


def build_summary(
    *,
    required_sources: dict[str, Any],
    consumer_self_check: dict[str, Any],
    claude_skills: dict[str, Any],
    release_readiness: dict[str, Any],
    quick: bool,
) -> dict[str, Any]:
    readiness_payload = payload_dict(release_readiness)
    consumer_payload = payload_dict(consumer_self_check)
    consumer_summary = consumer_payload.get("summary", {}) if isinstance(consumer_payload.get("summary"), dict) else {}
    release_scope = readiness_payload.get("release_scope", {}) if isinstance(readiness_payload.get("release_scope"), dict) else {}
    p0_blockers = readiness_payload.get("p0_blockers", [])
    p0_blockers = p0_blockers if isinstance(p0_blockers, list) else ["p0_blocker_parse_error"]
    non_blocking_gaps = readiness_payload.get("non_blocking_gaps", [])
    non_blocking_gap_ids = [
        gap.get("id")
        for gap in non_blocking_gaps
        if isinstance(gap, dict) and gap.get("id")
    ]
    host_summary = consumer_summary.get("host_summary", {}) if isinstance(consumer_summary, dict) else {}
    provider_summary = consumer_summary.get("provider_summary", {}) if isinstance(consumer_summary, dict) else {}

    return {
        "consumer_path_ready": (
            required_sources.get("ok") is True
            and consumer_self_check.get("ok") is True
            and claude_skills.get("ok") is True
            and release_readiness.get("ok") is True
            and not p0_blockers
        ),
        "ship_decision": release_scope.get("ship_decision"),
        "quick_mode": quick,
        "required_sources_ok": required_sources.get("ok") is True,
        "agent_consumer_self_check_ok": consumer_self_check.get("ok") is True,
        "claude_project_skills_ok": claude_skills.get("ok") is True,
        "release_readiness_ok": release_readiness.get("ok") is True,
        "p0_blockers": p0_blockers,
        "non_blocking_gap_ids": non_blocking_gap_ids,
        "live_passed_hosts": host_summary.get("live_passed_hosts", []),
        "missing_hosts": host_summary.get("missing_hosts", []),
        "provider_live_ready": provider_summary.get("ready_for_live_run"),
        "provider_url_required": False,
    }


def run_json_command(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    result = run_command(command, cwd=cwd, timeout_seconds=timeout_seconds)
    payload: dict[str, Any] | None = None
    json_parse_ok = False
    if result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
            json_parse_ok = isinstance(payload, dict)
        except json.JSONDecodeError:
            payload = None
    return {
        **result,
        "json_parse_ok": json_parse_ok,
        "ok": result["returncode"] == 0 and json_parse_ok and bool(payload.get("ok")) if isinstance(payload, dict) else False,
        "payload": payload,
    }


def run_command(command: list[str], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"Timed out after {timeout_seconds} seconds.",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }


def command_stdout(command: list[str], cwd: Path) -> str:
    result = run_command(command, cwd=cwd, timeout_seconds=30)
    return result["stdout"].strip() if result["returncode"] == 0 else ""


def summarize_json_command(result: dict[str, Any]) -> dict[str, Any]:
    payload = payload_dict(result)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else None
    return {
        "command": result.get("command"),
        "cwd": result.get("cwd"),
        "returncode": result.get("returncode"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ok": result.get("ok"),
        "timed_out": result.get("timed_out"),
        "summary": summary,
        "p0_blockers": payload.get("p0_blockers") if isinstance(payload, dict) else None,
        "artifacts": payload.get("artifacts") if isinstance(payload.get("artifacts"), dict) else None,
    }


def payload_dict(result: dict[str, Any]) -> dict[str, Any]:
    return result.get("payload") if isinstance(result.get("payload"), dict) else {}


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    checks = report.get("checks", {}) if isinstance(report.get("checks"), dict) else {}
    lines = [
        "# Post-Release Consumer Audit",
        "",
        f"- Result: `{'PASS' if report.get('ok') else 'FAIL'}`",
        f"- Source: `{report.get('source')}`",
        f"- Ref: `{report.get('ref')}`",
        f"- Checkout state: `{report.get('checkout_state', 'n/a')}`",
        f"- Head: `{report.get('metadata', {}).get('head', 'n/a')}`",
        f"- Tag describe: `{report.get('metadata', {}).get('tag_describe', 'n/a')}`",
        "",
        "## Summary",
        "",
        f"- Consumer path ready: `{summary.get('consumer_path_ready')}`",
        f"- Ship decision: `{summary.get('ship_decision')}`",
        f"- P0 blockers: `{summary.get('p0_blockers')}`",
        f"- Non-blocking gaps: `{summary.get('non_blocking_gap_ids')}`",
        f"- Live-passed hosts: `{summary.get('live_passed_hosts')}`",
        f"- Missing hosts: `{summary.get('missing_hosts')}`",
        f"- Provider live ready: `{summary.get('provider_live_ready')}`",
        f"- Provider URL required for this audit: `{summary.get('provider_url_required')}`",
        "",
        "## Checks",
        "",
    ]
    for name, check in checks.items():
        if not isinstance(check, dict):
            continue
        ok = check.get("ok")
        if ok is None and "returncode" in check:
            ok = check.get("returncode") == 0
        lines.append(f"- `{name}`: `{'PASS' if ok else 'FAIL'}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing audit proves the release ref works from a fresh cloned checkout for the local-first consumer path.",
            "It does not prove real provider-live support or live support for local agent CLIs that are not installed and validated on this machine.",
            "",
        ]
    )
    if report.get("error"):
        lines.extend(["## Error", "", f"```text\n{report['error']}\n```", ""])
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
