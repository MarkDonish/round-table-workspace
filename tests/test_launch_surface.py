from __future__ import annotations

import json
import unittest
import importlib.util
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
from types import SimpleNamespace

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
        self.assertIn('property="og:title"', text)
        self.assertIn('name="twitter:card"', text)
        self.assertIn('name="theme-color"', text)
        self.assertNotIn("<script", text.lower())

    def test_credits_application_answers_exist_and_are_linked(self) -> None:
        answers = REPO_ROOT / "docs" / "credits-application-answers.md"
        packet = REPO_ROOT / "docs" / "application-packet.md"
        self.assertTrue(answers.exists())
        text = answers.read_text(encoding="utf-8")
        self.assertIn("# Credits Application Answers", text)
        self.assertIn("## Short project description", text)
        self.assertIn("## What will you use the credits for?", text)
        self.assertIn("fixture-backed", text)
        self.assertIn("provider-live", text)
        self.assertIn("No host-live or provider-live support is claimed", text)
        self.assertIn("docs/credits-application-answers.md", packet.read_text(encoding="utf-8"))

    def test_reviewer_checklist_exists_and_is_linked_from_public_surfaces(self) -> None:
        checklist = REPO_ROOT / "docs" / "reviewer-checklist.md"
        packet = REPO_ROOT / "docs" / "application-packet.md"
        answers = REPO_ROOT / "docs" / "credits-application-answers.md"
        index = REPO_ROOT / "docs" / "index.html"

        self.assertTrue(checklist.exists())
        text = checklist.read_text(encoding="utf-8")
        self.assertIn("# Reviewer Checklist", text)
        self.assertIn("## 2-minute review path", text)
        self.assertIn("## Evidence matrix", text)
        self.assertIn("python3 -m unittest discover -v", text)
        self.assertIn("No host-live or provider-live support is claimed", text)
        for surface in (packet, answers, index):
            self.assertIn("reviewer-checklist", surface.read_text(encoding="utf-8"))

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
        self.assertIn("docs/application-packet.md", payload["assets"])
        self.assertIn("docs/credits-application-answers.md", payload["assets"])
        self.assertIn("docs/reviewer-checklist.md", payload["assets"])
        self.assertIn("docs/competitive-insights.md", payload["assets"])
        self.assertIn("application_packet", payload)
        self.assertIn("reviewer_checklist", payload)
        self.assertEqual(
            payload["reviewer_checklist"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/reviewer-checklist.md",
        )
        self.assertIn("credits_application_answers", payload)
        self.assertEqual(
            payload["credits_application_answers"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/credits-application-answers.md",
        )
        self.assertEqual(
            payload["application_packet"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/application-packet.md",
        )
        self.assertEqual(
            payload["competitive_insights"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/competitive-insights.md",
        )
        self.assertIn("Make your AI agents argue", payload["positioning"])
        self.assertEqual(payload["missing_assets"], [])
        for item in payload["asset_status"]:
            self.assertTrue(item["exists"], item["path"])

        summary_path = REPO_ROOT / ".tmp-launch-kit-summary.md"
        try:
            summary_code, _summary_stdout = self.invoke(["launch-kit", "--output-markdown", str(summary_path), "--quiet"])
            self.assertEqual(summary_code, 0)
            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Application packet", summary)
            self.assertIn("Competitive insights", summary)
            self.assertIn("docs/application-packet.md", summary)
        finally:
            summary_path.unlink(missing_ok=True)

    def test_competitive_insights_doc_is_original_and_source_attributed(self) -> None:
        insights = REPO_ROOT / "docs" / "competitive-insights.md"
        packet = REPO_ROOT / "docs" / "application-packet.md"
        answers = REPO_ROOT / "docs" / "credits-application-answers.md"
        index = REPO_ROOT / "docs" / "index.html"

        self.assertTrue(insights.exists())
        text = insights.read_text(encoding="utf-8")
        self.assertIn("# Competitive Insights", text)
        self.assertIn("## What we learned without copying code", text)
        self.assertIn("## Differentiation for Round Table Workspace", text)
        self.assertIn("addyosmani/agent-skills", text)
        self.assertIn("FoundationAgents/MetaGPT", text)
        self.assertIn("camel-ai/camel", text)
        self.assertIn("pydantic/pydantic-ai", text)
        self.assertIn("plandex-ai/plandex", text)
        self.assertIn("No source code was copied", text)
        self.assertIn("fixture-backed", text)
        for surface in (packet, answers, index):
            self.assertIn("competitive-insights", surface.read_text(encoding="utf-8"))

    def test_next_release_notes_exist_and_readme_names_current_release(self) -> None:
        release_note = REPO_ROOT / "docs" / "releases" / "v0.2.2-pages-launch-kit.md"
        self.assertTrue(release_note.exists())
        note = release_note.read_text(encoding="utf-8")
        self.assertIn("GitHub Pages", note)
        self.assertIn("launch-kit", note)

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("v0.2.2-pages-launch-kit", readme)

    def test_github_release_publication_defaults_follow_current_release(self) -> None:
        publication_check = self.load_module(
            "github_release_publication_check",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "github_release_publication_check.py",
        )
        release_extractor = self.load_module(
            "extract_github_release_body",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "extract_github_release_body.py",
        )
        draft = REPO_ROOT / "docs" / "releases" / "v0.2.2-pages-launch-kit-github-release.md"

        self.assertTrue(draft.exists())
        self.assertEqual(publication_check.DEFAULT_TAG, "v0.2.2-pages-launch-kit")
        self.assertEqual(
            publication_check.DEFAULT_RELEASE_DRAFT,
            "docs/releases/v0.2.2-pages-launch-kit-github-release.md",
        )
        self.assertEqual(
            release_extractor.DEFAULT_RELEASE_DRAFT,
            "docs/releases/v0.2.2-pages-launch-kit-github-release.md",
        )
        extraction = release_extractor.build_report(
            SimpleNamespace(
                release_draft=release_extractor.DEFAULT_RELEASE_DRAFT,
                output="/tmp/rtw-test-release-body.md",
                output_json=None,
            )
        )
        self.assertTrue(extraction["ok"], extraction)

        workflow_check = publication_check.check_release_workflow(
            publication_check.DEFAULT_RELEASE_WORKFLOW,
            expected_tag=publication_check.DEFAULT_TAG,
            expected_release_draft=publication_check.DEFAULT_RELEASE_DRAFT,
        )
        self.assertTrue(workflow_check["defaults_match_requested_release"])
        self.assertEqual(workflow_check["default_tag"], "v0.2.2-pages-launch-kit")
        self.assertEqual(
            workflow_check["default_release_draft"],
            "docs/releases/v0.2.2-pages-launch-kit-github-release.md",
        )
        self.assertEqual(workflow_check["default_dry_run"], "false")
        self.assertTrue(workflow_check["publication_safe"])
        self.assertFalse(workflow_check["push_trigger_can_publish"])
        self.assertTrue(workflow_check["has_tag_checkout_guard"])
        self.assertTrue(workflow_check["watches_gate_scripts"])

    def test_release_publication_paths_are_repo_bounded(self) -> None:
        publication_check = self.load_module(
            "github_release_publication_check_paths",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "github_release_publication_check.py",
        )
        release_extractor = self.load_module(
            "extract_github_release_body_paths",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "extract_github_release_body.py",
        )

        extraction = release_extractor.build_report(
            SimpleNamespace(release_draft="../README.md", output="/tmp/rtw-test-release-body.md", output_json=None)
        )
        self.assertFalse(extraction["ok"])
        self.assertEqual(extraction["error"], "release_draft_outside_repo")

        absolute_extraction = release_extractor.build_report(
            SimpleNamespace(release_draft="/tmp/README.md", output="/tmp/rtw-test-release-body.md", output_json=None)
        )
        self.assertFalse(absolute_extraction["ok"])
        self.assertEqual(absolute_extraction["error"], "release_draft_must_be_repo_relative")

        draft_check = publication_check.check_release_draft("../README.md")
        self.assertFalse(draft_check["exists"])
        self.assertFalse(draft_check["within_repo"])
        self.assertEqual(draft_check["error"], "release_draft_outside_repo")

        workflow_check = publication_check.check_release_workflow("../publish.yml")
        self.assertFalse(workflow_check["usable"])
        self.assertFalse(workflow_check["within_repo"])
        self.assertEqual(workflow_check["error"], "release_workflow_outside_repo")

    def test_publish_release_workflow_dry_run_does_not_swallow_gh_errors(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "publish-github-release.yml").read_text(encoding="utf-8")

        self.assertNotIn("gh release view \"$TAG\" --repo \"$GITHUB_REPOSITORY\" \\\n            --json tagName,name,isDraft,isPrerelease,publishedAt,targetCommitish,url || true", workflow)
        self.assertIn('release_view_status=$?', workflow)
        self.assertIn('release_view_status":"not_found"', workflow)
        self.assertIn('exit "$release_view_status"', workflow)
        self.assertIn("Verify checkout matches release tag", workflow)
        self.assertIn('tag_commit="$(git rev-list -n 1 "$TAG")"', workflow)
        self.assertIn("release checkout does not match tag", workflow)
        for path in [
            ".codex/skills/room-skill/runtime/github_release_publication_check.py",
            "scripts/check_source_truth_consistency.py",
            "scripts/release_check.py",
        ]:
            self.assertIn(path, workflow)

    def test_ci_release_check_uses_strict_clean_gate_and_read_permissions(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("./rtw release-check --include-fixtures --strict-git-clean", workflow)

    def test_source_truth_accepts_safe_release_workflow_defaults(self) -> None:
        from scripts import check_source_truth_consistency

        report = check_source_truth_consistency.build_report()

        release_defaults = report["checks"]["release_publication_defaults"]
        self.assertTrue(release_defaults["ok"], release_defaults)
        self.assertEqual(release_defaults["workflow_default_tag"], "v0.2.2-pages-launch-kit")
        self.assertEqual(
            release_defaults["workflow_default_release_draft"],
            "docs/releases/v0.2.2-pages-launch-kit-github-release.md",
        )
        self.assertFalse(release_defaults["workflow_push_trigger_can_publish"])
        self.assertTrue(release_defaults["workflow_has_tag_checkout_guard"])
        self.assertTrue(release_defaults["workflow_watches_gate_scripts"])
        self.assertEqual(release_defaults["problems"], [])

    def test_source_truth_requires_fresh_claim_dashboard(self) -> None:
        from scripts import check_source_truth_consistency

        report = check_source_truth_consistency.build_report()

        freshness = report["checks"]["claim_dashboard_freshness"]
        self.assertTrue(freshness["ok"], freshness)
        self.assertEqual(freshness["problems"], [])
        self.assertIsNotNone(freshness["stale_after"])
        self.assertRegex(freshness["source_commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(freshness["source_commit_is_ancestor"], freshness)

    @staticmethod
    def load_module(name: str, path: Path) -> object:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
