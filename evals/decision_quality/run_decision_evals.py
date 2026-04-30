#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVAL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EVAL_ROOT.parents[1]
CASE_DIR = EVAL_ROOT / "cases"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.decision_quality.rubric_engine import evaluate_case as evaluate_rubric_case


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fixture-based decision quality evals.")
    parser.add_argument("--output-markdown", help="Optional Markdown report path.")
    parser.add_argument("--output-json", help="Optional JSON report path.")
    args = parser.parse_args()

    report = build_report()
    markdown = render_markdown(report)
    output_markdown = Path(args.output_markdown).expanduser().resolve() if args.output_markdown else default_report_path()
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else output_markdown.with_suffix(".json")
    write_text(output_markdown, markdown)
    write_json(output_json, report)
    report["artifacts"] = {"markdown": str(output_markdown), "json": str(output_json)}
    write_json(output_json, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report() -> dict[str, Any]:
    cases = [load_case(path) for path in sorted(CASE_DIR.glob("*.yaml"))]
    results = [evaluate_case(case) for case in cases]
    return {
        "ok": all(item["ok"] for item in results),
        "action": "decision-quality-eval",
        "mode": "fixture_mock",
        "rubric": "docs/decision-quality-rubric.md",
        "cases": results,
        "artifacts": {},
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    rubric = evaluate_rubric_case(case)
    return {
        "id": case["id"],
        "workflow": case["workflow"],
        "ok": rubric.expected_result_met,
        **rubric.to_dict(),
    }


def load_case(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decision Quality Eval Report",
        "",
        f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`",
        "- Mode: `fixture_mock`",
        "- Live provider required: `false`",
        "- Host-live claim: `not_claimed`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        lines.append(
            f"- `{case['id']}` ({case['workflow']}): expected_met=`{case['ok']}`, "
            f"quality_pass=`{case['quality_pass']}`, total=`{case['total']}/14`"
        )
        for dimension, score in case["rubric_scores"].items():
            lines.append(f"  - `{dimension}`: `{score}`")
    lines.extend(
        [
            "",
            "This report evaluates fixture/mock output against `docs/decision-quality-rubric.md`.",
            "It is not host-live or provider-live validation evidence.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def default_report_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return REPO_ROOT / "reports" / "evals" / f"decision-quality-{timestamp}.md"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
