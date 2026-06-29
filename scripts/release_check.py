#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from roundtable_core.runtime.paths import assert_no_symlink_components, utc_timestamp
from secret_redaction import redact_sensitive_value


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Round Table Workspace release checks.")
    parser.add_argument(
        "--state-root",
        default=str(Path(tempfile.gettempdir()) / "round-table-release-check" / utc_timestamp()),
    )
    parser.add_argument("--include-fixtures", action="store_true")
    parser.add_argument("--strict-git-clean", action="store_true")
    parser.add_argument(
        "--skip-claim-dashboard",
        action="store_true",
        help="Internal use: avoid recursive dashboard generation while claim_boundary_dashboard.py consumes release-check.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    report = build_report(args)
    state_root = Path(report["state_root"])
    write_json(state_root / "release-check.json", report)
    write_text(state_root / "release-check.md", render_markdown(report))
    print(json.dumps(redact_sensitive_value(report), ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    raw_state_root = Path(args.state_root).expanduser()
    assert_no_symlink_components(raw_state_root, include_leaf=True)
    state_root = raw_state_root.resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}
    source_truth_command = [
        sys.executable,
        "scripts/check_source_truth_consistency.py",
        "--output-json",
        str(state_root / "source-truth-consistency.json"),
        "--output-markdown",
        str(state_root / "source-truth-consistency.md"),
    ]
    if args.skip_claim_dashboard:
        source_truth_command.append("--skip-claim-dashboard-freshness")
    checks["source_truth_consistency"] = run_json(source_truth_command, timeout=args.timeout_seconds + 10)
    checks["agent_registry_sync"] = run_json(
        [
            sys.executable,
            "scripts/check_agent_registry_sync.py",
            "--output-json",
            str(state_root / "agent-registry-sync.json"),
            "--output-markdown",
            str(state_root / "agent-registry-sync.md"),
        ],
        timeout=args.timeout_seconds + 10,
    )
    checks["skill_drift"] = run_json(
        [
            sys.executable,
            "scripts/check_skill_drift.py",
            "--output-json",
            str(state_root / "skill-drift.json"),
            "--output-markdown",
            str(state_root / "skill-drift.md"),
        ],
        timeout=args.timeout_seconds + 10,
    )
    checks["agent_factory"] = run_agent_factory_checks(args.timeout_seconds)
    checks["public_cli_surface"] = run_public_cli_surface_checks(args.timeout_seconds)
    checks["schema_validation"] = run_schema_validations(args.timeout_seconds)
    checks["runtime_projection_validation"] = run_runtime_projection_validations(state_root, args.timeout_seconds)
    checks["regression_fixtures"] = run_json(
        [
            sys.executable,
            "scripts/run_regression_fixtures.py",
            "--output-json",
            str(state_root / "regression-fixtures.json"),
        ],
        timeout=args.timeout_seconds + 10,
    )
    checks["negative_fixtures"] = run_json(
        [
            sys.executable,
            "scripts/run_negative_fixtures.py",
            "--output-json",
            str(state_root / "negative-fixtures.json"),
        ],
        timeout=args.timeout_seconds + 10,
    )
    checks["live_lane_evidence"] = run_json(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/live_lane_evidence_report.py",
            "--state-root",
            str(state_root / "live-lane-evidence"),
            "--timeout-seconds",
            str(args.timeout_seconds),
        ],
        timeout=args.timeout_seconds + 30,
    )
    if args.skip_claim_dashboard:
        checks["claim_boundary_dashboard"] = {
            "ok": True,
            "skipped": True,
            "reason": "skipped to avoid recursive release-check -> dashboard -> release-check execution",
        }
    else:
        claim_dashboard_command = [
            sys.executable,
            "scripts/claim_boundary_dashboard.py",
            "--state-root",
            str(state_root / "claim-boundary-dashboard-state"),
            "--output-json",
            str(state_root / "claim-boundary-dashboard.json"),
            "--output-markdown",
            str(state_root / "claim-boundary-dashboard.md"),
            "--timeout-seconds",
            str(args.timeout_seconds),
        ]
        if args.strict_git_clean:
            claim_dashboard_command.append("--strict-git-clean")
        checks["claim_boundary_dashboard"] = run_json(claim_dashboard_command, timeout=args.timeout_seconds + 100)
    checks["github_release_publication"] = run_json(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/github_release_publication_check.py",
            "--state-root",
            str(state_root / "github-release-publication"),
            "--output-json",
            str(state_root / "github-release-publication.json"),
            "--output-markdown",
            str(state_root / "github-release-publication.md"),
            "--timeout-seconds",
            str(args.timeout_seconds),
        ],
        timeout=args.timeout_seconds + 60,
    )
    checks["legacy_release_readiness"] = run_legacy_release_readiness(args, state_root=state_root)
    if args.include_fixtures:
        checks["decision_quality_evals"] = run_json(
            [
                sys.executable,
                "evals/decision_quality/run_decision_evals.py",
                "--output-json",
                str(state_root / "decision-quality-eval.json"),
                "--output-markdown",
                str(state_root / "decision-quality-eval.md"),
            ],
            timeout=args.timeout_seconds + 10,
        )
    else:
        checks["decision_quality_evals"] = {"ok": True, "skipped": True, "reason": "pass --include-fixtures to run"}
    if args.strict_git_clean:
        checks["git_clean"] = run_git_clean()
    else:
        checks["git_clean"] = {"ok": True, "skipped": True, "reason": "pass --strict-git-clean to enforce"}

    blockers = [name for name, check in checks.items() if not check.get("ok")]
    warnings = collect_check_warnings(checks)
    return {
        "ok": not blockers,
        "action": "release-check",
        "state_root": str(state_root),
        "include_fixtures": args.include_fixtures,
        "strict_git_clean": args.strict_git_clean,
        "skip_claim_dashboard": args.skip_claim_dashboard,
        "checks": checks,
        "release_blockers": blockers,
        "release_warnings": warnings,
        "claim_boundary": [
            "release-check aggregates local-first validation only.",
            "It does not convert fixture/mock/config readiness into live support.",
        ],
        "artifacts": {
            "json": str(state_root / "release-check.json"),
            "markdown": str(state_root / "release-check.md"),
        },
    }


def run_schema_validations(timeout: int) -> dict[str, Any]:
    commands = [
        ["./rtw", "validate", "--schema", "schemas/room-session.schema.json", "--fixture", "tests/fixtures/room-session.valid.json"],
        ["./rtw", "validate", "--schema", "schemas/debate-session.schema.json", "--fixture", "examples/fixtures/debate-session.valid.json"],
        ["./rtw", "validate", "--schema", "schemas/debate-result.schema.json", "--fixture", "examples/fixtures/debate-result.valid.json"],
        ["./rtw", "validate", "--schema", "schemas/debate-result.schema.json", "--fixture", "examples/fixtures/debate-result.allow.json"],
        ["./rtw", "validate", "--schema", "schemas/debate-result.schema.json", "--fixture", "examples/fixtures/debate-result.reject.json"],
        ["./rtw", "validate", "--schema", "schemas/debate-result.schema.json", "--fixture", "examples/fixtures/debate-result.follow-up-required.json"],
        ["./rtw", "validate", "--schema", "schemas/room-to-debate-handoff.schema.json", "--fixture", "examples/fixtures/room-to-debate-handoff.valid.json"],
        ["./rtw", "validate", "--schema", "schemas/claim-boundary.schema.json", "--fixture", "examples/fixtures/claim-boundary.valid.json"],
        ["./rtw", "validate", "--schema", "schemas/agent-manifest.schema.json", "--fixture", "examples/agent-factory/duan-yongping.agent.manifest.json"],
        ["./rtw", "validate", "--schema", "schemas/agent-registry.schema.json", "--fixture", "config/agent-registry.json"],
        ["./rtw", "validate", "--schema", "schemas/agent-selection-request.schema.json", "--fixture", "examples/agent-factory/selection-request.manual-pool.json"],
    ]
    results = [run_json(command, timeout=timeout) for command in commands]
    return {"ok": all(item.get("ok") for item in results), "results": results}


def run_agent_factory_checks(timeout: int) -> dict[str, Any]:
    commands = {
        "bundle_validation": [
            "./rtw",
            "agent",
            "validate",
            "examples/agent-factory/duan-yongping.agent.manifest.json",
            "--profile",
            "examples/agent-factory/duan-yongping.roundtable-profile.md",
        ],
        "registry_list": [
            "./rtw",
            "agent",
            "list",
        ],
        "registry_validate": [
            "./rtw",
            "agent",
            "validate",
        ],
    }
    results = {name: run_json(command, timeout=timeout + 10) for name, command in commands.items()}
    return {"ok": all(item.get("ok") for item in results.values()), "results": results}


def run_public_cli_surface_checks(timeout: int) -> dict[str, Any]:
    commands = {
        "ship_check": [
            "./rtw",
            "ship-check",
            "Should we merge this AI-generated feature?",
        ],
        "launch_kit": [
            "./rtw",
            "launch-kit",
        ],
    }
    results = {name: run_json(command, timeout=timeout + 10) for name, command in commands.items()}
    launch_payload = results["launch_kit"].get("payload")
    missing_assets = (
        launch_payload.get("missing_assets", [])
        if isinstance(launch_payload, dict) and isinstance(launch_payload.get("missing_assets"), list)
        else ["missing launch-kit payload"]
    )
    return {
        "ok": all(item.get("ok") for item in results.values()) and not missing_assets,
        "results": results,
        "missing_assets": missing_assets,
    }


def run_legacy_release_readiness(args: argparse.Namespace, *, state_root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        ".codex/skills/room-skill/runtime/release_readiness_check.py",
        "--state-root",
        str(state_root / "legacy-release-readiness"),
        "--output-json",
        str(state_root / "legacy-release-readiness.json"),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    if args.strict_git_clean:
        command.append("--strict-git-clean")
    return run_json(command, timeout=args.timeout_seconds + 60)


def run_runtime_projection_validations(state_root: Path, timeout: int) -> dict[str, Any]:
    room = run_json(
        [
            "./rtw",
            "room",
            "我想讨论一个面向大学生的 AI 学习产品",
            "--state-root",
            str(state_root / "projection-room"),
        ],
        timeout=timeout + 30,
    )
    debate = run_json(
        [
            "./rtw",
            "debate",
            "这个创业方向值不值得做",
            "--state-root",
            str(state_root / "projection-debate"),
        ],
        timeout=timeout + 30,
    )
    room_standard = check_standard_run_files(room)
    debate_standard = check_standard_run_files(debate)
    return {
        "ok": room.get("ok") and debate.get("ok") and room_standard["ok"] and debate_standard["ok"],
        "room": room,
        "debate": debate,
        "standard_runs": {
            "room": room_standard,
            "debate": debate_standard,
        },
    }


def check_standard_run_files(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    run_dir = payload.get("run_dir") if isinstance(payload, dict) else None
    if not run_dir:
        return {"ok": False, "run_dir": None, "missing": ["run_dir"]}
    required = ["run.json", "input.json", "output.json", "evidence.json", "summary.md"]
    missing = [name for name in required if not (Path(str(run_dir)) / name).exists()]
    return {
        "ok": not missing,
        "run_dir": str(run_dir),
        "required": required,
        "missing": missing,
    }


def run_git_clean() -> dict[str, Any]:
    completed = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    dirty = [line for line in completed.stdout.splitlines() if line.strip()]
    return {"ok": completed.returncode == 0 and not dirty, "dirty_entries": dirty}


def collect_check_warnings(checks: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for name, check in checks.items():
        payload = check.get("payload") if isinstance(check.get("payload"), dict) else check
        if not isinstance(payload, dict):
            continue
        for item in payload.get("warnings", []) or []:
            warnings.append({"check": name, "warning": item})
    return warnings


def run_json(command: list[str], *, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    payload = extract_json(completed.stdout)
    json_parse_ok = isinstance(payload, dict)
    payload_ok = payload.get("ok") is True if json_parse_ok else False
    ok = completed.returncode == 0 and json_parse_ok and payload_ok
    return redact_sensitive_value({
        "ok": ok,
        "command": command,
        "returncode": completed.returncode,
        "payload": payload if isinstance(payload, dict) else None,
        "json_parse_ok": json_parse_ok,
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


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Release Check", "", f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`", ""]
    lines.append("| Check | OK |")
    lines.append("|---|---|")
    for name, check in report["checks"].items():
        lines.append(f"| `{name}` | `{check.get('ok')}` |")
    lines.extend(["", "## Release Blockers", ""])
    if report["release_blockers"]:
        for blocker in report["release_blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Release Warnings", ""])
    if report.get("release_warnings"):
        for warning in report["release_warnings"]:
            lines.append(f"- `{warning['check']}`: {warning['warning']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Claim Boundary", ""])
    for item in report["claim_boundary"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


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
