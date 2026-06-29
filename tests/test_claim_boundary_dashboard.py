from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch


class ClaimBoundaryDashboardTest(unittest.TestCase):
    def test_local_mainline_claimable_requires_release_gate_pass(self) -> None:
        from scripts import claim_boundary_dashboard

        args = SimpleNamespace(state_root="/tmp/rtw-claim-dashboard-test", timeout_seconds=1, strict_git_clean=False)

        def fake_run_json(command: list[str], *, timeout_seconds: int) -> dict[str, object]:
            del timeout_seconds
            if "live_lane_evidence_report.py" in command:
                return {
                    "ok": True,
                    "command": command,
                    "returncode": 0,
                    "payload": {
                        "ok": True,
                        "host_live_lanes": [],
                        "provider_live_lane": {"evidence_status": "not_configured", "claim": "not_claimed"},
                        "summary": {},
                    },
                    "stderr": "",
                }
            return {
                "ok": False,
                "command": command,
                "returncode": 1,
                "payload": {
                    "ok": True,
                    "release_scope": {"ship_decision": "blocked"},
                    "p0_blockers": [{"id": "working_tree_dirty"}],
                },
                "stderr": "",
            }

        with patch("scripts.claim_boundary_dashboard.run_json_command", side_effect=fake_run_json):
            with patch("scripts.claim_boundary_dashboard.git_commit", return_value="test-commit"):
                report = claim_boundary_dashboard.build_report(args)

        local_mainline = report["matrix"][0]
        self.assertFalse(report["ok"])
        self.assertEqual(local_mainline["lane"], "local_mainline")
        self.assertEqual(local_mainline["status"], "blocked")
        self.assertFalse(local_mainline["evidence_record"]["claimable"])
        self.assertEqual(report["release_gate"]["p0_blockers"], [{"id": "working_tree_dirty"}])

    def test_local_mainline_claimable_when_release_gate_has_no_p0_blockers(self) -> None:
        from scripts import claim_boundary_dashboard

        args = SimpleNamespace(state_root="/tmp/rtw-claim-dashboard-test", timeout_seconds=1, strict_git_clean=False)

        def fake_run_json(command: list[str], *, timeout_seconds: int) -> dict[str, object]:
            del timeout_seconds
            if "live_lane_evidence_report.py" in command:
                return {
                    "ok": True,
                    "command": command,
                    "returncode": 0,
                    "payload": {
                        "ok": True,
                        "host_live_lanes": [],
                        "provider_live_lane": {"evidence_status": "not_configured", "claim": "not_claimed"},
                        "summary": {},
                    },
                    "stderr": "",
                }
            return {
                "ok": True,
                "command": command,
                "returncode": 0,
                "payload": {
                    "ok": True,
                    "release_scope": {"ship_decision": "ready_for_codex_local_mainline_scope"},
                    "p0_blockers": [],
                },
                "stderr": "",
            }

        with patch("scripts.claim_boundary_dashboard.run_json_command", side_effect=fake_run_json):
            with patch("scripts.claim_boundary_dashboard.git_commit", return_value="test-commit"):
                report = claim_boundary_dashboard.build_report(args)

        local_mainline = report["matrix"][0]
        self.assertTrue(report["ok"])
        self.assertEqual(local_mainline["status"], "supported")
        self.assertTrue(local_mainline["evidence_record"]["claimable"])


if __name__ == "__main__":
    unittest.main()
