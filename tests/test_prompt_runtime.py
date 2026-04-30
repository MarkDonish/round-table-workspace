from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from roundtable_core.prompts import PromptRenderError, PromptSpec, parse_structured_output, render_prompt


class PromptRuntimeTest(unittest.TestCase):
    def test_prompt_spec_rejects_missing_and_extra_variables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.md"
            prompt.write_text("Topic: {{ topic }}", encoding="utf-8")
            spec = PromptSpec(
                prompt_path=prompt,
                required_variables=("topic",),
                allowed_variables=("topic",),
                append_context_policy="explicit",
            )
            with self.assertRaises(PromptRenderError):
                render_prompt(prompt, {}, prompt_spec=spec)
            with self.assertRaises(PromptRenderError):
                render_prompt(prompt, {"topic": "A", "secret": "B"}, prompt_spec=spec)

            rendered = render_prompt(prompt, {"topic": "A"}, prompt_spec=spec, append_context=True)
            self.assertIn("Runtime Input", rendered.text)
            self.assertNotIn("secret", rendered.text)

    def test_renderer_default_does_not_append_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.md"
            prompt.write_text("Topic: {{ topic }}", encoding="utf-8")
            rendered = render_prompt(prompt, {"topic": "A"}, required_variables=["topic"])
            self.assertNotIn("Runtime Input", rendered.text)

    def test_parser_reports_candidates(self) -> None:
        result = parse_structured_output(
            "bad ```json\n{\"missing\": true}\n``` good ```json\n{\"ok\": true}\n```",
            required_keys=["ok"],
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.data, {"ok": True})
        self.assertGreaterEqual(len(result.candidates), 2)
        self.assertIsNotNone(result.candidates[0]["error"])

    def test_parser_reports_malformed_json_candidate(self) -> None:
        result = parse_structured_output("```json\n{\"ok\": true,}\n```", required_keys=["ok"])
        self.assertFalse(result.ok)
        self.assertTrue(result.candidates)
        self.assertFalse(result.candidates[0]["parse_ok"])


if __name__ == "__main__":
    unittest.main()
