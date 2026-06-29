from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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

    def test_agent_consumer_self_check_refuses_symlink_output_json(self) -> None:
        module = load_module(
            "agent_consumer_self_check_output_guard_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "agent_consumer_self_check.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            with self.assertRaisesRegex(ValueError, "symlink component"):
                module.write_json(output_json, {"ok": True})

            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_source_truth_refuses_symlink_output_json(self) -> None:
        from scripts import check_source_truth_consistency

        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            with self.assertRaisesRegex(ValueError, "symlink component"):
                check_source_truth_consistency.write_json(output_json, {"ok": True})

            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_report_writers_refuse_symlink_outputs(self) -> None:
        from evals.decision_quality import run_decision_evals
        from scripts import (
            check_agent_registry_sync,
            check_skill_drift,
            claim_boundary_dashboard,
            release_check,
            run_negative_fixtures,
            run_regression_fixtures,
        )

        runtime_dir = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
        modules = [
            check_agent_registry_sync,
            check_skill_drift,
            claim_boundary_dashboard,
            release_check,
            run_negative_fixtures,
            run_regression_fixtures,
            run_decision_evals,
            load_module("agent_host_inventory_guard_test", runtime_dir / "agent_host_inventory.py"),
            load_module("generic_agent_json_wrapper_validation_guard_test", runtime_dir / "generic_agent_json_wrapper_validation.py"),
            load_module("generic_agent_adapter_validation_guard_test", runtime_dir / "generic_agent_adapter_validation.py"),
            load_module("local_agent_host_validation_matrix_guard_test", runtime_dir / "local_agent_host_validation_matrix.py"),
            load_module("chat_completions_live_validation_guard_test", runtime_dir / "chat_completions_live_validation.py"),
            load_module("host_recipes_consistency_check_guard_test", runtime_dir / "host_recipes_consistency_check.py"),
            load_module("live_lane_evidence_report_guard_test", runtime_dir / "live_lane_evidence_report.py"),
            load_module("release_readiness_check_guard_test", runtime_dir / "release_readiness_check.py"),
            load_module("development_checkpoint_guard_test", runtime_dir / "development_checkpoint.py"),
            load_module("post_release_consumer_audit_guard_test", runtime_dir / "post_release_consumer_audit.py"),
            load_module("release_candidate_report_guard_test", runtime_dir / "release_candidate_report.py"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for index, module in enumerate(modules):
                victim = Path(temp_dir) / f"victim-{index}.json"
                victim.write_text("keep", encoding="utf-8")
                output_json = Path(temp_dir) / f"out-{index}.json"
                output_json.symlink_to(victim)

                with self.assertRaisesRegex(ValueError, "symlink component"):
                    module.write_json(output_json, {"ok": True})

                self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_generic_agent_executor_writer_refuses_symlink_output(self) -> None:
        module = load_module(
            "generic_agent_executor_output_guard_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "generic_agent_executor.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            with self.assertRaisesRegex(ValueError, "symlink component"):
                module.write_json_file(output_json, {"ok": True})

            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_runtime_state_root_helpers_refuse_symlink_roots(self) -> None:
        from scripts import claim_boundary_dashboard

        runtime_dir = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
        helper_calls = [
            lambda value: claim_boundary_dashboard.resolve_state_root(value),
            lambda value: load_module(
                "agent_consumer_self_check_state_root_guard_test",
                runtime_dir / "agent_consumer_self_check.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "release_readiness_check_state_root_guard_test",
                runtime_dir / "release_readiness_check.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "live_lane_evidence_report_state_root_guard_test",
                runtime_dir / "live_lane_evidence_report.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "local_agent_host_validation_matrix_state_root_guard_test",
                runtime_dir / "local_agent_host_validation_matrix.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "generic_agent_adapter_validation_state_root_guard_test",
                runtime_dir / "generic_agent_adapter_validation.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "generic_agent_json_wrapper_validation_state_root_guard_test",
                runtime_dir / "generic_agent_json_wrapper_validation.py",
            ).resolve_state_root(value),
            lambda value: load_module(
                "development_checkpoint_state_root_guard_test",
                runtime_dir / "development_checkpoint.py",
            ).resolve_user_path(value, include_leaf=True),
            lambda value: load_module(
                "post_release_consumer_audit_state_root_guard_test",
                runtime_dir / "post_release_consumer_audit.py",
            ).resolve_user_path(value, include_leaf=True),
            lambda value: load_module(
                "release_candidate_report_state_root_guard_test",
                runtime_dir / "release_candidate_report.py",
            ).resolve_user_path(value, include_leaf=True),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            real_dir = Path(temp_dir) / "real"
            real_dir.mkdir()
            link_dir = Path(temp_dir) / "link"
            link_dir.symlink_to(real_dir, target_is_directory=True)

            for helper in helper_calls:
                with self.assertRaisesRegex(ValueError, "symlink component"):
                    helper(str(link_dir))

    def test_runtime_child_dirs_refuse_symlink_leaves(self) -> None:
        from roundtable_core.runtime.state_store import create_run_dir

        room_runtime = load_module(
            "room_runtime_child_dir_guard_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "room_runtime.py",
        )
        debate_runtime = load_module(
            "debate_runtime_child_dir_guard_test",
            REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime" / "debate_runtime.py",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            state_root = Path(temp_dir) / "state"
            state_root.mkdir()
            victim = Path(temp_dir) / "victim"
            victim.mkdir()

            room_link = state_root / "room-safe-id"
            room_link.symlink_to(victim, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                room_runtime.ensure_directory(room_runtime.get_room_dir(state_root, "room-safe-id"))

            debate_link = state_root / "debate-safe-id"
            debate_link.symlink_to(victim, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                debate_runtime.ensure_directory(debate_runtime.get_debate_dir(state_root, "debate-safe-id"))

            runs_dir = state_root / "runs"
            runs_dir.mkdir()
            run_link = runs_dir / "demo-run"
            run_link.symlink_to(victim, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                create_run_dir(state_root, "room", run_id="demo-run")

    def test_resolve_checked_path_refuses_symlink_leaf(self) -> None:
        from roundtable_core.runtime.paths import resolve_checked_path

        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            with self.assertRaisesRegex(ValueError, "symlink component"):
                resolve_checked_path(output_json)

            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_user_output_paths_do_not_resolve_before_guard(self) -> None:
        checked_paths = [
            "scripts/check_agent_registry_sync.py",
            "scripts/check_skill_drift.py",
            "scripts/check_source_truth_consistency.py",
            "scripts/claim_boundary_dashboard.py",
            "scripts/run_regression_fixtures.py",
            "scripts/run_negative_fixtures.py",
            "evals/decision_quality/run_decision_evals.py",
            ".codex/skills/room-skill/runtime/generic_fixture_agent.py",
            ".codex/skills/room-skill/runtime/wrapper_fixture_agent.py",
            ".codex/skills/room-skill/runtime/chat_completions_executor.py",
            ".codex/skills/room-skill/runtime/generic_agent_json_wrapper.py",
            ".codex/skills/room-skill/runtime/local_codex_executor.py",
            ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py",
        ]
        forbidden = re.compile(
            r"Path\(args\.(?:output_json|output_markdown|output)\)\.expanduser\(\)\.resolve\(\)"
            r"|Path\(final_output\)\.expanduser\(\)\.resolve\(\)"
        )
        for rel_path in checked_paths:
            text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            self.assertIsNone(forbidden.search(text), rel_path)

    def test_runtime_run_ids_refuse_path_traversal(self) -> None:
        runtime_dir = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_run_id = "../escape"
            cases = [
                (
                    load_module(
                        "post_release_consumer_audit_run_id_guard_test",
                        runtime_dir / "post_release_consumer_audit.py",
                    ).build_report,
                    SimpleNamespace(
                        state_root=temp_dir,
                        run_id=invalid_run_id,
                        source=str(REPO_ROOT),
                        ref="HEAD",
                        quick=True,
                        timeout_seconds=1,
                        keep_worktree=False,
                    ),
                ),
                (
                    load_module(
                        "room_debate_e2e_validation_flow_id_guard_test",
                        runtime_dir / "room_debate_e2e_validation.py",
                    ).run_validation,
                    SimpleNamespace(state_root=temp_dir, flow_id=invalid_run_id),
                ),
                (
                    load_module(
                        "chat_completions_live_validation_run_id_guard_test",
                        runtime_dir / "chat_completions_live_validation.py",
                    ).run_validation,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
                (
                    load_module(
                        "chat_completions_regression_run_id_guard_test",
                        runtime_dir / "chat_completions_regression.py",
                    ).run_regression,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
                (
                    load_module(
                        "claude_code_live_validation_run_id_guard_test",
                        runtime_dir / "claude_code_live_validation.py",
                    ).run_validation,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
                (
                    load_module(
                        "local_codex_regression_run_id_guard_test",
                        runtime_dir / "local_codex_regression.py",
                    ).run_regression,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
                (
                    load_module(
                        "local_codex_second_host_validation_run_id_guard_test",
                        runtime_dir / "local_codex_second_host_validation.py",
                    ).run_validation,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
                (
                    load_module(
                        "local_codex_cross_machine_validation_run_id_guard_test",
                        runtime_dir / "local_codex_cross_machine_validation.py",
                    ).prepare_bundle,
                    SimpleNamespace(state_root=temp_dir, run_id=invalid_run_id),
                ),
            ]

            for func, args in cases:
                with self.assertRaisesRegex(ValueError, "path traversal"):
                    func(args)

    def test_source_boundary_audit_refuses_symlink_output_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            victim = Path(temp_dir) / "victim.json"
            victim.write_text("keep", encoding="utf-8")
            output_json = Path(temp_dir) / "out.json"
            output_json.symlink_to(victim)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "source_boundary_audit.py"),
                    "--output-json",
                    str(output_json),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("symlink component", completed.stderr)
            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

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

    def test_release_readiness_command_ok_requires_json_ok_true(self) -> None:
        module = load_module(
            "release_readiness_command_ok_gate_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "release_readiness_check.py",
        )

        rejected = [
            {"returncode": 0, "json_parse_ok": True, "json": {}},
            {"returncode": 0, "json_parse_ok": True, "json": {"ok": False}},
            {"returncode": 0, "json_parse_ok": False, "json": None},
            {"returncode": 1, "json_parse_ok": True, "json": {"ok": True}},
        ]
        for result in rejected:
            self.assertFalse(module.command_ok(result), result)

        self.assertTrue(module.command_ok({"returncode": 0, "json_parse_ok": True, "json": {"ok": True}}))

    def test_checked_in_host_live_evidence_defaults_to_historical_only(self) -> None:
        module = load_module(
            "release_readiness_historical_evidence_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "release_readiness_check.py",
        )
        report_path = REPO_ROOT / "reports" / "CLAUDE_CODE_HOST_LIVE_VALIDATION_2026-04-27.md"
        metadata = module.extract_checked_in_host_live_metadata(report_path.read_text(encoding="utf-8"), report_path)

        self.assertFalse(metadata["claimable"])
        self.assertEqual(metadata["evidence_status"], "historical_only")
        self.assertFalse(metadata["has_structured_provenance"])

    def test_secret_redaction_covers_common_sensitive_key_names(self) -> None:
        module = load_module(
            "secret_redaction_key_coverage_test",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "secret_redaction.py",
        )
        secret = "plainsecretvalue12345"
        payload = {
            "auth_bearer": secret,
            "authorization": secret,
            "access_token": secret,
            "refresh_token": secret,
            "client_secret": secret,
            "token_value": secret,
            "GITHUB_TOKEN": secret,
            "nested": [{"service_api_key": secret}],
            "argv": ["tool", "--client-secret", secret],
        }

        redacted = module.redact_sensitive_value(payload)
        text = str(redacted)
        self.assertNotIn(secret, text)
        self.assertIn("[REDACTED]", text)


def load_module(name: str, path: Path) -> object:
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
