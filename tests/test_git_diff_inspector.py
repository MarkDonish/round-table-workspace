from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.git.diff_inspector import GitDiffInspector, GitDiffResult, inspect_git_diff
from roundtable_core.git.heuristic_router import HeuristicRoleRouter, recommend_panel_for_diff
from roundtable.cli import build_ship_check_payload


class GitDiffInspectorTest(unittest.TestCase):
    def test_inspect_current_repo(self) -> None:
        result = inspect_git_diff(REPO_ROOT)
        self.assertTrue(result.ok)
        self.assertEqual(result.repo_root, str(REPO_ROOT))
        self.assertIsInstance(result.changed_files, list)
        self.assertIsInstance(result.categories, list)

    def test_non_git_directory_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = inspect_git_diff(tmp_dir)
            self.assertFalse(result.ok)
            self.assertEqual(result.error, "not_a_git_repository")
            self.assertIn("not a Git repository", result.summary_text)

    def test_file_categorization_logic(self) -> None:
        files = [
            "migrations/0001_initial.py",
            "src/auth/jwt_handler.py",
            "api/v1/routes.py",
            "frontend/components/Button.tsx",
            "tests/test_something.py",
            ".github/workflows/ci.yml",
        ]
        categories = GitDiffInspector._categorize_files(files)
        self.assertIn("database_migration", categories)
        self.assertIn("security_auth", categories)
        self.assertIn("api_endpoint", categories)
        self.assertIn("frontend_ui", categories)
        self.assertIn("test_spec", categories)
        self.assertIn("config_ci", categories)

    def test_heuristic_router_specialist_mapping(self) -> None:
        mock_diff = GitDiffResult(
            ok=True,
            repo_root="/dummy",
            target_ref="working_tree",
            changed_files=["migrations/001_users.sql", "src/auth/session.py", "api/routes.py"],
            categories=["api_endpoint", "database_migration", "security_auth"],
            insertions=120,
            deletions=10,
            raw_diff="dummy diff content",
            summary_text="Changed files: 3",
        )
        recommendation = recommend_panel_for_diff(mock_diff)
        self.assertIn("engineering", recommendation.roles)
        self.assertIn("database-auditor", recommendation.roles)
        self.assertIn("security-auditor", recommendation.roles)
        self.assertIn("api-contract-reviewer", recommendation.roles)
        self.assertEqual(recommendation.primary_focus, "specialist_verification")

    def test_ship_check_dynamic_diff_payload(self) -> None:
        payload = build_ship_check_payload("Review recent commit", diff=True, cwd=str(REPO_ROOT))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["action"], "ship-check")
        self.assertIn(payload["decision"], ("ship", "revise", "reject"))
        self.assertIn("panel_votes", payload)
        self.assertIn("diff_summary", payload)


if __name__ == "__main__":
    unittest.main()
