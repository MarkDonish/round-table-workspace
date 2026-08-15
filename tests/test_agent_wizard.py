from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.agents.wizard import create_agent_bundle


class AgentWizardTest(unittest.TestCase):
    def test_create_agent_bundle_in_temp_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            (temp_root / "agents").mkdir(parents=True, exist_ok=True)
            (temp_root / "agents" / "registry.json").write_text(
                json.dumps({"registry_kind": "agent_factory_library", "agents": []}, indent=2),
                encoding="utf-8",
            )

            res = create_agent_bundle(
                agent_id="test-architect",
                display_name="Test Architect",
                short_name="Architect",
                structural_role="defensive",
                strength="Distributed systems and resilience",
                repo_root=temp_root,
            )
            self.assertTrue(res["ok"])
            self.assertEqual(res["agent_id"], "test-architect")
            self.assertTrue(Path(res["manifest_path"]).exists())
            self.assertTrue(Path(res["profile_path"]).exists())

            # Verify manifest content
            manifest = json.loads(Path(res["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["agent_id"], "test-architect")
            self.assertEqual(manifest["display_name"], "Test Architect")
            self.assertEqual(manifest["structural_role"], "defensive")


if __name__ == "__main__":
    unittest.main()
