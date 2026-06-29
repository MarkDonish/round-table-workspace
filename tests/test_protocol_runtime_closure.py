from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from roundtable_core.protocol.handoff import portable_handoff_to_runtime_packet, runtime_packet_to_portable_handoff
from roundtable_core.protocol.projections import (
    project_debate_artifacts_to_result,
    project_debate_artifacts_to_session,
    project_room_state_to_session,
)
from roundtable_core.validation import validate_file


REPO_ROOT = Path(__file__).resolve().parents[1]


class ProtocolRuntimeClosureTest(unittest.TestCase):
    def test_legacy_handoff_round_trips_to_portable_schema(self) -> None:
        legacy = json.loads(
            (
                REPO_ROOT
                / ".codex"
                / "skills"
                / "room-skill"
                / "runtime"
                / "fixtures"
                / "canonical"
                / "upgrade.json"
            ).read_text(encoding="utf-8")
        )
        portable = runtime_packet_to_portable_handoff(legacy)
        round_tripped = portable_handoff_to_runtime_packet(portable)

        self.assertEqual(portable["schema_version"], "0.1.0")
        self.assertEqual(round_tripped["schema_version"], "v0.1")
        self.assertEqual(round_tripped["source_room_id"], portable["source_room_session_id"])

    def test_room_runtime_projects_to_portable_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/room-skill/runtime/room_runtime.py",
                    "validate-canonical",
                    "--state-root",
                    temp_dir,
                    "--room-id",
                    "room-projection-test",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            room_state = json.loads(Path(report["state_path"]).read_text(encoding="utf-8"))
            projection = project_room_state_to_session(room_state, report["artifacts"])
            projection_path = Path(temp_dir) / "room-session.json"
            projection_path.write_text(json.dumps(projection, ensure_ascii=False, indent=2), encoding="utf-8")
            validation = validate_file(
                schema_path=REPO_ROOT / "schemas" / "room-session.schema.json",
                instance_path=projection_path,
            )
            self.assertTrue(validation.ok, validation.errors)

    def test_room_runtime_rejects_unsafe_room_id_path_segment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/room-skill/runtime/room_runtime.py",
                    "validate-canonical",
                    "--state-root",
                    temp_dir,
                    "--room-id",
                    "../escape",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("room_id must not contain path traversal", payload["error"])
            self.assertFalse((Path(temp_dir).parent / "escape").exists())

    def test_room_runtime_refuses_symlink_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            real_dir = base / "real"
            real_dir.mkdir()
            link_dir = base / "link"
            link_dir.symlink_to(real_dir, target_is_directory=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/room-skill/runtime/room_runtime.py",
                    "validate-canonical",
                    "--state-root",
                    str(base / "missing" / ".." / "link"),
                    "--room-id",
                    "room-symlink-test",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("symlink component", payload["error"])
            self.assertFalse((real_dir / "room-symlink-test").exists())

    def test_debate_runtime_projects_to_portable_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py",
                    "validate-canonical-execution",
                    "--state-root",
                    temp_dir,
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            artifacts = {
                "launch_bundle": report["artifacts"]["launch_bundle"],
                "roundtable_record": report["artifacts"]["roundtable_record"],
                "review_packet": report["artifacts"]["review_packet"],
                "review_result": report["artifacts"]["review_result"],
                "legacy_handoff_packet": str(
                    REPO_ROOT
                    / ".codex"
                    / "skills"
                    / "room-skill"
                    / "runtime"
                    / "fixtures"
                    / "canonical"
                    / "upgrade.json"
                ),
            }
            session = project_debate_artifacts_to_session(artifacts)
            result = project_debate_artifacts_to_result(artifacts)
            session_path = Path(temp_dir) / "debate-session.json"
            result_path = Path(temp_dir) / "debate-result.json"
            session_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

            session_validation = validate_file(
                schema_path=REPO_ROOT / "schemas" / "debate-session.schema.json",
                instance_path=session_path,
            )
            result_validation = validate_file(
                schema_path=REPO_ROOT / "schemas" / "debate-result.schema.json",
                instance_path=result_path,
            )
            self.assertTrue(session_validation.ok, session_validation.errors)
            self.assertTrue(result_validation.ok, result_validation.errors)

    def test_debate_runtime_rejects_unsafe_debate_id_path_segment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py",
                    "build-launch-bundle",
                    "--packet-json",
                    str(
                        REPO_ROOT
                        / ".codex"
                        / "skills"
                        / "room-skill"
                        / "runtime"
                        / "fixtures"
                        / "canonical"
                        / "upgrade.json"
                    ),
                    "--state-root",
                    temp_dir,
                    "--debate-id",
                    "../escape",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("debate_id must not contain path traversal", payload["error"])
            self.assertFalse((Path(temp_dir).parent / "escape").exists())

    def test_debate_runtime_refuses_symlink_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            real_dir = base / "real"
            real_dir.mkdir()
            link_dir = base / "link"
            link_dir.symlink_to(real_dir, target_is_directory=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    ".codex/skills/debate-roundtable-skill/runtime/debate_runtime.py",
                    "validate-canonical-execution",
                    "--state-root",
                    str(base / "missing" / ".." / "link"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("symlink component", payload["error"])
            self.assertFalse((real_dir / "debate-canonical-execution").exists())


if __name__ == "__main__":
    unittest.main()
