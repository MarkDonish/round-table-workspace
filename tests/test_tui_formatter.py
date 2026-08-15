from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.ui.formatter import TUIFormatter, format_ship_check_terminal


class TUIFormatterTest(unittest.TestCase):
    def test_ship_check_terminal_formatting_no_color(self) -> None:
        payload = {
            "action": "ship-check",
            "decision": "ship",
            "confidence": "high",
            "question": "Deploy v0.3.0 release",
            "panel_votes": [
                {"agent": "security-auditor", "vote": "ship", "reason": "No vulnerabilities."},
                {"agent": "engineering", "vote": "ship", "reason": "Tests all green."},
            ],
            "categories": ["api_endpoint", "test_spec"],
            "risks": ["Minor latency increase"],
            "next_actions": ["Run git push"],
        }
        output = format_ship_check_terminal(payload, use_color=False)
        self.assertIn("ROUND TABLE WORKSPACE", output)
        self.assertIn("SHIP", output)
        self.assertIn("Deploy v0.3.0 release", output)
        self.assertIn("security-auditor", output)
        self.assertIn("engineering", output)
        self.assertIn("Detected Categories: api_endpoint, test_spec", output)
        self.assertIn("Run git push", output)

    def test_ship_check_terminal_formatting_colored(self) -> None:
        payload = {
            "action": "ship-check",
            "decision": "revise",
            "confidence": "medium",
            "question": "Auth refactor",
            "panel_votes": [
                {"agent": "security-auditor", "vote": "revise", "reason": "Missing token revocation test."},
            ],
        }
        output = format_ship_check_terminal(payload, use_color=True)
        self.assertIn("\033[", output)  # Contains ANSI codes
        self.assertIn("REVISE", output)


if __name__ == "__main__":
    unittest.main()
