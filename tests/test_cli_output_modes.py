from __future__ import annotations

import io
import json
import tempfile
import unittest
import uuid
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

    def test_ship_check_writes_output_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_json = Path(temp_dir) / "ship-check.json"
            output_md = Path(temp_dir) / "ship-check.md"
            code, stdout = self.invoke(
                [
                    "ship-check",
                    "Should we merge this AI-generated feature?",
                    "--quiet",
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(output_md),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["action"], "ship-check")
            self.assertEqual(payload["decision"], "revise")
            self.assertIn("Ship Check", output_md.read_text(encoding="utf-8"))

    def test_output_json_refuses_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            code, stdout = self.invoke(
                [
                    "ship-check",
                    "Should we merge this AI-generated feature?",
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(code, 2)
            self.assertIn("refusing to write output through symlink", stdout)
            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_output_json_refuses_symlink_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            real_dir = Path(temp_dir) / "real"
            real_dir.mkdir()
            link_dir = Path(temp_dir) / "link"
            link_dir.symlink_to(real_dir, target_is_directory=True)
            output_json = link_dir / "out.json"

            code, stdout = self.invoke(
                [
                    "ship-check",
                    "Should we merge this AI-generated feature?",
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(code, 2)
            self.assertIn("refusing path through symlink component", stdout)
            self.assertFalse((real_dir / "out.json").exists())

    def test_output_markdown_refuses_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.md"
            victim.write_text("keep", encoding="utf-8")
            output_md = Path(temp_dir) / "out.md"
            output_md.symlink_to(victim)

            code, stdout = self.invoke(
                [
                    "ship-check",
                    "Should we merge this AI-generated feature?",
                    "--output-markdown",
                    str(output_md),
                ]
            )

            self.assertEqual(code, 2)
            self.assertIn("refusing to write output through symlink", stdout)
            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_output_json_allows_system_tmp_parent(self) -> None:
        output_json = Path("/tmp") / f"rtw-output-{uuid.uuid4().hex}.json"
        try:
            code, stdout = self.invoke(
                [
                    "ship-check",
                    "Should we merge this AI-generated feature?",
                    "--quiet",
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["action"], "ship-check")
        finally:
            output_json.unlink(missing_ok=True)

    def test_root_level_output_flags_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launch_output = Path(temp_dir) / "launch-kit.json"

            code, stdout = self.invoke(["--quiet", "ship-check", "Should we merge this AI-generated feature?"])
            self.assertEqual(code, 0)
            self.assertEqual(stdout, "")

            code, stdout = self.invoke(["--output-json", str(launch_output), "launch-kit"])
            self.assertEqual(code, 0)
            self.assertIn('"action": "launch-kit"', stdout)
            payload = json.loads(launch_output.read_text(encoding="utf-8"))
            self.assertEqual(payload["action"], "launch-kit")

            code, stdout = self.invoke(["--json", "room", "讨论一个大学生 AI 学习产品", "--state-root", temp_dir])
            self.assertEqual(code, 0)
            payload = json.loads(stdout)
            self.assertEqual(payload["action"], "room")
            self.assertTrue(payload["ok"])

    def test_usage_validation_returns_two(self) -> None:
        code, output = self.invoke(["validate", "--schema", "schemas/room-session.schema.json"])
        self.assertEqual(code, 2)
        self.assertIn("--schema and at least one --fixture", output)

    def test_usage_validation_respects_quiet_and_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_json = Path(temp_dir) / "usage-error.json"
            code, output = self.invoke(
                [
                    "validate",
                    "--schema",
                    "schemas/room-session.schema.json",
                    "--quiet",
                    "--output-json",
                    str(output_json),
                ]
            )
            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["action"], "schema-validation")
            self.assertIn("--schema and at least one --fixture", payload["error"])

    def test_schema_validation_missing_fixture_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_fixture = Path(temp_dir) / "missing.json"
            output_json = Path(temp_dir) / "missing-fixture.json"
            output_markdown = Path(temp_dir) / "missing-fixture.md"

            code, output = self.invoke(
                [
                    "validate",
                    "--schema",
                    "schemas/room-session.schema.json",
                    "--fixture",
                    str(missing_fixture),
                    "--quiet",
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(output_markdown),
                ]
            )

            self.assertEqual(code, 1)
            self.assertEqual(output, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["action"], "schema-validation")
            self.assertIn("file does not exist", payload["results"][0]["errors"][0])
            markdown = output_markdown.read_text(encoding="utf-8")
            self.assertIn("## Issues", markdown)
            self.assertIn("file does not exist", markdown)

    def test_schema_validation_invalid_json_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_fixture = Path(temp_dir) / "bad.json"
            bad_fixture.write_text("{bad json", encoding="utf-8")
            output_json = Path(temp_dir) / "bad-fixture.json"

            code, output = self.invoke(
                [
                    "validate",
                    "--schema",
                    "schemas/room-session.schema.json",
                    "--fixture",
                    str(bad_fixture),
                    "--quiet",
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(code, 1)
            self.assertEqual(output, "")
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["action"], "schema-validation")
            self.assertIn("invalid JSON", payload["results"][0]["errors"][0])


if __name__ == "__main__":
    unittest.main()
