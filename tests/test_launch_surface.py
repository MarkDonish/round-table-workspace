from __future__ import annotations

import json
import unittest
import importlib.util
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

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
        self.assertIn("Why star Round Table Workspace", text)
        self.assertIn("Who it is for", text)
        self.assertIn("What it catches", text)
        self.assertIn("Why it is different", text)
        self.assertIn("product, engineering, risk, and user perspectives", text)
        self.assertIn("ai-generated-feature-review-demo.html", text)
        self.assertIn("./one-minute-demo.html", text)
        self.assertIn("./quick-evaluation.md", text)
        self.assertIn("5-minute evaluation", text)
        self.assertIn("./use-cases.html", text)
        self.assertIn("./repo-card.html", text)
        self.assertIn('property="og:title"', text)
        self.assertIn('property="og:image"', text)
        self.assertIn('name="twitter:card"', text)
        self.assertIn('name="twitter:image"', text)
        self.assertIn('name="theme-color"', text)
        self.assertIn('href="./sitemap.xml"', text)
        self.assertIn('href="./llms.txt"', text)
        self.assertNotIn("<script", text.lower())

    def test_ai_generated_feature_review_demo_is_pages_ready(self) -> None:
        page = REPO_ROOT / "docs" / "ai-generated-feature-review-demo.html"
        markdown = REPO_ROOT / "docs" / "ai-generated-feature-review-demo.md"
        self.assertTrue(page.exists())
        self.assertTrue(markdown.exists())
        text = page.read_text(encoding="utf-8")
        self.assertIn("Review AI-generated work before you trust it", text)
        self.assertIn("Decision: revise", text)
        self.assertIn("Star on GitHub", text)
        self.assertIn('property="og:image"', text)
        self.assertIn('name="twitter:image"', text)
        self.assertIn('name="twitter:card" content="summary_large_image"', text)
        self.assertIn('href="./sitemap.xml"', text)
        self.assertIn('href="./llms.txt"', text)
        self.assertIn("This is an illustrative transcript, not host-live or provider-live validation evidence.", text)
        self.assertIn("./ai-generated-feature-review-demo.md", text)
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

    def test_readme_explains_before_after_review_value(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## What Changes", readme)
        self.assertIn("Without a review gate", readme)
        self.assertIn("AI agent: The feature is implemented and ready to merge.", readme)
        self.assertIn("ship-check: revise", readme)
        self.assertIn("Product: the user value is still vague", readme)
        self.assertIn("Risk: the launch claim needs current evidence", readme)
        self.assertIn("a repeatable pause", readme)

    def test_readme_surfaces_star_decision_before_long_overview(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        star_cta = "**Star this repo if you want a local-first review gate"
        overview = "Round Table Workspace is a local-first decision layer"
        self.assertIn(star_cta, readme)
        self.assertIn("[60-second demo]", readme)
        self.assertIn("[AI feature review example]", readme)
        self.assertIn("[5-minute evaluation path](docs/quick-evaluation.md)", readme)
        self.assertIn("[repo preview card]", readme)
        self.assertIn("[why this is worth starring](docs/why-star-this-repo.md)", readme)
        self.assertIn("No provider key is required for the default demo path.", readme)
        self.assertLess(readme.index(star_cta), readme.index(overview))

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
        self.assertEqual(payload["repo_card"], "https://markdonish.github.io/round-table-workspace/repo-card.html")
        self.assertEqual(payload["repo_card_image"], "https://markdonish.github.io/round-table-workspace/repo-card.png")
        self.assertEqual(
            payload["one_minute_demo_card"],
            "https://markdonish.github.io/round-table-workspace/one-minute-demo-card.html",
        )
        self.assertEqual(
            payload["one_minute_demo_card_image"],
            "https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png",
        )
        for topic in ("ai-code-review", "agentic-workflow", "ship-check", "round-table"):
            self.assertIn(topic, payload["topics"])
        self.assertIn("docs/launch-copy.md", payload["assets"])
        self.assertIn("docs/robots.txt", payload["assets"])
        self.assertIn("docs/sitemap.xml", payload["assets"])
        self.assertIn("docs/llms.txt", payload["assets"])
        self.assertIn("docs/one-minute-demo.html", payload["assets"])
        self.assertIn("docs/one-minute-demo-card.html", payload["assets"])
        self.assertIn("docs/one-minute-demo-card.png", payload["assets"])
        self.assertIn("docs/one-minute-demo.md", payload["assets"])
        self.assertIn("docs/quick-evaluation.md", payload["assets"])
        self.assertIn("docs/use-cases.html", payload["assets"])
        self.assertIn("docs/use-cases.md", payload["assets"])
        self.assertIn("docs/repo-card.html", payload["assets"])
        self.assertIn("docs/repo-card.png", payload["assets"])
        self.assertIn("docs/community-share-kit.md", payload["assets"])
        self.assertIn("docs/directory-submission-kit.md", payload["assets"])
        self.assertIn("docs/distribution-checklist.md", payload["assets"])
        self.assertIn("docs/public-submission-targets.md", payload["assets"])
        self.assertIn("docs/developer-forum-feedback-kit.md", payload["assets"])
        self.assertIn("docs/show-hn-submission-draft.md", payload["assets"])
        self.assertIn("docs/newsletter-roundup-pitch-kit.md", payload["assets"])
        self.assertIn("docs/product-hunt-launch-kit.md", payload["assets"])
        self.assertIn("docs/promotion-feedback-template.md", payload["assets"])
        self.assertIn("docs/comparison-guide.md", payload["assets"])
        self.assertIn("docs/ai-failure-modes.md", payload["assets"])
        self.assertIn("docs/demo-recording-guide.md", payload["assets"])
        self.assertIn("docs/short-video-script-kit.md", payload["assets"])
        self.assertIn("examples/transcripts/ship-check-architecture-decision.md", payload["assets"])
        self.assertIn(".github/ISSUE_TEMPLATE/workflow_example.yml", payload["assets"])
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
        self.assertIn("community_share_kit", payload)
        self.assertEqual(
            payload["community_share_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/community-share-kit.md",
        )
        self.assertIn("quick_evaluation", payload)
        self.assertEqual(
            payload["quick_evaluation"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/quick-evaluation.md",
        )
        self.assertIn("directory_submission_kit", payload)
        self.assertEqual(
            payload["directory_submission_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/directory-submission-kit.md",
        )
        self.assertIn("distribution_checklist", payload)
        self.assertEqual(
            payload["distribution_checklist"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/distribution-checklist.md",
        )
        self.assertIn("public_submission_targets", payload)
        self.assertEqual(
            payload["public_submission_targets"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/public-submission-targets.md",
        )
        self.assertIn("developer_forum_feedback_kit", payload)
        self.assertEqual(
            payload["developer_forum_feedback_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/developer-forum-feedback-kit.md",
        )
        self.assertIn("show_hn_submission_draft", payload)
        self.assertEqual(
            payload["show_hn_submission_draft"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/show-hn-submission-draft.md",
        )
        self.assertIn("newsletter_roundup_pitch_kit", payload)
        self.assertEqual(
            payload["newsletter_roundup_pitch_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/newsletter-roundup-pitch-kit.md",
        )
        self.assertIn("product_hunt_launch_kit", payload)
        self.assertEqual(
            payload["product_hunt_launch_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/product-hunt-launch-kit.md",
        )
        self.assertIn("promotion_feedback_template", payload)
        self.assertEqual(
            payload["promotion_feedback_template"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/promotion-feedback-template.md",
        )
        self.assertIn("comparison_guide", payload)
        self.assertEqual(
            payload["comparison_guide"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/comparison-guide.md",
        )
        self.assertIn("ai_failure_modes", payload)
        self.assertEqual(
            payload["ai_failure_modes"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/ai-failure-modes.md",
        )
        self.assertIn("demo_recording_guide", payload)
        self.assertEqual(
            payload["demo_recording_guide"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/demo-recording-guide.md",
        )
        self.assertIn("short_video_script_kit", payload)
        self.assertEqual(
            payload["short_video_script_kit"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/docs/short-video-script-kit.md",
        )
        self.assertIn("architecture_decision_transcript", payload)
        self.assertEqual(
            payload["architecture_decision_transcript"],
            "https://github.com/MarkDonish/round-table-workspace/blob/main/examples/transcripts/ship-check-architecture-decision.md",
        )
        self.assertIn("workflow_example_issue", payload)
        self.assertEqual(
            payload["workflow_example_issue"],
            "https://github.com/MarkDonish/round-table-workspace/issues/new?template=workflow_example.yml",
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
            self.assertIn("Repo card", summary)
            self.assertIn("Repo card image", summary)
            self.assertIn("Competitive insights", summary)
            self.assertIn("Community share kit", summary)
            self.assertIn("Quick evaluation path", summary)
            self.assertIn("Directory submission kit", summary)
            self.assertIn("Distribution checklist", summary)
            self.assertIn("Public submission targets", summary)
            self.assertIn("Developer forum feedback kit", summary)
            self.assertIn("Show HN submission draft", summary)
            self.assertIn("Newsletter roundup pitch kit", summary)
            self.assertIn("Product Hunt launch kit", summary)
            self.assertIn("Promotion feedback template", summary)
            self.assertIn("Comparison guide", summary)
            self.assertIn("AI failure modes", summary)
            self.assertIn("Demo recording guide", summary)
            self.assertIn("Short video script kit", summary)
            self.assertIn("Architecture decision transcript", summary)
            self.assertIn("Workflow example issue form", summary)
            self.assertIn("docs/application-packet.md", summary)
        finally:
            summary_path.unlink(missing_ok=True)

    def test_quick_evaluation_path_is_claim_safe_and_linked(self) -> None:
        quick_eval = REPO_ROOT / "docs" / "quick-evaluation.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(quick_eval.exists())
        text = quick_eval.read_text(encoding="utf-8")
        self.assertIn("# Quick Evaluation Path", text)
        self.assertIn("5-Minute Local Trial", text)
        self.assertIn("./rtw ship-check \"Should we merge this AI-generated feature?\"", text)
        self.assertIn("./rtw doctor --quick", text)
        self.assertIn("No provider key is required", text)
        self.assertIn("Star the repo if", text)
        self.assertIn("Skip For Now If", text)
        self.assertIn("universal live support for every local agent host", text)
        self.assertIn("provider-live", text)
        self.assertIn("fresh evidence", text)

        for surface in (readme, docs_index, launch_copy, llms):
            self.assertIn("docs/quick-evaluation.md", surface.read_text(encoding="utf-8"))

    def test_community_share_kit_is_claim_safe_and_linked(self) -> None:
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"

        self.assertTrue(share_kit.exists())
        text = share_kit.read_text(encoding="utf-8")
        self.assertIn("# Community Share Kit", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/ai-generated-feature-review-demo.html", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/repo-card.html", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/repo-card.png", text)
        self.assertIn("docs/public-submission-targets.md", text)
        self.assertIn("./rtw ship-check \"Should we merge this AI-generated feature?\"", text)
        self.assertIn("## Real-World Failure Mode To Share", text)
        self.assertIn("An AI coding agent adds a database migration", text)
        self.assertIn("whether the migration can roll back", text)
        self.assertIn("Expected result for this example is usually `revise`", text)
        self.assertIn("No host-live or provider-live support is claimed without current evidence.", text)
        self.assertIn("The workflow helps review AI-generated work; it does not guarantee correctness.", text)

        for surface in (readme, docs_index, launch_copy):
            self.assertIn("docs/community-share-kit.md", surface.read_text(encoding="utf-8"))

    def test_directory_submission_kit_is_claim_safe_and_linked(self) -> None:
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        recording_guide = REPO_ROOT / "docs" / "demo-recording-guide.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(submission_kit.exists())
        text = submission_kit.read_text(encoding="utf-8")
        self.assertIn("# Directory Submission Kit", text)
        self.assertIn("Round Table Workspace", text)
        self.assertIn("Make your AI coding agents argue before they ship.", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/repo-card.html", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/repo-card.png", text)
        self.assertIn("docs/public-submission-targets.md", text)
        self.assertIn("host-live or provider-live", text)
        self.assertIn("Do not claim", text)
        self.assertIn("Submission Checklist", text)

        for surface in (readme, docs_index, launch_copy, share_kit, llms):
            self.assertIn("docs/directory-submission-kit.md", surface.read_text(encoding="utf-8"))

    def test_distribution_checklist_is_claim_safe_and_linked(self) -> None:
        checklist = REPO_ROOT / "docs" / "distribution-checklist.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(checklist.exists())
        text = checklist.read_text(encoding="utf-8")
        self.assertIn("# Distribution Checklist", text)
        self.assertIn("Submission Order", text)
        self.assertIn("Hacker News / Show HN", text)
        self.assertIn("Open-source directories and tool lists", text)
        self.assertIn("GitHub repository as the first URL", text)
        self.assertIn("repo-card.html", text)
        self.assertIn("repo-card.png", text)
        self.assertIn("docs/public-submission-targets.md", text)
        self.assertIn("docs/show-hn-submission-draft.md", text)
        self.assertIn("docs/newsletter-roundup-pitch-kit.md", text)
        self.assertIn("docs/product-hunt-launch-kit.md", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("Do not claim host-live or provider-live support without fresh evidence.", text)
        self.assertIn("72h result", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, llms):
            self.assertIn("docs/distribution-checklist.md", surface.read_text(encoding="utf-8"))

    def test_public_submission_targets_are_claim_safe_and_linked(self) -> None:
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(targets.exists())
        text = targets.read_text(encoding="utf-8")
        self.assertIn("# Public Submission Targets", text)
        self.assertIn("Verified: 2026-07-02.", text)
        self.assertIn("Hacker News / Show HN", text)
        self.assertIn("https://news.ycombinator.com/submit", text)
        self.assertIn("docs/show-hn-submission-draft.md", text)
        self.assertIn("docs/newsletter-roundup-pitch-kit.md", text)
        self.assertIn("Product Hunt", text)
        self.assertIn("docs/product-hunt-launch-kit.md", text)
        self.assertIn("https://www.producthunt.com/launch", text)
        self.assertIn("DevHunt", text)
        self.assertIn("https://devhunt.org/", text)
        self.assertIn("Do not publish a second public campaign from the same angle until the 72-hour", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("It does not add", text)
        self.assertIn("host-live or provider-live support", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, distribution, llms):
            self.assertIn("docs/public-submission-targets.md", surface.read_text(encoding="utf-8"))

    def test_show_hn_submission_draft_is_claim_safe_and_linked(self) -> None:
        show_hn = REPO_ROOT / "docs" / "show-hn-submission-draft.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(show_hn.exists())
        text = show_hn.read_text(encoding="utf-8")
        self.assertIn("# Show HN Submission Draft", text)
        self.assertIn("https://news.ycombinator.com/submit", text)
        self.assertIn("Show HN: Round Table Workspace", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("Do not ask for upvotes.", text)
        self.assertIn("Do not coordinate comments or votes.", text)
        self.assertIn("Do not submit before the 72-hour X feedback is reviewed.", text)
        self.assertIn("fixture-backed", text)
        self.assertIn("host-live or provider-live support", text)
        self.assertIn("Reply Bank", text)
        self.assertIn("ship, revise, or reject", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, distribution, targets, llms):
            self.assertIn("docs/show-hn-submission-draft.md", surface.read_text(encoding="utf-8"))

    def test_newsletter_roundup_pitch_kit_is_claim_safe_and_linked(self) -> None:
        pitch_kit = REPO_ROOT / "docs" / "newsletter-roundup-pitch-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(pitch_kit.exists())
        text = pitch_kit.read_text(encoding="utf-8")
        self.assertIn("# Newsletter And Roundup Pitch Kit", text)
        self.assertIn("Do not send these pitches before the 72-hour X feedback", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", text)
        self.assertIn("Subject Lines", text)
        self.assertIn("Editor Email", text)
        self.assertIn("Roundup Listing", text)
        self.assertIn("Follow-Up Reply", text)
        self.assertIn("host-live or provider-live support claims", text)
        self.assertIn("Do not send the same copy to every publication.", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, distribution, targets, llms):
            self.assertIn("docs/newsletter-roundup-pitch-kit.md", surface.read_text(encoding="utf-8"))

    def test_product_hunt_launch_kit_is_claim_safe_and_linked(self) -> None:
        product_hunt = REPO_ROOT / "docs" / "product-hunt-launch-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(product_hunt.exists())
        text = product_hunt.read_text(encoding="utf-8")
        self.assertIn("# Product Hunt Launch Kit", text)
        self.assertIn("https://www.producthunt.com/launch", text)
        self.assertIn("https://help.producthunt.com/en/articles/479557-how-to-post-a-product", text)
        self.assertIn("Do not launch before the 72-hour X feedback", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/repo-card.png", text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png", text)
        self.assertIn("Make AI coding agents argue before they ship", text)
        self.assertIn("Maker Comment", text)
        self.assertIn("Gallery Assets", text)
        self.assertIn("FAQ", text)
        self.assertIn("Do not ask for upvotes.", text)
        self.assertIn("host-live or provider-live support", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, distribution, targets, llms):
            self.assertIn("docs/product-hunt-launch-kit.md", surface.read_text(encoding="utf-8"))

    def test_developer_forum_feedback_kit_is_feedback_first_and_linked(self) -> None:
        forum_kit = REPO_ROOT / "docs" / "developer-forum-feedback-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(forum_kit.exists())
        text = forum_kit.read_text(encoding="utf-8")
        self.assertIn("# Developer Forum Feedback Kit", text)
        self.assertIn("https://redditinc.com/policies/content-policy", text)
        self.assertIn("https://www.reddit.com/wiki/selfpromotion/", text)
        self.assertIn("Do not post this kit before the 72-hour X feedback", text)
        self.assertIn("Community-specific rules are the source of truth", text)
        self.assertIn("What AI-generated coding failure should this review gate catch next?", text)
        self.assertIn("Can you upvote this?", text)
        self.assertIn("Do not ask for votes, upvotes, stars", text)
        self.assertIn("host-live or provider-live support", text)
        self.assertIn("copy_source: docs/developer-forum-feedback-kit.md", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)

        for surface in (readme, docs_index, launch_copy, share_kit, distribution, targets, llms):
            self.assertIn("docs/developer-forum-feedback-kit.md", surface.read_text(encoding="utf-8"))

    def test_short_video_script_kit_is_claim_safe_and_linked(self) -> None:
        video_kit = REPO_ROOT / "docs" / "short-video-script-kit.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        recording_guide = REPO_ROOT / "docs" / "demo-recording-guide.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(video_kit.exists())
        text = video_kit.read_text(encoding="utf-8")
        self.assertIn("# Short Video Script Kit", text)
        self.assertIn("Do not publish a new public video campaign before the 72-hour X feedback", text)
        self.assertIn("docs/promotion-feedback-template.md", text)
        self.assertIn("30-Second Script", text)
        self.assertIn("60-Second Script", text)
        self.assertIn("Product Hunt Gallery Clip", text)
        self.assertIn("Forum-Friendly Clip", text)
        self.assertIn("/room -> /debate -> ship-check -> ship / revise / reject", text)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("screenshot-ready one-minute demo", text)
        self.assertIn("Do not claim host-live or provider-live support without fresh evidence.", text)
        self.assertIn("Do not ask for votes, upvotes, or coordinated promotion.", text)
        self.assertIn("copy_source: docs/short-video-script-kit.md", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)

        for surface in (readme, docs_index, launch_copy, share_kit, recording_guide, llms):
            self.assertIn("docs/short-video-script-kit.md", surface.read_text(encoding="utf-8"))

    def test_promotion_feedback_template_is_claim_safe_and_linked(self) -> None:
        feedback = REPO_ROOT / "docs" / "promotion-feedback-template.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        submission_kit = REPO_ROOT / "docs" / "directory-submission-kit.md"
        distribution = REPO_ROOT / "docs" / "distribution-checklist.md"
        targets = REPO_ROOT / "docs" / "public-submission-targets.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(feedback.exists())
        text = feedback.read_text(encoding="utf-8")
        self.assertIn("# Promotion Feedback Template", text)
        self.assertIn("72h", text)
        self.assertIn("72-hour", text)
        self.assertIn("impressions", text)
        self.assertIn("link clicks", text)
        self.assertIn("stars_before", text)
        self.assertIn("stars_after", text)
        self.assertIn("mechanism-first", text)
        self.assertIn("failure-mode-first", text)
        self.assertIn("demo-first", text)
        self.assertIn("comparison-first", text)
        self.assertIn("proof-card-first", text)
        self.assertIn("Do not publish a second public campaign", text)
        self.assertIn("records public response", text)
        self.assertIn("host-live or provider-live support claims", text)

        for surface in (readme, docs_index, launch_copy, share_kit, submission_kit, distribution, targets, llms):
            self.assertIn("docs/promotion-feedback-template.md", surface.read_text(encoding="utf-8"))

    def test_comparison_guide_is_claim_safe_and_linked(self) -> None:
        comparison = REPO_ROOT / "docs" / "comparison-guide.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(comparison.exists())
        text = comparison.read_text(encoding="utf-8")
        self.assertIn("# Comparison Guide", text)
        self.assertIn("One direct AI agent answer", text)
        self.assertIn("Multi-agent framework", text)
        self.assertIn("CI / test suite", text)
        self.assertIn("Should this AI-assisted work be trusted yet?", text)
        self.assertIn("host-live or provider-live", text)
        self.assertIn("does not add any host-live or provider-live support claim", text)

        for surface in (readme, docs_index, launch_copy, share_kit, llms):
            self.assertIn("docs/comparison-guide.md", surface.read_text(encoding="utf-8"))

    def test_ai_failure_modes_guide_is_claim_safe_and_linked(self) -> None:
        failure_modes = REPO_ROOT / "docs" / "ai-failure-modes.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(failure_modes.exists())
        text = failure_modes.read_text(encoding="utf-8")
        self.assertIn("# AI Failure Modes This Catches", text)
        self.assertIn("Confident but untested code", text)
        self.assertIn("Launch claim too broad", text)
        self.assertIn("Refactor with no second use case", text)
        self.assertIn("ship`, `revise`, or `reject", text)
        self.assertIn("does not guarantee correctness", text)
        self.assertIn("does not add host-live or provider-live support claims", text)

        for surface in (readme, docs_index, launch_copy, share_kit, llms):
            self.assertIn("docs/ai-failure-modes.md", surface.read_text(encoding="utf-8"))

    def test_demo_recording_guide_is_claim_safe_and_linked(self) -> None:
        recording = REPO_ROOT / "docs" / "demo-recording-guide.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        launch_copy = REPO_ROOT / "docs" / "launch-copy.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"
        llms = REPO_ROOT / "docs" / "llms.txt"

        self.assertTrue(recording.exists())
        text = recording.read_text(encoding="utf-8")
        self.assertIn("# Demo Recording Guide", text)
        self.assertIn("45-Second Storyboard", text)
        self.assertIn("screenshot-ready card", text)
        self.assertIn("./rtw ship-check \"Should we merge this AI-generated feature?\"", text)
        self.assertIn("X / Twitter", text)
        self.assertIn("LinkedIn", text)
        self.assertIn("does not add host-live or provider-live support claims", text)

        for surface in (readme, docs_index, launch_copy, share_kit, llms):
            self.assertIn("docs/demo-recording-guide.md", surface.read_text(encoding="utf-8"))

    def test_github_contribution_templates_preserve_claim_boundary(self) -> None:
        templates = [
            REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
            REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml",
            REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "claim_boundary.yml",
            REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "workflow_example.yml",
            REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
        ]
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for template in templates:
            self.assertTrue(template.exists(), str(template))
            text = template.read_text(encoding="utf-8")
            self.assertIn("host-live", text)
            self.assertIn("provider-live", text)

        contributing = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        share_kit = (REPO_ROOT / "docs" / "community-share-kit.md").read_text(encoding="utf-8")
        self.assertIn("## Contribute", readme)
        self.assertIn("examples/transcripts/ship-check-architecture-decision.md", readme)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", readme)
        self.assertIn("docs/community-share-kit.md#real-world-failure-mode-to-share", readme)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace/labels/good%20first%20issue", readme)
        self.assertIn("Filing Issues", contributing)
        self.assertIn("Claim boundary question", contributing)
        self.assertIn("AI workflow example", contributing)
        self.assertIn("workflow_example.yml", readme)
        self.assertIn("workflow_example.yml", share_kit)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace/labels/good%20first%20issue", contributing)
        self.assertIn("Good First Feedback", share_kit)
        self.assertIn("CONTRIBUTING.md", share_kit)
        self.assertIn("https://github.com/MarkDonish/round-table-workspace/labels/good%20first%20issue", share_kit)

    def test_public_discovery_files_are_claim_safe(self) -> None:
        robots = REPO_ROOT / "docs" / "robots.txt"
        sitemap = REPO_ROOT / "docs" / "sitemap.xml"
        llms = REPO_ROOT / "docs" / "llms.txt"
        docs_index = REPO_ROOT / "docs" / "index.md"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"

        for path in (robots, sitemap, llms):
            self.assertTrue(path.exists(), str(path))

        robots_text = robots.read_text(encoding="utf-8")
        sitemap_text = sitemap.read_text(encoding="utf-8")
        llms_text = llms.read_text(encoding="utf-8")

        self.assertIn("Sitemap: https://markdonish.github.io/round-table-workspace/sitemap.xml", robots_text)
        self.assertIn("<loc>https://markdonish.github.io/round-table-workspace/</loc>", sitemap_text)
        self.assertIn("ai-generated-feature-review-demo.html", sitemap_text)
        self.assertIn("one-minute-demo-card.html", sitemap_text)
        self.assertIn("Round Table Workspace is a local-first review workflow", llms_text)
        self.assertIn("host-live or provider-live", llms_text)
        self.assertIn('./rtw ship-check "Should we merge this AI-generated feature?"', llms_text)
        self.assertIn("docs/llms.txt", docs_index.read_text(encoding="utf-8"))
        self.assertIn("docs/sitemap.xml", docs_index.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/llms.txt", share_kit.read_text(encoding="utf-8"))

    def test_use_cases_surface_is_pages_ready_and_linked(self) -> None:
        page = REPO_ROOT / "docs" / "use-cases.html"
        markdown = REPO_ROOT / "docs" / "use-cases.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        sitemap = REPO_ROOT / "docs" / "sitemap.xml"
        llms = REPO_ROOT / "docs" / "llms.txt"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"

        self.assertTrue(page.exists())
        self.assertTrue(markdown.exists())
        text = page.read_text(encoding="utf-8")
        self.assertIn("Use it before one confident AI answer becomes trusted work.", text)
        self.assertIn("Pre-merge AI review", text)
        self.assertIn("Launch claim check", text)
        self.assertIn("Star on GitHub", text)
        self.assertIn("host-live", text)
        self.assertIn("provider-live", text)
        self.assertIn("./use-cases.md", text)
        self.assertNotIn("<script", text.lower())

        markdown_text = markdown.read_text(encoding="utf-8")
        self.assertIn("# Use Cases", markdown_text)
        self.assertIn("ship-check", markdown_text)
        self.assertIn("host-live or provider-live", markdown_text)

        for surface in (readme, docs_index):
            self.assertIn("docs/use-cases", surface.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/use-cases.html", sitemap.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/use-cases.html", llms.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/use-cases.html", share_kit.read_text(encoding="utf-8"))

    def test_one_minute_demo_surface_is_pages_ready_and_linked(self) -> None:
        page = REPO_ROOT / "docs" / "one-minute-demo.html"
        card_page = REPO_ROOT / "docs" / "one-minute-demo-card.html"
        card_image = REPO_ROOT / "docs" / "one-minute-demo-card.png"
        markdown = REPO_ROOT / "docs" / "one-minute-demo.md"
        readme = REPO_ROOT / "README.md"
        docs_index = REPO_ROOT / "docs" / "index.md"
        sitemap = REPO_ROOT / "docs" / "sitemap.xml"
        llms = REPO_ROOT / "docs" / "llms.txt"
        share_kit = REPO_ROOT / "docs" / "community-share-kit.md"

        self.assertTrue(page.exists())
        self.assertTrue(card_page.exists())
        self.assertTrue(card_image.exists())
        self.assertTrue(markdown.exists())
        text = page.read_text(encoding="utf-8")
        self.assertIn("See the review gate in one minute.", text)
        self.assertIn("Screenshot-ready one-minute demo", text)
        self.assertIn("Before one confident AI answer becomes trusted work", text)
        self.assertIn("Decision: revise", text)
        self.assertIn("Decision badge", text)
        self.assertIn("product: revise", text)
        self.assertIn("engineering: ship", text)
        self.assertIn("github.com/MarkDonish/round-table-workspace", text)
        self.assertIn("Star on GitHub", text)
        self.assertIn("host-live", text)
        self.assertIn("provider-live", text)
        self.assertIn("./one-minute-demo.md", text)
        self.assertIn("./one-minute-demo-card.png", text)
        self.assertIn('property="og:image"', text)
        self.assertIn('name="twitter:image"', text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png", text)
        self.assertNotIn("<script", text.lower())

        card_text = card_page.read_text(encoding="utf-8")
        self.assertIn("Make AI coding agents argue before they ship.", card_text)
        self.assertIn("Decision: revise", card_text)
        self.assertIn("No</em> host-live or provider-live claim", card_text)
        image_bytes = card_image.read_bytes()
        self.assertEqual(image_bytes[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(image_bytes[16:20], "big"), 1200)
        self.assertEqual(int.from_bytes(image_bytes[20:24], "big"), 630)

        markdown_text = markdown.read_text(encoding="utf-8")
        self.assertIn("# One-Minute Demo", markdown_text)
        self.assertIn("Screenshot-Friendly Card", markdown_text)
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png", markdown_text)
        self.assertIn("Decision: revise", markdown_text)
        self.assertIn("fixture-backed local transcript", markdown_text)
        self.assertIn("host-live or provider-live", markdown_text)

        for surface in (readme, docs_index):
            self.assertIn("docs/one-minute-demo", surface.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", sitemap.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.html", sitemap.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", llms.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png", llms.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo.html", share_kit.read_text(encoding="utf-8"))
        self.assertIn("https://markdonish.github.io/round-table-workspace/one-minute-demo-card.png", share_kit.read_text(encoding="utf-8"))

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
        self.assertTrue(workflow_check["has_pre_publish_release_guards"])
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

    def test_github_release_publication_check_redacts_command_output(self) -> None:
        publication_check = self.load_module(
            "github_release_publication_redaction",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "github_release_publication_check.py",
        )
        token = "ghp_releasepublication1234567890SECRET"

        def fake_run(command: list[str], **_: object) -> object:
            import subprocess

            return subprocess.CompletedProcess(
                command,
                1,
                stdout=f'{{"ok": false, "token": "{token}"}}\n',
                stderr=f"Authorization: Bearer {token}",
            )

        with patch.object(publication_check.subprocess, "run", side_effect=fake_run):
            result = publication_check.run_command(["fake", "--token", token], timeout_seconds=1)

        result_text = str(result)
        self.assertNotIn(token, result_text)
        self.assertIn("[REDACTED]", result_text)

    def test_github_release_push_success_is_dry_run_evidence(self) -> None:
        publication_check = self.load_module(
            "github_release_publication_push_dry_run",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "github_release_publication_check.py",
        )

        summary = publication_check.build_summary(
            api_check={"status_code": 404, "request_completed": True, "authenticated": True},
            gh_release={"status": "not_found", "published": False, "authenticated": True},
            gh_state={"authenticated": True},
            token_state={"present": True},
            local_tag={"exists": True},
            release_draft={"exists": True},
            release_workflow=release_workflow_fixture(),
            workflow_runs={
                "authenticated": True,
                "latest_run": {
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "updatedAt": "2026-06-29T09:10:24Z",
                },
            },
            repository="MarkDonish/round-table-workspace",
            tag="v0.2.2-pages-launch-kit",
        )

        self.assertEqual(summary["release_workflow_run_status"], "latest_push_dry_run_success")
        self.assertEqual(
            summary["publication_decision"],
            "release_workflow_push_dry_run_succeeded_release_page_requires_authenticated_confirmation",
        )

    def test_github_release_page_currentness_flags_newer_workflow_run(self) -> None:
        publication_check = self.load_module(
            "github_release_publication_currentness",
            REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "github_release_publication_check.py",
        )

        summary = publication_check.build_summary(
            api_check={
                "status_code": 200,
                "request_completed": True,
                "authenticated": True,
                "payload": {"published_at": "2026-06-02T00:00:00Z"},
            },
            gh_release={
                "status": "published",
                "published": True,
                "authenticated": True,
                "published_at": "2026-06-02T00:00:00Z",
            },
            gh_state={"authenticated": True},
            token_state={"present": True},
            local_tag={"exists": True},
            release_draft={"exists": True},
            release_workflow=release_workflow_fixture(),
            workflow_runs={
                "authenticated": True,
                "latest_run": {
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "updatedAt": "2026-06-29T09:10:24Z",
                },
            },
            repository="MarkDonish/round-table-workspace",
            tag="v0.2.2-pages-launch-kit",
        )

        self.assertEqual(summary["release_page_status"], "published")
        self.assertEqual(summary["release_page_current_status"], "published_but_older_than_latest_workflow_run")
        self.assertEqual(summary["publication_decision"], "published_but_currentness_requires_review")

    def test_publish_release_workflow_dry_run_does_not_swallow_gh_errors(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "publish-github-release.yml").read_text(encoding="utf-8")

        self.assertNotIn("gh release view \"$TAG\" --repo \"$GITHUB_REPOSITORY\" \\\n            --json tagName,name,isDraft,isPrerelease,publishedAt,targetCommitish,url || true", workflow)
        self.assertIn('release_view_status=$?', workflow)
        self.assertIn('release_view_status":"not_found"', workflow)
        self.assertIn('exit "$release_view_status"', workflow)
        self.assertIn("Verify checkout matches release tag", workflow)
        self.assertIn('tag_commit="$(git rev-list -n 1 "$TAG")"', workflow)
        self.assertIn("release checkout does not match tag", workflow)
        self.assertIn("Run release guards before publication", workflow)
        self.assertIn("python3 scripts/check_source_truth_consistency.py", workflow)
        self.assertIn("./rtw release-check \\", workflow)
        self.assertIn("--strict-git-clean", workflow)
        self.assertIn("$RUNNER_TEMP/rtw-publish-release-check", workflow)
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
        self.assertTrue(release_defaults["workflow_has_pre_publish_release_guards"])
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
        self.assertIsNotNone(freshness["source_commit_ahead_count"])
        self.assertLessEqual(freshness["source_commit_ahead_count"], 1, freshness)

    def test_source_truth_rejects_dashboard_source_commit_behind_non_dashboard_change(self) -> None:
        from scripts import check_source_truth_consistency

        with patch.object(check_source_truth_consistency, "git_commit_is_ancestor", return_value=True):
            with patch.object(check_source_truth_consistency, "git_commit_ahead_count", return_value=1):
                with patch.object(
                    check_source_truth_consistency,
                    "git_changed_paths_since",
                    return_value=["scripts/release_check.py"],
                ):
                    freshness = check_source_truth_consistency.check_claim_dashboard_freshness("")

        self.assertFalse(freshness["ok"], freshness)
        self.assertEqual(freshness["source_commit_ahead_count"], 1)
        self.assertEqual(freshness["source_commit_changed_paths"], ["scripts/release_check.py"])
        self.assertIn("claim_dashboard_source_commit_stale", freshness["problems"])

    @staticmethod
    def load_module(name: str, path: Path) -> object:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def release_workflow_fixture() -> dict[str, object]:
    return {
        "usable": True,
        "defaults_match_requested_release": True,
        "publication_safe": True,
        "default_tag": "v0.2.2-pages-launch-kit",
        "default_release_draft": "docs/releases/v0.2.2-pages-launch-kit-github-release.md",
        "default_dry_run": "false",
        "push_trigger_can_publish": False,
        "exists": True,
        "has_tag_checkout_guard": True,
        "watches_gate_scripts": True,
    }
