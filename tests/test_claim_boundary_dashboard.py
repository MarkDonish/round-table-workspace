from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch


class ClaimBoundaryDashboardTest(unittest.TestCase):
    def test_run_json_command_redacts_sensitive_stderr_and_payload(self) -> None:
        import subprocess

        from scripts import claim_boundary_dashboard

        token = "ghp_claimdashboard1234567890SECRET"

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                1,
                stdout=f'{{"ok": false, "token": "{token}"}}\n',
                stderr=f"Authorization: Basic {token}",
            )

        with patch("scripts.claim_boundary_dashboard.subprocess.run", side_effect=fake_run):
            result = claim_boundary_dashboard.run_json_command(["fake", "--token", token], timeout_seconds=1)

        result_text = str(result)
        self.assertNotIn(token, result_text)
        self.assertIn("[REDACTED]", result_text)

    def test_local_mainline_claimable_requires_release_gate_pass(self) -> None:
        from scripts import claim_boundary_dashboard

        args = SimpleNamespace(state_root="/tmp/rtw-claim-dashboard-test", timeout_seconds=1, strict_git_clean=False)

        def fake_run_json(command: list[str], *, timeout_seconds: int) -> dict[str, object]:
            del timeout_seconds
            if any("live_lane_evidence_report.py" in part for part in command):
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
                    "release_blockers": ["working_tree_dirty"],
                    "artifacts": {"json": "/tmp/release-check.json", "markdown": "/tmp/release-check.md"},
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
        self.assertEqual(report["release_gate"]["release_blockers"], ["working_tree_dirty"])

    def test_local_mainline_claimable_when_release_gate_has_no_blockers(self) -> None:
        from scripts import claim_boundary_dashboard

        args = SimpleNamespace(state_root="/tmp/rtw-claim-dashboard-test", timeout_seconds=1, strict_git_clean=False)

        def fake_run_json(command: list[str], *, timeout_seconds: int) -> dict[str, object]:
            del timeout_seconds
            if any("live_lane_evidence_report.py" in part for part in command):
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
                    "release_blockers": [],
                    "artifacts": {"json": "/tmp/release-check.json", "markdown": "/tmp/release-check.md"},
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
        self.assertEqual(
            local_mainline["evidence_record"]["artifact_paths"],
            ["/tmp/release-check.json", "/tmp/release-check.md"],
        )

    def test_claimable_lanes_require_artifact_paths_and_historical_host_is_not_claimable(self) -> None:
        from scripts import claim_boundary_dashboard

        args = SimpleNamespace(state_root="/tmp/rtw-claim-dashboard-test", timeout_seconds=1, strict_git_clean=False)

        def fake_run_json(command: list[str], *, timeout_seconds: int) -> dict[str, object]:
            del timeout_seconds
            if any("live_lane_evidence_report.py" in part for part in command):
                return {
                    "ok": True,
                    "command": command,
                    "returncode": 0,
                    "payload": {
                        "ok": True,
                        "artifacts": {
                            "json": "/tmp/live-lane-evidence-report.json",
                            "markdown": "/tmp/live-lane-evidence-report.md",
                        },
                        "host_live_lanes": [
                            {
                                "host_id": "claude_code",
                                "evidence_status": "historical_only",
                                "claim": "historical_evidence_not_current_claim",
                                "checked_in_evidence": {
                                    "report": "reports/CLAUDE_CODE_HOST_LIVE_VALIDATION_2026-04-27.md",
                                    "claimable": False,
                                    "evidence_status": "historical_only",
                                },
                            }
                        ],
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
                    "release_blockers": [],
                    "artifacts": {"json": "/tmp/release-check.json", "markdown": "/tmp/release-check.md"},
                },
                "stderr": "",
            }

        with patch("scripts.claim_boundary_dashboard.run_json_command", side_effect=fake_run_json):
            with patch("scripts.claim_boundary_dashboard.git_commit", return_value="test-commit"):
                report = claim_boundary_dashboard.build_report(args)

        for row in report["matrix"]:
            record = row["evidence_record"]
            if record["claimable"]:
                self.assertTrue(record["artifact_paths"], row["lane"])

        host_row = next(row for row in report["matrix"] if row["lane"] == "host:claude_code")
        self.assertEqual(host_row["status"], "historical_only")
        self.assertFalse(host_row["evidence_record"]["claimable"])


if __name__ == "__main__":
    unittest.main()
