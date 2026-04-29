from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPO_ROOT / "docs" / "roadmap.md"
MILESTONE_PATH = REPO_ROOT / "docs" / "milestones" / "v0.2.0.md"


class MilestoneDocsTest(unittest.TestCase):
    def test_roadmap_and_v020_milestone_exist(self) -> None:
        self.assertTrue(ROADMAP_PATH.exists())
        self.assertTrue(MILESTONE_PATH.exists())

    def test_v020_milestone_covers_required_scope_and_priorities(self) -> None:
        text = MILESTONE_PATH.read_text(encoding="utf-8")

        for expected in [
            "RTW-001",
            "RTW-027",
            "P0",
            "P1",
            "P2",
            "P3",
            "rtw CLI",
            "golden demo",
            "protocol spec",
            "room/debate/handoff schema",
            "roundtable_core",
            "skill generator",
            "drift check",
            "decision quality rubric",
            "eval suite",
            "docs index",
            "source consistency check",
            "Out Of Scope",
            "provider-live",
            "host-live",
            "fixture pass",
        ]:
            self.assertIn(expected, text)

    def test_readme_links_roadmap_and_milestone(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("docs/roadmap.md", readme)
        self.assertIn("docs/milestones/v0.2.0.md", readme)


if __name__ == "__main__":
    unittest.main()
