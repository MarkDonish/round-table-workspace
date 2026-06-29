from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch


class ReleaseCheckTest(unittest.TestCase):
    def test_run_json_requires_parseable_json_payload(self) -> None:
        from scripts import release_check

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="plain success\n", stderr="")

        with patch("scripts.release_check.subprocess.run", side_effect=fake_run):
            result = release_check.run_json(["fake"], timeout=1)

        self.assertFalse(result["ok"])
        self.assertFalse(result["json_parse_ok"])
        self.assertIsNone(result["payload"])

    def test_run_json_accepts_successful_json_payload(self) -> None:
        from scripts import release_check

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout='{"ok": true, "action": "fake"}\n', stderr="")

        with patch("scripts.release_check.subprocess.run", side_effect=fake_run):
            result = release_check.run_json(["fake"], timeout=1)

        self.assertTrue(result["ok"])
        self.assertTrue(result["json_parse_ok"])
        self.assertEqual(result["payload"]["action"], "fake")


if __name__ == "__main__":
    unittest.main()
