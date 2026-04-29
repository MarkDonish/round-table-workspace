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


FIXTURE_DIRS = [
    "tests/fixtures/room-basic",
    "tests/fixtures/debate-basic",
    "tests/fixtures/room-to-debate-basic",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run room/debate/handoff regression fixture checks.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    args = parser.parse_args()

    report = build_report()
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report() -> dict[str, Any]:
    results = [check_fixture_dir(REPO_ROOT / rel_dir) for rel_dir in FIXTURE_DIRS]
    return {
        "ok": all(item["ok"] for item in results),
        "action": "regression-fixture-check",
        "fixtures": results,
    }


def check_fixture_dir(fixture_dir: Path) -> dict[str, Any]:
    shape_path = fixture_dir / "expected-output-shape.json"
    claim_path = fixture_dir / "expected-claim-boundary.json"
    shape = json.loads(shape_path.read_text(encoding="utf-8"))
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    schema_path = REPO_ROOT / shape["schema"]
    fixture_path = REPO_ROOT / shape["fixture"]
    validation = validate_file(schema_path=schema_path, instance_path=fixture_path)
    instance = json.loads(fixture_path.read_text(encoding="utf-8"))
    missing = [field for field in shape["required_fields"] if field not in instance]
    claim_boundary = instance.get("claim_boundary", {})
    unsupported_live_claim = (
        claim_boundary.get("host_live") == "live_passed"
        or claim_boundary.get("provider_live") == "live_passed"
        or not claim.get("not_live_claim")
    )
    handoff_consumed = True
    if "consumer_fixture" in shape:
        consumer = json.loads((REPO_ROOT / shape["consumer_fixture"]).read_text(encoding="utf-8"))
        handoff_consumed = (
            consumer.get("handoff_packet", {}).get("source_room_session_id")
            == instance.get("source_room_session_id")
        )
    ok = validation.ok and not missing and not unsupported_live_claim and handoff_consumed
    return {
        "fixture_dir": str(fixture_dir.relative_to(REPO_ROOT)),
        "ok": ok,
        "schema_validation": validation.to_dict(),
        "missing_required_fields": missing,
        "unsupported_live_claim": unsupported_live_claim,
        "handoff_consumed_by_debate_fixture": handoff_consumed,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
