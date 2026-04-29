#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate v0.2.0 release checks.")
    parser.add_argument("--state-root", default="/tmp/round-table-release-check")
    parser.add_argument("--include-fixtures", action="store_true")
    parser.add_argument("--strict-git-clean", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    report = build_report(args)
    state_root = Path(args.state_root).expanduser().resolve()
    write_json(state_root / "release-check.json", report)
    write_text(state_root / "release-check.md", render_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}
    checks["source_truth_consistency"] = run_json(
        [
            sys.executable,
            "scripts/check_source_truth_consistency.py",
            "--output-json",
            str(state_root / "source-truth-consistency.json"),
            "--output-markdown",
            str(state_root / "source-truth-consistency.md"),
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
    checks["schema_validation"] = run_schema_validations(args.timeout_seconds)
    checks["regression_fixtures"] = run_json(
        [
            sys.executable,
            "scripts/run_regression_fixtures.py",
            "--output-json",
            str(state_root / "regression-fixtures.json"),
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
    checks["claim_boundary_dashboard"] = run_json(
        [
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
        ],
        timeout=args.timeout_seconds + 40,
    )
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
    return {
        "ok": not blockers,
        "action": "release-check",
        "state_root": str(state_root),
        "include_fixtures": args.include_fixtures,
        "strict_git_clean": args.strict_git_clean,
        "checks": checks,
        "release_blockers": blockers,
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
        ["./rtw", "validate", "--schema", "schemas/room-to-debate-handoff.schema.json", "--fixture", "examples/fixtures/room-to-debate-handoff.valid.json"],
    ]
    results = [run_json(command, timeout=timeout) for command in commands]
    return {"ok": all(item.get("ok") for item in results), "results": results}


def run_git_clean() -> dict[str, Any]:
    completed = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    dirty = [line for line in completed.stdout.splitlines() if line.strip()]
    return {"ok": completed.returncode == 0 and not dirty, "dirty_entries": dirty}


def run_json(command: list[str], *, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    payload = extract_json(completed.stdout)
    ok = completed.returncode == 0 and (not isinstance(payload, dict) or payload.get("ok") is not False)
    return {
        "ok": ok,
        "command": command,
        "returncode": completed.returncode,
        "payload": payload if isinstance(payload, dict) else None,
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
    lines.extend(["", "## Claim Boundary", ""])
    for item in report["claim_boundary"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
