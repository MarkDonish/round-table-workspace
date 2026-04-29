from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


class RoundtableCliTest(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, str]:
        from roundtable import cli

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cli.main(argv)
        return code, stdout.getvalue()

    def test_doctor_quick_runs_consumer_self_check_with_default_state_root(self) -> None:
        from roundtable import cli

        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with patch.object(cli, "utc_timestamp", return_value="20260429T010203Z"):
            with patch("roundtable.cli.subprocess.run", side_effect=fake_run):
                code, _ = self.invoke(["doctor", "--quick"])

        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)
        command = calls[0]
        self.assertEqual(command[0], sys.executable)
        self.assertIn(".codex/skills/room-skill/runtime/agent_consumer_self_check.py", command)
        self.assertIn("--quick", command)
        self.assertIn("--state-root", command)
        state_root = command[command.index("--state-root") + 1]
        self.assertEqual(state_root, "/tmp/round-table-workspace/doctor/20260429T010203Z")

    def test_validate_quick_reuses_consumer_self_check(self) -> None:
        from roundtable import cli

        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with patch.object(cli, "utc_timestamp", return_value="20260429T020304Z"):
            with patch("roundtable.cli.subprocess.run", side_effect=fake_run):
                code, _ = self.invoke(["validate", "--quick"])

        self.assertEqual(code, 0)
        command = calls[0]
        self.assertIn(".codex/skills/room-skill/runtime/agent_consumer_self_check.py", command)
        self.assertIn("--quick", command)
        state_root = command[command.index("--state-root") + 1]
        self.assertEqual(state_root, "/tmp/round-table-workspace/validate/20260429T020304Z")

    def test_validate_runs_local_codex_regression_without_quick(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with patch("roundtable.cli.subprocess.run", side_effect=fake_run):
            code, _ = self.invoke(["validate", "--state-root", "/tmp/custom-validate"])

        self.assertEqual(code, 0)
        command = calls[0]
        self.assertIn(".codex/skills/room-skill/runtime/local_codex_regression.py", command)
        self.assertIn("--state-root", command)
        self.assertEqual(command[command.index("--state-root") + 1], "/tmp/custom-validate")

    def test_evidence_runs_live_lane_report(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with patch("roundtable.cli.subprocess.run", side_effect=fake_run):
            code, _ = self.invoke(["evidence", "--state-root", "/tmp/evidence"])

        self.assertEqual(code, 0)
        command = calls[0]
        self.assertIn(".codex/skills/room-skill/runtime/live_lane_evidence_report.py", command)
        self.assertEqual(command[command.index("--state-root") + 1], "/tmp/evidence")

    def test_room_stub_remains_available(self) -> None:
        code, output = self.invoke(["room", "--stub", "讨论一个大学生 AI 学习产品"])

        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["action"], "room")
        self.assertEqual(payload["status"], "safe_stub")
        self.assertIn("not host-live", payload["claim_boundary"][0])
        self.assertIn("room_runtime.py validate-canonical", " ".join(payload["next_commands"]))

    def test_debate_stub_remains_available(self) -> None:
        code, output = self.invoke(["debate", "--stub", "这个 MVP 值不值得做"])

        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["action"], "debate")
        self.assertEqual(payload["status"], "safe_stub")
        self.assertIn("not provider-live", payload["claim_boundary"][0])
        self.assertIn("debate_runtime.py validate-canonical", " ".join(payload["next_commands"]))

    def test_room_runs_fixture_backed_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            code, output = self.invoke(["room", "讨论一个大学生 AI 学习产品", "--state-root", temp_dir])
            self.assertEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "fixture_backed")
            self.assertTrue(payload["schema_validation"]["ok"])
            self.assertTrue(Path(payload["outputs"]["room_session"]).exists())
            self.assertTrue(Path(payload["outputs"]["portable_handoff_packet"]).exists())

    def test_debate_runs_fixture_backed_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            code, output = self.invoke(["debate", "这个 MVP 值不值得做", "--state-root", temp_dir])
            self.assertEqual(code, 0)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "fixture_backed")
            self.assertTrue(payload["schema_validation"]["debate_session"]["ok"])
            self.assertTrue(payload["schema_validation"]["debate_result"]["ok"])
            self.assertTrue(Path(payload["outputs"]["debate_session"]).exists())
            self.assertTrue(Path(payload["outputs"]["debate_result"]).exists())

    def test_repo_root_points_to_checkout(self) -> None:
        from roundtable import cli

        self.assertTrue((cli.REPO_ROOT / "AGENTS.md").exists())
        self.assertEqual(cli.REPO_ROOT, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
