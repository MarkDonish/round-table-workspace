from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class V020CompletionTest(unittest.TestCase):
    def test_handoff_schema_fixture_and_debate_reference_are_valid(self) -> None:
        from roundtable_core.validation import validate_file

        handoff_result = validate_file(
            schema_path=REPO_ROOT / "schemas" / "room-to-debate-handoff.schema.json",
            instance_path=REPO_ROOT / "examples" / "fixtures" / "room-to-debate-handoff.valid.json",
        )
        debate_result = validate_file(
            schema_path=REPO_ROOT / "schemas" / "debate-session.schema.json",
            instance_path=REPO_ROOT / "examples" / "fixtures" / "debate-session.valid.json",
        )

        self.assertTrue(handoff_result.ok, handoff_result.to_json())
        self.assertTrue(debate_result.ok, debate_result.to_json())

        handoff = json.loads((REPO_ROOT / "examples" / "fixtures" / "room-to-debate-handoff.valid.json").read_text())
        debate = json.loads((REPO_ROOT / "examples" / "fixtures" / "debate-session.valid.json").read_text())
        self.assertEqual(debate["handoff_packet"]["source_room_session_id"], handoff["source_room_session_id"])

    def test_prompt_renderer_parser_state_store_and_fixture_adapter(self) -> None:
        from roundtable_core.prompts import PromptRenderError, parse_structured_output, render_prompt
        from roundtable_core.runtime import FixtureHostAdapter, create_run_dir, write_evidence, write_input, write_output, write_summary

        rendered = render_prompt(
            REPO_ROOT / "prompts" / "room-selection.md",
            {"mode": "room_full", "topic": "AI study product"},
            required_variables=["mode", "topic"],
        )
        self.assertIn("Runtime Input", rendered.text)

        with self.assertRaises(PromptRenderError):
            render_prompt(REPO_ROOT / "prompts" / "debate-reviewer.md", {}, required_variables=["review_packet"])

        parsed = parse_structured_output("prefix ```json\n{\"ok\": true, \"status\": \"allow\"}\n```", required_keys=["ok"])
        self.assertTrue(parsed.ok)

        malformed = parse_structured_output("no json here", required_keys=["ok"])
        self.assertFalse(malformed.ok)

        with tempfile.TemporaryDirectory() as temp_dir:
            run = create_run_dir(temp_dir, "room", run_id="room-test-run", created_at="20260429T010203Z")
            write_input(run.run_dir, {"question": "test"})
            write_output(run.run_dir, {"ok": True})
            write_evidence(run.run_dir, {"claim_boundary": {"host_live": "not_claimed"}})
            write_summary(run.run_dir, "# Summary")
            self.assertTrue((run.run_dir / "input.json").exists())
            adapter = FixtureHostAdapter()
            prepared = adapter.prepare_session(run, {"question": "test"})
            result = adapter.execute_turn(prepared)
            evidence = adapter.report_evidence(run, {"question": "test"}, result)
            self.assertEqual(result.claim_boundary["host_live"], "fixture_only")
            self.assertEqual(evidence["host"], "fixture")

    def test_scripts_and_docs_for_v020_full_scope_exist(self) -> None:
        required_paths = [
            "docs/decision-quality-rubric.md",
            "docs/index.md",
            "docs/skill-generation.md",
            "scripts/generate_skills.py",
            "scripts/check_skill_drift.py",
            "scripts/check_source_truth_consistency.py",
            "scripts/run_regression_fixtures.py",
            "scripts/claim_boundary_dashboard.py",
            "scripts/release_check.py",
            "evals/decision_quality/run_decision_evals.py",
            "skills_src/room.skill.yaml",
            "skills_src/debate.skill.yaml",
        ]
        for rel_path in required_paths:
            self.assertTrue((REPO_ROOT / rel_path).exists(), rel_path)

    def test_cli_exposes_release_check_interactive_and_demo(self) -> None:
        from roundtable import cli

        parser = cli.build_parser()
        help_text = parser.format_help()
        self.assertIn("release-check", help_text)
        self.assertIn("interactive", help_text)
        self.assertIn("demo", help_text)

        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> object:
            calls.append(command)
            return type("Completed", (), {"returncode": 0})()

        with patch.object(cli, "utc_timestamp", return_value="20260429T010203Z"):
            with patch("roundtable.cli.subprocess.run", side_effect=fake_run):
                self.assertEqual(cli.main(["release-check", "--include-fixtures"]), 0)

        self.assertIn("scripts/release_check.py", calls[0])
        self.assertIn("--include-fixtures", calls[0])


if __name__ == "__main__":
    unittest.main()
