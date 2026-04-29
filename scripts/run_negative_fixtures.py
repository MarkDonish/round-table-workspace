#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.validation import validate_file


NEGATIVE_CASES = [
    {
        "id": "room_session_missing_panel",
        "schema": "schemas/room-session.schema.json",
        "fixture": "tests/fixtures/negative/room-session.missing-panel.json",
        "must_fail_with": "missing required property 'panel'",
    },
    {
        "id": "debate_result_allow_with_null_decision",
        "schema": "schemas/debate-result.schema.json",
        "fixture": "tests/fixtures/negative/debate-result.allow-with-null-decision.json",
        "must_fail_with": "final_decision",
    },
    {
        "id": "handoff_too_few_panel_members",
        "schema": "schemas/room-to-debate-handoff.schema.json",
        "fixture": "tests/fixtures/negative/handoff.too-few-panel-members.json",
        "must_fail_with": "recommended_panel",
    },
    {
        "id": "claim_boundary_false_local_first",
        "schema": "schemas/claim-boundary.schema.json",
        "fixture": "tests/fixtures/negative/claim-boundary.false-local-first.json",
        "must_fail_with": "local_first",
    },
    {
        "id": "provider_live_without_evidence",
        "schema": "schemas/claim-boundary.schema.json",
        "fixture": "tests/fixtures/negative/provider-live-without-evidence.json",
        "must_fail_with": "evidence_records",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that negative fixtures are rejected.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    args = parser.parse_args()

    report = build_report()
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report() -> dict[str, Any]:
    results = [run_case(case) for case in NEGATIVE_CASES]
    return {
        "ok": all(item["ok"] for item in results),
        "action": "negative-fixture-check",
        "cases": results,
    }


def run_case(case: dict[str, str]) -> dict[str, Any]:
    validation = validate_file(
        schema_path=REPO_ROOT / case["schema"],
        instance_path=REPO_ROOT / case["fixture"],
    )
    combined_errors = "\n".join(validation.errors)
    matched_expected_error = case["must_fail_with"] in combined_errors
    return {
        "id": case["id"],
        "ok": (not validation.ok) and matched_expected_error,
        "schema": case["schema"],
        "fixture": case["fixture"],
        "validator": validation.validator_name,
        "must_fail_with": case["must_fail_with"],
        "matched_expected_error": matched_expected_error,
        "validation": validation.to_dict(),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
