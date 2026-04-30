from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roundtable_core.protocol import build_debate_result
from roundtable_core.validation import validate_file


REPO_ROOT = Path(__file__).resolve().parents[1]


class DebateResultBuilderTest(unittest.TestCase):
    def fixture_parts(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        fixture = json.loads((REPO_ROOT / "examples" / "fixtures" / "debate-result.allow.json").read_text(encoding="utf-8"))
        roundtable_record = {
            "agent_outputs": fixture["agent_arguments"],
            "moderator_summary": fixture["moderator_summary"],
            "evidence_buckets": fixture["evidence"],
        }
        return fixture["launch_bundle"], roundtable_record, fixture["reviewer_result"]

    def assert_valid_result(self, result: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "debate-result.json"
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            validation = validate_file(schema_path=REPO_ROOT / "schemas" / "debate-result.schema.json", instance_path=path)
            self.assertTrue(validation.ok, validation.errors)

    def test_builder_allows_final_decision(self) -> None:
        launch_bundle, roundtable_record, review_result = self.fixture_parts()
        result = build_debate_result(
            launch_bundle=launch_bundle,
            roundtable_record=roundtable_record,
            review_packet={},
            review_result=review_result,
        )
        self.assertEqual(result["final_outcome"], "allow")
        self.assertIsInstance(result["final_decision"], dict)
        self.assert_valid_result(result)

    def test_builder_rejects_severe_red_flags(self) -> None:
        launch_bundle, roundtable_record, review_result = self.fixture_parts()
        review_result = dict(review_result)
        review_result["allow_final_decision"] = False
        review_result["severe_red_flags"] = ["fabricated live support claim"]
        result = build_debate_result(
            launch_bundle=launch_bundle,
            roundtable_record=roundtable_record,
            review_packet={},
            review_result=review_result,
        )
        self.assertEqual(result["final_outcome"], "reject")
        self.assertIsNone(result["final_decision"])
        self.assert_valid_result(result)

    def test_builder_requires_followup(self) -> None:
        launch_bundle, roundtable_record, review_result = self.fixture_parts()
        review_result = dict(review_result)
        review_result["allow_final_decision"] = False
        review_result["required_followups"] = ["define target segment"]
        result = build_debate_result(
            launch_bundle=launch_bundle,
            roundtable_record=roundtable_record,
            review_packet={},
            review_result=review_result,
        )
        self.assertEqual(result["final_outcome"], "follow_up_required")
        self.assertIn("define target segment", result["open_questions"])
        self.assert_valid_result(result)


if __name__ == "__main__":
    unittest.main()
