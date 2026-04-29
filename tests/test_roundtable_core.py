from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class RoundtableCoreTest(unittest.TestCase):
    def test_core_package_namespaces_are_importable(self) -> None:
        import roundtable_core.agents
        import roundtable_core.prompts
        import roundtable_core.protocol
        import roundtable_core.runtime
        import roundtable_core.validation

        self.assertEqual(roundtable_core.protocol.__name__, "roundtable_core.protocol")
        self.assertEqual(roundtable_core.runtime.__name__, "roundtable_core.runtime")

    def test_schema_validation_is_available_from_core_and_legacy_path(self) -> None:
        from roundtable.schema_validation import validate_file as legacy_validate_file
        from roundtable_core.validation import validate_file as core_validate_file

        schema_path = REPO_ROOT / "schemas" / "room-session.schema.json"
        fixture_path = REPO_ROOT / "tests" / "fixtures" / "room-session.valid.json"

        core_result = core_validate_file(schema_path=schema_path, instance_path=fixture_path)
        legacy_result = legacy_validate_file(schema_path=schema_path, instance_path=fixture_path)

        self.assertTrue(core_result.ok, core_result.to_json())
        self.assertTrue(legacy_result.ok, legacy_result.to_json())
        self.assertEqual(core_result.to_dict(), legacy_result.to_dict())

    def test_runtime_state_root_helper_matches_cli_defaults(self) -> None:
        from roundtable import cli
        from roundtable_core.runtime import default_state_root, resolve_state_root

        with patch("roundtable_core.runtime.paths.utc_timestamp", return_value="20260429T030405Z"):
            self.assertEqual(
                str(default_state_root("validate")),
                "/tmp/round-table-workspace/validate/20260429T030405Z",
            )

        self.assertEqual(
            cli.resolve_state_root("/tmp/custom-state-root", "validate"),
            str(resolve_state_root("/tmp/custom-state-root", "validate")),
        )

    def test_claim_boundary_helper_is_claim_safe(self) -> None:
        from roundtable_core.protocol import ClaimStatus, local_first_claim_boundary

        boundary = local_first_claim_boundary(notes=["fixture validation only"])

        self.assertTrue(boundary["local_first"])
        self.assertEqual(boundary["host_live"], ClaimStatus.NOT_CLAIMED.value)
        self.assertEqual(boundary["provider_live"], ClaimStatus.NOT_CLAIMED.value)
        self.assertIn("fixture validation only", boundary["notes"])

    def test_evidence_metadata_helper_is_json_ready(self) -> None:
        from roundtable_core.runtime import build_evidence_metadata

        metadata = build_evidence_metadata(
            workflow="room",
            action="schema-validation",
            claim_boundary={"local_first": True, "host_live": "not_claimed"},
            generated_at="2026-04-29T00:00:00Z",
        )

        payload = json.loads(json.dumps(metadata))
        self.assertEqual(payload["workflow"], "room")
        self.assertEqual(payload["action"], "schema-validation")
        self.assertEqual(payload["claim_boundary"]["host_live"], "not_claimed")


if __name__ == "__main__":
    unittest.main()
