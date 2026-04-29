from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_SCHEMA_PATH = REPO_ROOT / "schemas" / "debate-session.schema.json"
RESULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "debate-result.schema.json"
SESSION_FIXTURE_PATH = REPO_ROOT / "examples" / "fixtures" / "debate-session.valid.json"
RESULT_FIXTURE_PATH = REPO_ROOT / "examples" / "fixtures" / "debate-result.valid.json"


class DebateSchemaTest(unittest.TestCase):
    def test_debate_schema_files_cover_required_fields(self) -> None:
        self.assertTrue(SESSION_SCHEMA_PATH.exists())
        self.assertTrue(RESULT_SCHEMA_PATH.exists())

        session_schema = json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))
        result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))

        for schema in [session_schema, result_schema]:
            required = set(schema["required"])
            for expected in [
                "launch_bundle",
                "selected_panel",
                "agent_arguments",
                "moderator_summary",
                "reviewer_result",
                "final_outcome",
                "open_questions",
                "evidence",
                "claim_boundary",
            ]:
                self.assertIn(expected, required)
            self.assertEqual(schema["properties"]["workflow"]["const"], "debate")

        self.assertEqual(result_schema["properties"]["schema_version"]["const"], "0.1.0")
        self.assertEqual(
            result_schema["properties"]["final_outcome"]["enum"],
            ["allow", "reject", "follow_up_required"],
        )

    def test_debate_fixtures_pass_schema_validation(self) -> None:
        from roundtable.schema_validation import validate_file

        session_result = validate_file(schema_path=SESSION_SCHEMA_PATH, instance_path=SESSION_FIXTURE_PATH)
        result_result = validate_file(schema_path=RESULT_SCHEMA_PATH, instance_path=RESULT_FIXTURE_PATH)

        self.assertTrue(session_result.ok, session_result.to_json())
        self.assertTrue(result_result.ok, result_result.to_json())

    def test_result_schema_rejects_unknown_final_outcome(self) -> None:
        from roundtable.schema_validation import validate_instance

        schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        fixture = json.loads(RESULT_FIXTURE_PATH.read_text(encoding="utf-8"))
        fixture["final_outcome"] = "maybe"

        errors = validate_instance(instance=fixture, schema=schema)

        self.assertTrue(any("final_outcome" in error for error in errors), errors)

    def test_cli_can_validate_debate_schema_fixtures(self) -> None:
        from roundtable import cli

        commands = [
            [
                "validate",
                "--schema",
                "schemas/debate-session.schema.json",
                "--fixture",
                "examples/fixtures/debate-session.valid.json",
            ],
            [
                "validate",
                "--schema",
                "schemas/debate-result.schema.json",
                "--fixture",
                "examples/fixtures/debate-result.valid.json",
            ],
        ]

        for command in commands:
            with self.subTest(command=command):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = cli.main(command)
                payload = json.loads(stdout.getvalue())
                self.assertEqual(code, 0)
                self.assertTrue(payload["ok"])

    def test_protocol_spec_and_readme_link_debate_schemas(self) -> None:
        protocol_spec = (REPO_ROOT / "docs" / "protocol-spec.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in [
            "schemas/debate-session.schema.json",
            "schemas/debate-result.schema.json",
            "examples/fixtures/debate-session.valid.json",
            "examples/fixtures/debate-result.valid.json",
        ]:
            self.assertIn(expected, protocol_spec)

        self.assertIn("schemas/debate-session.schema.json", readme)
        self.assertIn("schemas/debate-result.schema.json", readme)


if __name__ == "__main__":
    unittest.main()
