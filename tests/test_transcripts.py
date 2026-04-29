from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "This is an illustrative transcript, not host-live or provider-live validation evidence."
TRANSCRIPTS = [
    "examples/transcripts/room-startup-idea.md",
    "examples/transcripts/debate-mvp-decision.md",
    "examples/transcripts/room-to-debate-handoff.md",
]


class TranscriptExamplesTest(unittest.TestCase):
    def test_transcript_examples_exist_with_claim_safe_disclaimer(self) -> None:
        for transcript in TRANSCRIPTS:
            path = REPO_ROOT / transcript
            self.assertTrue(path.exists(), transcript)
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first_line, DISCLAIMER)

    def test_readme_links_to_transcript_examples(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("examples/transcripts/", readme)


if __name__ == "__main__":
    unittest.main()
