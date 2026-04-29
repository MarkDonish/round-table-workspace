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
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-release-readiness"
CLAUDE_CODE_LIVE_EVIDENCE_PATTERN = "CLAUDE_CODE_HOST_LIVE_VALIDATION_*.md"

REQUIRED_SOURCE_TRUTH: list[tuple[str, str]] = [
    ("file", "AGENTS.md"),
    ("file", "LAUNCH.md"),
    ("file", "README.md"),
    ("dir", "docs"),
    ("dir", "prompts"),
    ("dir", "examples"),
    ("dir", "schemas"),
    ("dir", "roundtable_core"),
    ("dir", "scripts"),
    ("dir", "skills_src"),
    ("dir", "evals"),
    ("dir", ".codex/skills/room-skill"),
    ("dir", ".codex/skills/debate-roundtable-skill"),
    ("dir", ".claude/skills"),
]

REQUIRED_RUNTIME_FILES: list[str] = [
    ".codex/skills/room-skill/runtime/room_runtime.py",
    ".codex/skills/room-skill/runtime/room_e2e_validation.py",
    ".codex/skills/room-skill/runtime/room_debate_e2e_validation.py",
    ".codex/skills/room-skill/runtime/local_codex_executor.py",
    ".codex/skills/room-skill/runtime/local_codex_regression.py",
    ".codex/skills/room-skill/runtime/generic_agent_executor.py",
    ".codex/skills/room-skill/runtime/generic_agent_adapter_validation.py",
    ".codex/skills/room-skill/runtime/generic_agent_json_wrapper.py",
    ".codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py",
    ".codex/skills/room-skill/runtime/opencode_agent_wrapper.py",
    ".codex/skills/room-skill/runtime/agent_host_inventory.py",
    ".codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py",
    ".codex/skills/room-skill/runtime/live_lane_evidence_report.py",
    ".codex/skills/room-skill/runtime/host_recipes_consistency_check.py",
    ".codex/skills/room-skill/runtime/agent_consumer_self_check.py",
    ".codex/skills/room-skill/runtime/post_release_consumer_audit.py",
    ".codex/skills/room-skill/runtime/chat_completions_readiness.py",
    ".codex/skills/room-skill/runtime/chat_completions_regression.py",
    ".codex/skills/room-skill/runtime/chat_completions_live_validation.py",
    ".codex/skills/room-skill/runtime/release_readiness_check.py",
    ".codex/skills/room-skill/runtime/release_candidate_report.py",
    ".codex/skills/room-skill/runtime/source_boundary_audit.py",
    ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py",
    ".codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py",
    ".codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py",
    ".claude/scripts/validate_project_skills.py",
]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_release_report(args)
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report["p0_blockers"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate non-secret release readiness checks for the round-table repository. "
            "This command does not call real provider endpoints and does not require third-party agent accounts."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for optional validation evidence. Defaults outside the repository.",
    )
    parser.add_argument("--output-json", help="Optional path to persist the readiness report.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout for lightweight subprocess checks.",
    )
    parser.add_argument(
        "--include-fixture-runs",
        action="store_true",
        help="Also run the generic fixture-backed /room -> /debate adapter validation.",
    )
    parser.add_argument(
        "--strict-git-clean",
        action="store_true",
        help="Treat a dirty working tree as a P0 release blocker.",
    )
    return parser


def build_release_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)

    source_truth = check_source_truth()
    runtime_files = check_runtime_files()
    git_state = check_git_state()
    claude_skills = run_json_command(
        [sys.executable, ".claude/scripts/validate_project_skills.py"],
        timeout_seconds=args.timeout_seconds,
    )
    agent_inventory = run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/agent_host_inventory.py",
            "--timeout-seconds",
            str(args.timeout_seconds),
        ],
        timeout_seconds=args.timeout_seconds + 5,
    )
    host_validation_matrix = run_json_command(
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
    provider_readiness = run_json_command(
        [sys.executable, ".codex/skills/room-skill/runtime/chat_completions_readiness.py"],
        timeout_seconds=args.timeout_seconds,
    )
    live_lane_evidence = run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/live_lane_evidence_report.py",
            "--timeout-seconds",
            str(args.timeout_seconds),
            "--state-root",
            str(state_root / "live-lane-evidence"),
        ],
        timeout_seconds=args.timeout_seconds + 20,
    )
    host_recipes_consistency = run_json_command(
        [sys.executable, ".codex/skills/room-skill/runtime/host_recipes_consistency_check.py"],
        timeout_seconds=args.timeout_seconds,
    )

    fixture_validation = None
    wrapper_validation = None
    if args.include_fixture_runs:
        fixture_validation = run_json_command(
            [
                sys.executable,
                ".codex/skills/room-skill/runtime/generic_agent_adapter_validation.py",
                "--state-root",
                str(state_root / "generic-agent-adapter-validation"),
            ],
            timeout_seconds=max(180, args.timeout_seconds),
        )
        wrapper_validation = run_json_command(
            [
                sys.executable,
                ".codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py",
                "--state-root",
                str(state_root / "generic-agent-json-wrapper-validation"),
            ],
            timeout_seconds=max(240, args.timeout_seconds),
        )

    checked_in_host_live_evidence = collect_checked_in_host_live_evidence()
    p0_blockers = build_p0_blockers(
        source_truth=source_truth,
        runtime_files=runtime_files,
        git_state=git_state,
        claude_skills=claude_skills,
        agent_inventory=agent_inventory,
        host_validation_matrix=host_validation_matrix,
        provider_readiness=provider_readiness,
        live_lane_evidence=live_lane_evidence,
        host_recipes_consistency=host_recipes_consistency,
        fixture_validation=fixture_validation,
        wrapper_validation=wrapper_validation,
        strict_git_clean=args.strict_git_clean,
    )
    non_blocking_gaps = build_non_blocking_gaps(
        agent_inventory=agent_inventory,
        host_validation_matrix=host_validation_matrix,
        provider_readiness=provider_readiness,
        fixture_validation=fixture_validation,
        include_fixture_runs=args.include_fixture_runs,
        checked_in_host_live_evidence=checked_in_host_live_evidence,
    )

    pass_criteria = {
        "source_truth_present": source_truth["ok"],
        "runtime_entrypoints_present": runtime_files["ok"],
        "claude_project_skill_structure_passed": command_ok(claude_skills),
        "agent_host_inventory_tooling_passed": command_ok(agent_inventory),
        "local_agent_host_validation_matrix_tooling_passed": command_ok(host_validation_matrix),
        "provider_readiness_tooling_passed": command_ok(provider_readiness),
        "live_lane_evidence_report_tooling_passed": command_ok(live_lane_evidence),
        "host_recipes_consistency_passed": command_ok(host_recipes_consistency),
        "fixture_adapter_validation_passed_or_not_requested": (
            True if fixture_validation is None else command_ok(fixture_validation)
        ),
        "json_wrapper_validation_passed_or_not_requested": (
            True if wrapper_validation is None else command_ok(wrapper_validation)
        ),
        "no_p0_blockers": not p0_blockers,
    }

    ready_to_claim = [
        "Codex local mainline release scope",
        "checked-in /room and /debate protocol/runtime source",
        "Claude Code project-skill discovery structure",
        (
            "generic local agent adapter contract with fixture-backed validation"
            if args.include_fixture_runs
            else "generic local agent adapter contract source"
        ),
        "third-party local agent JSON wrapper tooling and recipes",
        "OpenCode local-agent wrapper tooling without host-live claim",
        "third-party local agent validation matrix/report tooling",
        "host/provider live-lane evidence report tooling",
        "third-party local agent host recipe consistency tooling",
        "clone-friendly agent consumer self-check tooling",
        "post-release fresh-checkout consumer audit tooling",
        "GitHub Release publication status checker and workflow source",
        "clone-friendly launch quickstart",
        "provider fallback readiness tooling and mock regression source",
        "source-truth boundary audit tooling",
    ]
    if any(item["host_id"] == "claude_code" for item in checked_in_host_live_evidence):
        ready_to_claim.append("default Claude Code host-live support on the validated Mac account")

    not_claimed = [
        (
            "unvalidated Claude Code machines/accounts before claude_code_live_validation.py passes there"
            if checked_in_host_live_evidence
            else "real Claude Code live execution when account auth is unavailable"
        ),
        "real third-party local agent live execution before its CLI contract validation passes",
        "real Chat Completions-compatible provider live execution before .env.room and .env.debate are ready",
        "all possible agent hosts being production-stable without per-host live validation",
    ]

    return {
        "ok": True,
        "action": "release-readiness-check",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "release_scope": {
            "ship_decision": "blocked" if p0_blockers else "ready_for_codex_local_mainline_scope",
            "ready_to_claim": ready_to_claim,
            "not_claimed": not_claimed,
        },
        "p0_blockers": p0_blockers,
        "non_blocking_gaps": non_blocking_gaps,
        "pass_criteria": pass_criteria,
        "checked_in_host_live_evidence": checked_in_host_live_evidence,
        "checks": {
            "source_truth": source_truth,
            "runtime_files": runtime_files,
            "git_state": git_state,
            "claude_project_skills": summarize_command(claude_skills),
            "agent_host_inventory": summarize_command(agent_inventory),
            "local_agent_host_validation_matrix": summarize_command(host_validation_matrix),
            "provider_readiness": summarize_command(provider_readiness),
            "live_lane_evidence_report": summarize_command(live_lane_evidence),
            "host_recipes_consistency": summarize_command(host_recipes_consistency),
            "generic_fixture_validation": summarize_command(fixture_validation) if fixture_validation else None,
            "json_wrapper_validation": summarize_command(wrapper_validation) if wrapper_validation else None,
        },
        "manual_release_validations": [
            "python3 .codex/skills/room-skill/runtime/local_codex_regression.py --state-root /tmp/round-table-local-codex-regression",
            "python3 .codex/skills/room-skill/runtime/chat_completions_regression.py --state-root /tmp/round-table-chat-completions-regression",
            "python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py --state-root /tmp/round-table-generic-agent-adapter-validation",
            "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py --state-root /tmp/round-table-generic-agent-json-wrapper-validation",
            "python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py --state-root /tmp/round-table-local-agent-host-validation-matrix",
            "python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py --state-root /tmp/round-table-live-lane-evidence",
            "python3 .codex/skills/room-skill/runtime/host_recipes_consistency_check.py --output-json /tmp/round-table-host-recipes-consistency.json",
            "python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py --state-root /tmp/round-table-agent-consumer-self-check",
            "python3 .codex/skills/room-skill/runtime/source_boundary_audit.py --output-json /tmp/round-table-source-boundary-audit.json",
            "python3 .codex/skills/room-skill/runtime/release_candidate_report.py --include-fixture-runs --strict-git-clean --state-root /tmp/round-table-release-candidate",
        ],
    }


def check_source_truth() -> dict[str, Any]:
    entries = []
    for kind, rel_path in REQUIRED_SOURCE_TRUTH:
        path = REPO_ROOT / rel_path
        exists = path.is_file() if kind == "file" else path.is_dir()
        entries.append({"kind": kind, "path": rel_path, "exists": exists})
    return {
        "ok": all(item["exists"] for item in entries),
        "entries": entries,
        "missing": [item["path"] for item in entries if not item["exists"]],
    }


def check_runtime_files() -> dict[str, Any]:
    entries = [{"path": rel_path, "exists": (REPO_ROOT / rel_path).is_file()} for rel_path in REQUIRED_RUNTIME_FILES]
    return {
        "ok": all(item["exists"] for item in entries),
        "entries": entries,
        "missing": [item["path"] for item in entries if not item["exists"]],
    }


def collect_checked_in_host_live_evidence() -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    report = latest_claude_code_live_evidence_report()
    if report is None:
        return evidence
    text = report.read_text(encoding="utf-8")
    if (
        "Claimable as default Claude Code host live: `true`" in text
        and "Support claim: `real_claude_code_host_live_validated`" in text
        and "claude_code_live_validation.py" in text
    ):
        evidence.append(
            {
                "host_id": "claude_code",
                "scope": "default_claude_code_host_live_on_validated_mac_account",
                "report": str(report.relative_to(REPO_ROOT)),
            }
        )
    return evidence


def latest_claude_code_live_evidence_report() -> Path | None:
    reports_dir = REPO_ROOT / "reports"
    reports = sorted(reports_dir.glob(CLAUDE_CODE_LIVE_EVIDENCE_PATTERN), reverse=True)
    return reports[0] if reports else None


def check_git_state() -> dict[str, Any]:
    branch = run_command(["git", "status", "-sb"], timeout_seconds=10)
    porcelain = run_command(["git", "status", "--porcelain"], timeout_seconds=10)
    head = run_command(["git", "log", "--oneline", "-1"], timeout_seconds=10)
    remote = run_command(["git", "remote", "-v"], timeout_seconds=10)
    dirty_lines = [line for line in porcelain["stdout"].splitlines() if line.strip()]
    return {
        "ok": branch["returncode"] == 0 and porcelain["returncode"] == 0,
        "branch": branch["stdout"],
        "head": head["stdout"],
        "remote": remote["stdout"],
        "dirty": bool(dirty_lines),
        "dirty_entries": dirty_lines,
    }


def build_p0_blockers(
    *,
    source_truth: dict[str, Any],
    runtime_files: dict[str, Any],
    git_state: dict[str, Any],
    claude_skills: dict[str, Any],
    agent_inventory: dict[str, Any],
    host_validation_matrix: dict[str, Any],
    provider_readiness: dict[str, Any],
    live_lane_evidence: dict[str, Any],
    host_recipes_consistency: dict[str, Any],
    fixture_validation: dict[str, Any] | None,
    wrapper_validation: dict[str, Any] | None,
    strict_git_clean: bool,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if not source_truth["ok"]:
        blockers.append({"id": "source_truth_missing", "detail": source_truth["missing"]})
    if not runtime_files["ok"]:
        blockers.append({"id": "runtime_entrypoint_missing", "detail": runtime_files["missing"]})
    if not command_ok(claude_skills):
        blockers.append({"id": "claude_project_skill_structure_failed", "detail": command_failure_detail(claude_skills)})
    if not command_ok(agent_inventory):
        blockers.append({"id": "agent_host_inventory_tooling_failed", "detail": command_failure_detail(agent_inventory)})
    if not command_ok(host_validation_matrix):
        blockers.append(
            {
                "id": "local_agent_host_validation_matrix_tooling_failed",
                "detail": command_failure_detail(host_validation_matrix),
            }
        )
    if not command_ok(provider_readiness):
        blockers.append({"id": "provider_readiness_tooling_failed", "detail": command_failure_detail(provider_readiness)})
    if not command_ok(live_lane_evidence):
        blockers.append(
            {
                "id": "live_lane_evidence_report_tooling_failed",
                "detail": command_failure_detail(live_lane_evidence),
            }
        )
    if not command_ok(host_recipes_consistency):
        blockers.append(
            {
                "id": "host_recipes_consistency_failed",
                "detail": command_failure_detail(host_recipes_consistency),
            }
        )
    if fixture_validation is not None and not command_ok(fixture_validation):
        blockers.append({"id": "generic_fixture_adapter_validation_failed", "detail": command_failure_detail(fixture_validation)})
    if wrapper_validation is not None and not command_ok(wrapper_validation):
        blockers.append({"id": "generic_json_wrapper_validation_failed", "detail": command_failure_detail(wrapper_validation)})
    if strict_git_clean and git_state.get("dirty"):
        blockers.append({"id": "working_tree_dirty", "detail": git_state.get("dirty_entries", [])})
    return blockers


def build_non_blocking_gaps(
    *,
    agent_inventory: dict[str, Any],
    host_validation_matrix: dict[str, Any],
    provider_readiness: dict[str, Any],
    fixture_validation: dict[str, Any] | None,
    include_fixture_runs: bool,
    checked_in_host_live_evidence: list[dict[str, str]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    provider_payload = provider_readiness.get("json") or {}
    provider_criteria = provider_payload.get("pass_criteria", {})
    if provider_criteria.get("ready_for_live_run") is not True:
        gaps.append(
            {
                "id": "provider_live_not_ready",
                "why_not_p0": "provider lane is fallback/regression, not the local mainline",
                "detail": provider_payload.get("next_action") or command_failure_detail(provider_readiness),
            }
        )

    inventory_payload = agent_inventory.get("json") or {}
    summary = inventory_payload.get("summary", {})
    blocked_hosts = summary.get("blocked_hosts") or []
    missing_hosts = summary.get("missing_hosts") or []
    if blocked_hosts:
        gaps.append(
            {
                "id": "some_local_agent_hosts_blocked",
                "why_not_p0": "third-party host live validation is per-host evidence, not required for Codex mainline launch",
                "detail": blocked_hosts,
            }
        )
    if missing_hosts:
        gaps.append(
            {
                "id": "some_local_agent_hosts_missing",
                "why_not_p0": "missing third-party CLIs only block those host recipes",
                "detail": missing_hosts,
            }
        )

    matrix_payload = host_validation_matrix.get("json") or {}
    matrix_summary = matrix_payload.get("summary", {})
    matrix_live_hosts = set(matrix_summary.get("live_passed_hosts") or [])
    checked_live_hosts = {item["host_id"] for item in checked_in_host_live_evidence}
    live_passed_hosts = matrix_live_hosts | checked_live_hosts
    if command_ok(host_validation_matrix) and not live_passed_hosts:
        gaps.append(
            {
                "id": "no_real_third_party_agent_host_live_passed",
                "why_not_p0": "the current launch scope is Codex local mainline; host-live support is claimed per host only",
                "detail": "Run local_agent_host_validation_matrix.py with --run-live-ready or a specific --agent-command before claiming a real third-party host.",
            }
        )

    if not include_fixture_runs:
        gaps.append(
            {
                "id": "fixture_adapter_validation_not_run_in_this_check",
                "why_not_p0": "the checked-in command exists; run with --include-fixture-runs for stronger release evidence",
                "detail": "python3 .codex/skills/room-skill/runtime/release_readiness_check.py --include-fixture-runs",
            }
        )
    elif fixture_validation is not None and command_ok(fixture_validation):
        if live_passed_hosts:
            gaps.append(
                {
                    "id": "additional_third_party_agent_live_validation_pending",
                    "why_not_p0": "host-live support is claimed per host; one live-passed host does not prove every agent CLI",
                    "detail": "Claude Code has checked-in machine/account-scoped evidence; Gemini/OpenCode/Aider/Goose/Cursor Agent still need their own live validation before being claimed.",
                }
            )
        else:
            gaps.append(
                {
                    "id": "real_third_party_agent_live_validation_pending",
                    "why_not_p0": "fixture validation proves adapter contract, not a specific external host",
                    "detail": "Run generic_agent_adapter_validation.py with each real agent command before claiming host-live support.",
                }
            )
    return gaps


def run_json_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    result = run_command(command, timeout_seconds=timeout_seconds)
    payload = extract_json(result["stdout"])
    result["json"] = payload
    result["json_parse_ok"] = isinstance(payload, dict)
    return result


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


def extract_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def command_ok(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    payload = result.get("json")
    if isinstance(payload, dict) and payload.get("ok") is not None:
        return result.get("returncode") == 0 and payload.get("ok") is True
    return result.get("returncode") == 0


def command_failure_detail(result: dict[str, Any] | None) -> Any:
    if not result:
        return "command_not_run"
    payload = result.get("json")
    if isinstance(payload, dict):
        if payload.get("error"):
            return payload["error"]
        if payload.get("pass_criteria"):
            return payload["pass_criteria"]
    return {
        "returncode": result.get("returncode"),
        "stderr": result.get("stderr"),
        "timed_out": result.get("timed_out", False),
    }


def summarize_command(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result:
        return None
    payload = result.get("json")
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ok": command_ok(result),
        "payload": payload if isinstance(payload, dict) else None,
        "stderr": result.get("stderr"),
        "timed_out": result.get("timed_out", False),
    }


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
