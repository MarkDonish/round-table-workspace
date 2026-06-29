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

    def test_run_json_rejects_empty_json_payload(self) -> None:
        from scripts import release_check

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="{}\n", stderr="")

        with patch("scripts.release_check.subprocess.run", side_effect=fake_run):
            result = release_check.run_json(["fake"], timeout=1)

        self.assertFalse(result["ok"])
        self.assertTrue(result["json_parse_ok"])
        self.assertEqual(result["payload"], {})

    def test_collect_check_warnings_includes_nested_payload_warnings(self) -> None:
        from scripts import release_check

        warnings = release_check.collect_check_warnings(
            {
                "source_truth": {
                    "ok": True,
                    "payload": {
                        "warnings": [
                            {"check": "release_publication_defaults", "warning": "workflow_default_tag_mismatch"}
                        ]
                    },
                },
                "direct": {"ok": True, "warnings": ["direct_warning"]},
            }
        )

        self.assertEqual(
            warnings,
            [
                {
                    "check": "source_truth",
                    "warning": {"check": "release_publication_defaults", "warning": "workflow_default_tag_mismatch"},
                },
                {"check": "direct", "warning": "direct_warning"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
