from __future__ import annotations

import json
import unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

REPO_ROOT = Path(__file__).resolve().parents[1]


class LaunchSurfaceTest(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, str]:
        from roundtable import cli

        stdout = StringIO()
        with redirect_stdout(stdout):
            code = cli.main(argv)
        return code, stdout.getvalue()

    def test_docs_index_html_is_static_launch_landing_page(self) -> None:
        page = REPO_ROOT / "docs" / "index.html"
        self.assertTrue(page.exists())
        text = page.read_text(encoding="utf-8")
        self.assertIn("Make your AI agents argue before they ship", text)
        self.assertIn("./rtw ship-check", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertNotIn("<script", text.lower())

    def test_readme_and_launch_copy_point_to_pages_demo(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        launch_copy = (REPO_ROOT / "docs" / "launch-copy.md").read_text(encoding="utf-8")
        pages_url = "https://markdonish.github.io/round-table-workspace/"
        self.assertIn(pages_url, readme)
        self.assertIn(pages_url, launch_copy)

    def test_pages_launch_surface_has_manual_publish_instructions(self) -> None:
        release_note = REPO_ROOT / "docs" / "releases" / "v0.2.2-pages-launch-kit.md"
        note = release_note.read_text(encoding="utf-8")
        self.assertIn("GitHub Pages", note)
        self.assertIn("main branch /docs folder", note)

    def test_launch_kit_outputs_copy_assets_and_topics(self) -> None:
        code, output = self.invoke(["launch-kit", "--json"])

        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["action"], "launch-kit")
        self.assertEqual(payload["pages_url"], "https://markdonish.github.io/round-table-workspace/")
        self.assertIn("docs/launch-copy.md", payload["assets"])
        self.assertIn("docs/index.html", payload["assets"])
        self.assertIn("ai-agents", payload["topics"])
        self.assertIn("Make your AI agents argue", payload["positioning"])

    def test_next_release_notes_exist_and_readme_names_current_release(self) -> None:
        release_note = REPO_ROOT / "docs" / "releases" / "v0.2.2-pages-launch-kit.md"
        self.assertTrue(release_note.exists())
        note = release_note.read_text(encoding="utf-8")
        self.assertIn("GitHub Pages", note)
        self.assertIn("launch-kit", note)

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("v0.2.2-pages-launch-kit", readme)
