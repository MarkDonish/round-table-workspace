from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.github_pr_review import render_fallback_md


class GitHubPRReviewTest(unittest.TestCase):
    def test_render_fallback_md(self) -> None:
        payload = {
            "decision": "ship",
            "action": "ship-check",
            "confidence": "high",
            "panel_votes": [
                {"agent": "security-auditor", "vote": "ship", "reason": "No security risks."},
                {"agent": "engineering", "vote": "ship", "reason": "Clean code and high coverage."},
            ],
        }
        md = render_fallback_md(payload)
        self.assertIn("# 🚦 Round Table Review: `SHIP`", md)
        self.assertIn("security-auditor", md)
        self.assertIn("engineering", md)


if __name__ == "__main__":
    unittest.main()
