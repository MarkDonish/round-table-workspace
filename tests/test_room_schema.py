from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "room-session.schema.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "room-session.valid.json"


class RoomSessionSchemaTest(unittest.TestCase):
    def test_room_session_schema_exists_and_covers_required_fields(self) -> None:
        self.assertTrue(SCHEMA_PATH.exists())
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        required = set(schema["required"])
        for expected in [
            "schema_version",
            "session_id",
            "workflow",
            "user_question",
            "current_focus",
            "panel",
            "turns",
            "summaries",
            "handoff_packet",
            "claim_boundary",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(expected, required)

        self.assertEqual(schema["properties"]["schema_version"]["const"], "0.1.0")
        self.assertEqual(schema["properties"]["workflow"]["const"], "room")

    def test_room_session_fixture_passes_schema_validation(self) -> None:
        from roundtable.schema_validation import validate_file

        result = validate_file(schema_path=SCHEMA_PATH, instance_path=FIXTURE_PATH)

        self.assertTrue(result.ok, result.to_json())

    def test_schema_validator_rejects_missing_required_field(self) -> None:
        from roundtable.schema_validation import validate_instance

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        del fixture["workflow"]

        errors = validate_instance(instance=fixture, schema=schema)

        self.assertTrue(any("workflow" in error for error in errors), errors)

    def test_cli_can_validate_room_session_fixture(self) -> None:
        from roundtable import cli

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cli.main(
                [
                    "validate",
                    "--schema",
                    "schemas/room-session.schema.json",
                    "--fixture",
                    "tests/fixtures/room-session.valid.json",
                ]
            )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema"], "schemas/room-session.schema.json")
        self.assertEqual(payload["fixtures"], ["tests/fixtures/room-session.valid.json"])

    def test_protocol_spec_links_room_session_schema(self) -> None:
        protocol_spec = (REPO_ROOT / "docs" / "protocol-spec.md").read_text(encoding="utf-8")

        self.assertIn("schemas/room-session.schema.json", protocol_spec)
        self.assertIn("tests/fixtures/room-session.valid.json", protocol_spec)


if __name__ == "__main__":
    unittest.main()
