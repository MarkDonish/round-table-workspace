from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]

from roundtable_core.commands.ship_check import (
    PanelVote,
    build_enhanced_ship_check_payload,
    evaluate_engineering_lens,
    evaluate_product_lens,
    evaluate_risk_lens,
    evaluate_specialist_lens,
    render_ship_check_markdown_report,
    save_ship_check_archive_report,
)
from roundtable_core.git.diff_inspector import GitDiffResult


class ShipCheckEnhancedTest(unittest.TestCase):
    def test_evaluate_product_lens_scenarios(self) -> None:
        # Large change without documentation
        large_no_docs_diff = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["src/core.py", "src/extra.py"],
            categories=["backend_code"],
            insertions=500,
            deletions=20,
            raw_diff="diff",
            summary_text="500 lines added",
        )
        vote_no_docs = evaluate_product_lens("New big feature", large_no_docs_diff)
        self.assertEqual(vote_no_docs.vote, "revise")
        self.assertIn("documentation", vote_no_docs.reason)

        # Well-scoped change
        normal_diff = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["docs/readme.md", "src/feature.py"],
            categories=["frontend_ui"],
            insertions=60,
            deletions=10,
            raw_diff="diff",
            summary_text="60 lines added",
        )
        vote_normal = evaluate_product_lens("Scoped change", normal_diff)
        self.assertEqual(vote_normal.vote, "ship")

    def test_evaluate_engineering_lens_scenarios(self) -> None:
        # Large code change without tests
        diff_no_tests = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["src/service.py", "src/handler.py"],
            categories=["api_endpoint"],
            insertions=350,
            deletions=15,
            raw_diff="diff",
            summary_text="350 lines added",
        )
        vote_no_tests = evaluate_engineering_lens("Large code change", diff_no_tests)
        self.assertEqual(vote_no_tests.vote, "revise")
        self.assertIn("no accompanying tests", vote_no_tests.reason)

        # Code change with tests
        diff_with_tests = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["src/service.py", "tests/test_service.py"],
            categories=["api_endpoint", "test_spec"],
            insertions=120,
            deletions=10,
            raw_diff="diff",
            summary_text="120 lines added",
        )
        vote_with_tests = evaluate_engineering_lens("Code with tests", diff_with_tests)
        self.assertEqual(vote_with_tests.vote, "ship")

    def test_evaluate_risk_lens_scenarios(self) -> None:
        # Compound risk: auth and migrations
        diff_compound = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["migrations/001.sql", "src/auth.py"],
            categories=["database_migration", "security_auth"],
            insertions=80,
            deletions=5,
            raw_diff="diff",
            summary_text="80 lines added",
        )
        vote_compound = evaluate_risk_lens("Compound change", diff_compound)
        self.assertEqual(vote_compound.vote, "revise")
        self.assertIn("Compound blast radius", vote_compound.reason)

    def test_evaluate_specialist_lenses(self) -> None:
        diff_auth = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["src/auth/jwt.py"],
            categories=["security_auth"],
            insertions=40,
            deletions=5,
            raw_diff="diff",
            summary_text="Auth changes",
        )
        sec_vote = evaluate_specialist_lens("security-auditor", diff_auth)
        self.assertEqual(sec_vote.vote, "revise")
        self.assertIn("Auth/secret", sec_vote.reason)

        diff_clean = GitDiffResult(
            ok=True,
            repo_root=str(REPO_ROOT),
            target_ref="working_tree",
            changed_files=["docs/guide.md"],
            categories=["docs"],
            insertions=20,
            deletions=0,
            raw_diff="diff",
            summary_text="Docs only",
        )
        db_vote = evaluate_specialist_lens("database-auditor", diff_clean)
        self.assertEqual(db_vote.vote, "ship")

    def test_build_enhanced_ship_check_payload_structure(self) -> None:
        payload = build_enhanced_ship_check_payload(
            "Validate user registration feature",
            roles=["security-auditor"],
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["action"], "ship-check")
        self.assertIn(payload["decision"], ("ship", "revise", "reject"))
        self.assertIn(payload["confidence"], ("high", "medium", "low"))
        self.assertGreaterEqual(len(payload["panel_votes"]), 4)  # Product, Eng, Risk, Security
        self.assertGreaterEqual(len(payload["blocking_risks"]), 1)
        self.assertGreaterEqual(len(payload["next_testable_steps"]), 2)
        self.assertIn("claim_boundary", payload)

    def test_render_and_save_archive_report(self) -> None:
        payload = build_enhanced_ship_check_payload("Deploy release v0.2.4")
        markdown = render_ship_check_markdown_report(payload)

        self.assertIn("# Ship Check Report", markdown)
        self.assertIn("## Executive Summary", markdown)
        self.assertIn("## Multi-Lens Panel Review", markdown)
        self.assertIn("## Blocking Risks", markdown)
        self.assertIn("## Next Testable Steps & Action Checklist", markdown)

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = (Path(tmp_dir) / "custom-ship-check.md").resolve()
            saved = save_ship_check_archive_report(payload, custom_path=save_path)
            self.assertEqual(saved, save_path)
            self.assertTrue(save_path.exists())
            content = save_path.read_text(encoding="utf-8")
            self.assertIn("Deploy release v0.2.4", content)

    def test_cli_ship_check_with_diff_and_save_flag(self) -> None:
        from roundtable import cli

        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = (Path(tmp_dir) / "cli-report.md").resolve()
            with redirect_stdout(stdout):
                code = cli.main([
                    "ship-check",
                    "Merge PR review workflow",
                    "--diff",
                    "--save",
                    str(out_file),
                    "--json",
                ])

            self.assertEqual(code, 0)
            output_str = stdout.getvalue()
            payload = json.loads(output_str)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["action"], "ship-check")
            self.assertIn("saved_report", payload)
            self.assertEqual(payload["saved_report"], str(out_file))
            self.assertTrue(out_file.exists())
            self.assertIn("Ship Check Report", out_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
