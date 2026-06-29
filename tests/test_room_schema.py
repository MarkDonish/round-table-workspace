from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


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

    def test_fallback_schema_validator_is_forced_in_unit_test(self) -> None:
        from roundtable_core.validation.json_schema import validate_instance_details

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        invalid_fixture = dict(fixture)
        del invalid_fixture["panel"]

        with patch("roundtable_core.validation.json_schema.Draft202012Validator", None):
            errors, validator_name, supported_draft = validate_instance_details(instance=fixture, schema=schema)
            invalid_errors, _, _ = validate_instance_details(instance=invalid_fixture, schema=schema)

        self.assertEqual(errors, [])
        self.assertEqual(validator_name, "rtw-subset")
        self.assertEqual(supported_draft, "draft-2020-12-subset")
        self.assertTrue(any("panel" in error for error in invalid_errors), invalid_errors)

    def test_jsonschema_validator_uses_format_checker(self) -> None:
        from roundtable_core.validation.json_schema import validate_instance_details

        class FakeError:
            path = ["created_at"]
            message = "is not a date-time"

        class FakeFormatChecker:
            pass

        class FakeDraftValidator:
            def __init__(self, schema: dict[str, object], *, format_checker: object | None = None) -> None:
                self.format_checker = format_checker

            def iter_errors(self, instance: dict[str, object]) -> list[FakeError]:
                if self.format_checker is None:
                    return []
                return [FakeError()]

        schema = {"type": "object", "properties": {"created_at": {"type": "string", "format": "date-time"}}}
        instance = {"created_at": "not-a-date"}

        with patch("roundtable_core.validation.json_schema.Draft202012Validator", FakeDraftValidator):
            with patch("roundtable_core.validation.json_schema.FormatChecker", FakeFormatChecker):
                errors, validator_name, supported_draft = validate_instance_details(instance=instance, schema=schema)

        self.assertEqual(validator_name, "jsonschema.Draft202012Validator")
        self.assertEqual(supported_draft, "draft-2020-12")
        self.assertEqual(errors, ["$.created_at: is not a date-time"])

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
