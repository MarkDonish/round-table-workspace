from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


class CliOutputModesTest(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, str]:
        from roundtable import cli

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cli.main(argv)
        return code, stdout.getvalue()

    def test_validate_schema_writes_output_json_and_quiet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_json = Path(temp_dir) / "validation.json"
            code, stdout = self.invoke(
                [
                    "validate",
                    "--schema",
                    "schemas/room-session.schema.json",
                    "--fixture",
                    "tests/fixtures/room-session.valid.json",
                    "--quiet",
                    "--output-json",
                    str(output_json),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["action"], "schema-validation")

    def test_room_json_output_and_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_md = Path(temp_dir) / "room.md"
            code, stdout = self.invoke(
                [
                    "room",
                    "讨论一个大学生 AI 学习产品",
                    "--state-root",
                    temp_dir,
                    "--json",
                    "--output-markdown",
                    str(output_md),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue((Path(payload["run_dir"]) / "run.json").exists())
            self.assertIn("Room", output_md.read_text(encoding="utf-8"))

    def test_usage_validation_returns_two(self) -> None:
        code, output = self.invoke(["validate", "--schema", "schemas/room-session.schema.json"])
        self.assertEqual(code, 2)
        self.assertIn("--schema and at least one --fixture", output)


if __name__ == "__main__":
    unittest.main()
