from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class JsonSuccessGateTest(unittest.TestCase):
    def test_claim_boundary_dashboard_rejects_empty_json_success(self) -> None:
        from scripts import claim_boundary_dashboard

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="{}\n", stderr="")

        with patch("scripts.claim_boundary_dashboard.subprocess.run", side_effect=fake_run):
            result = claim_boundary_dashboard.run_json_command(["fake"], timeout_seconds=1)

        self.assertFalse(result["ok"])
        self.assertEqual(result["payload"], {})

    def test_agent_consumer_self_check_rejects_empty_json_success(self) -> None:
        module = load_module(
            "agent_consumer_self_check_gate_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "agent_consumer_self_check.py",
        )

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="{}\n", stderr="")

        with patch.object(module.subprocess, "run", side_effect=fake_run):
            result = module.run_json_command(["fake"], timeout_seconds=1)

        self.assertFalse(result["ok"])
        self.assertTrue(result["json_parse_ok"])
        self.assertEqual(result["payload"], {})

    def test_agent_consumer_self_check_summarizes_source_truth_blocker(self) -> None:
        module = load_module(
            "agent_consumer_self_check_summary_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "agent_consumer_self_check.py",
        )

        summary = module.build_summary(
            source_audit={"ok": True, "payload": {"summary": {}}},
            release_readiness={"ok": True, "payload": {"release_scope": {}, "p0_blockers": [], "pass_criteria": {}}},
            source_consistency={"ok": False, "payload": {"problems": [{"check": "release_publication_defaults"}]}},
            skill_drift={"ok": True, "payload": {}},
            quick=True,
        )

        self.assertFalse(summary["local_first_mainline_ready"])
        self.assertIn("source_truth_consistency_failed", summary["p0_blockers"])
        self.assertFalse(summary["source_truth_consistency_ok"])

    def test_development_checkpoint_rejects_empty_json_success(self) -> None:
        module = load_module(
            "development_checkpoint_gate_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "development_checkpoint.py",
        )

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="{}\n", stderr="")

        with patch.object(module.subprocess, "run", side_effect=fake_run):
            result = module.run_json_command(["fake"], timeout_seconds=1)

        self.assertFalse(result["ok"])
        self.assertTrue(result["json_parse_ok"])
        self.assertEqual(result["payload"], {})


def load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
