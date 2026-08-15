from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.providers.client import (
    ProviderConfig,
    get_default_provider_config,
    run_live_panel_review,
)


class LiveProviderTest(unittest.TestCase):
    def test_provider_config_resolution(self) -> None:
        config = get_default_provider_config(provider="deepseek", model="deepseek-chat")
        self.assertEqual(config.provider, "deepseek")
        self.assertEqual(config.model, "deepseek-chat")
        self.assertIn("api.deepseek.com", config.base_url)

    @patch("roundtable_core.providers.client.call_chat_completion")
    def test_mock_live_panel_review(self, mock_chat: unittest.mock.MagicMock) -> None:
        mock_chat.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"vote": "ship", "reason": "All checks passed cleanly.", "key_concern": "None"}'
                    }
                }
            ]
        }
        config = ProviderConfig(
            provider="deepseek",
            base_url="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-chat",
        )
        votes = run_live_panel_review(
            question="Refactor auth layer",
            diff_context="diff --git a/auth.py b/auth.py",
            roles=["security-auditor", "engineering"],
            config=config,
        )
        self.assertEqual(len(votes), 2)
        agents = {v["agent"] for v in votes}
        self.assertIn("security-auditor", agents)
        self.assertIn("engineering", agents)
        self.assertTrue(all(v["vote"] == "ship" for v in votes))


if __name__ == "__main__":
    unittest.main()
