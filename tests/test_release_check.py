from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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

    def test_run_json_redacts_sensitive_stderr_and_payload(self) -> None:
        from scripts import release_check

        token = "ghp_releasecheck1234567890SECRET"

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                1,
                stdout=f'{{"ok": false, "api_key": "{token}"}}\n',
                stderr=f"Authorization: Bearer {token}",
            )

        with patch("scripts.release_check.subprocess.run", side_effect=fake_run):
            result = release_check.run_json(["fake", "--token", token], timeout=1)

        result_text = str(result)
        self.assertNotIn(token, result_text)
        self.assertIn("[REDACTED]", result_text)

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

    def test_release_check_includes_github_release_publication_check(self) -> None:
        from scripts import release_check

        commands: list[list[str]] = []

        def fake_run_json(command: list[str], **_: object) -> dict[str, object]:
            commands.append(command)
            return {"ok": True, "command": command, "payload": {"ok": True}, "stderr": ""}

        with tempfile.TemporaryDirectory() as temp_dir:
            args = SimpleNamespace(
                state_root=temp_dir,
                include_fixtures=False,
                strict_git_clean=False,
                timeout_seconds=1,
            )
            with patch("scripts.release_check.run_json", side_effect=fake_run_json):
                with patch("scripts.release_check.run_agent_factory_checks", return_value={"ok": True}):
                    with patch("scripts.release_check.run_public_cli_surface_checks", return_value={"ok": True}):
                        with patch("scripts.release_check.run_schema_validations", return_value={"ok": True}):
                            with patch("scripts.release_check.run_runtime_projection_validations", return_value={"ok": True}):
                                with patch("scripts.release_check.run_legacy_release_readiness", return_value={"ok": True}):
                                    report = release_check.build_report(args)

        self.assertTrue(report["ok"], report["release_blockers"])
        publication = report["checks"]["github_release_publication"]
        self.assertTrue(publication["ok"])
        publication_commands = [
            command
            for command in commands
            if ".codex/skills/room-skill/runtime/github_release_publication_check.py" in command
        ]
        self.assertEqual(len(publication_commands), 1)
        self.assertIn("--output-json", publication_commands[0])

    def test_release_check_refuses_symlink_state_root(self) -> None:
        from scripts import release_check

        with tempfile.TemporaryDirectory() as temp_dir:
            real_dir = Path(temp_dir) / "real"
            real_dir.mkdir()
            link_dir = Path(temp_dir) / "link"
            link_dir.symlink_to(real_dir, target_is_directory=True)
            args = SimpleNamespace(
                state_root=str(link_dir),
                include_fixtures=False,
                strict_git_clean=False,
                timeout_seconds=1,
            )

            with self.assertRaisesRegex(ValueError, "symlink component"):
                release_check.build_report(args)


if __name__ == "__main__":
    unittest.main()
