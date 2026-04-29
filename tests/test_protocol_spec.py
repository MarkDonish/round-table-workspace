from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "docs" / "protocol-spec.md"


class ProtocolSpecTest(unittest.TestCase):
    def test_protocol_spec_exists_and_links_core_protocols(self) -> None:
        self.assertTrue(SPEC_PATH.exists())
        text = SPEC_PATH.read_text(encoding="utf-8")
        for expected in [
            "docs/room-architecture.md",
            "docs/debate-skill-architecture.md",
            "docs/room-to-debate-handoff.md",
            "docs/room-chat-contract.md",
            "docs/reviewer-protocol.md",
            "docs/release-candidate-scope.md",
        ]:
            self.assertIn(expected, text)

    def test_protocol_spec_covers_required_runtime_contracts(self) -> None:
        text = SPEC_PATH.read_text(encoding="utf-8")
        for expected in [
            "/room State Machine",
            "/debate State Machine",
            "/room -> /debate Handoff Contract",
            "Session State Fields",
            "Output Contracts",
            "Failure And Recovery",
            "Explicit-Only Trigger Rule",
            "Claim-Safe Support Boundary",
            "provider-live",
            "host-live",
        ]:
            self.assertIn(expected, text)

    def test_readme_links_to_protocol_spec(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/protocol-spec.md", readme)


if __name__ == "__main__":
    unittest.main()
