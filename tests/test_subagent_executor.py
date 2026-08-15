from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_SCHEMA_PATH = REPO_ROOT / "schemas" / "debate-session.schema.json"
RESULT_SCHEMA_PATH = REPO_ROOT / "schemas" / "debate-result.schema.json"

from roundtable_core.runtime.subagent_executor import (
    AgentArgumentOutput,
    SubagentExecutor,
    SubagentResult,
    SubagentTask,
    generate_deterministic_blind_argument,
    parse_argument_from_json_or_text,
    sanitize_profile_for_blind_review,
    verify_blind_isolation,
)
from roundtable_core.validation import validate_file, validate_instance
import sys
sys.path.insert(0, str(REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"))
from subagent_harness import (
    SubagentDebateHarness,
    build_blind_tasks,
    evaluate_reviewer_7d_rubric,
    load_participant_profile,
    render_debate_markdown,
    synthesize_moderator_summary,
)


class SubagentExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.session_schema = json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.result_schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_sanitize_profile_strips_counterweights(self) -> None:
        raw_profile = """# Profile
name: Test Agent
## 角色定位
- Focus on testing.
## 对冲对象
- 首选：Taleb、Munger
## 发言约束
- Be concise.
"""
        sanitized = sanitize_profile_for_blind_review(raw_profile)
        self.assertNotIn("对冲对象", sanitized)
        self.assertNotIn("Taleb", sanitized)
        self.assertNotIn("Munger", sanitized)
        self.assertIn("Focus on testing", sanitized)
        self.assertIn("Be concise", sanitized)

    def test_task_blind_system_prompt_contains_only_own_profile(self) -> None:
        task = SubagentTask(
            agent_id="steve-jobs",
            display_name="Steve Jobs",
            short_name="Jobs",
            responsibility="Compress product into sharp experience.",
            topic="Evaluate AI note taking app",
            profile_text="Focus on value proposition and user joy.",
        )
        sys_prompt = task.build_blind_system_prompt()
        user_prompt = task.build_blind_user_prompt()

        self.assertIn("Steve Jobs", sys_prompt)
        self.assertIn("Compress product into sharp experience", sys_prompt)
        self.assertIn("Focus on value proposition and user joy", sys_prompt)
        self.assertIn("Evaluate AI note taking app", user_prompt)
        self.assertNotIn("munger", sys_prompt.lower())
        self.assertNotIn("taleb", sys_prompt.lower())

    def test_verify_blind_isolation_detects_leakage(self) -> None:
        task_clean = SubagentTask(
            agent_id="steve-jobs",
            display_name="Steve Jobs",
            short_name="Jobs",
            responsibility="Focus on product.",
            topic="Test Topic",
            profile_text="Pure lens profile.",
        )
        task_leaky = SubagentTask(
            agent_id="munger",
            display_name="Charlie Munger",
            short_name="Munger",
            responsibility="Focus on risk.",
            topic="Test Topic",
            profile_text="Review profile.",
            context="Other agents argued that the product has strong retention.",
        )

        ok_clean, violations_clean = verify_blind_isolation([task_clean])
        self.assertTrue(ok_clean)
        self.assertEqual(violations_clean, [])

        ok_leaky, violations_leaky = verify_blind_isolation([task_clean, task_leaky])
        self.assertFalse(ok_leaky)
        self.assertTrue(any("other agents argued" in v for v in violations_leaky))

    def test_executor_runs_parallel_blind_deterministically(self) -> None:
        executor = SubagentExecutor(max_workers=3)
        tasks = [
            SubagentTask(
                agent_id="steve-jobs",
                display_name="Steve Jobs",
                short_name="Jobs",
                responsibility="Compress the product experience.",
                topic="AI study product validation",
                profile_text="Focus on core delight.",
            ),
            SubagentTask(
                agent_id="munger",
                display_name="Charlie Munger",
                short_name="Munger",
                responsibility="Check downside and kill rules.",
                topic="AI study product validation",
                profile_text="Focus on inversion and risk.",
            ),
            SubagentTask(
                agent_id="karpathy",
                display_name="Andrej Karpathy",
                short_name="Karpathy",
                responsibility="Check technical loop quality.",
                topic="AI study product validation",
                profile_text="Focus on thin technical loops.",
            ),
        ]

        results = executor.execute_parallel_blind(tasks)
        self.assertEqual(len(results), 3)
        self.assertEqual([r.agent_id for r in results], ["steve-jobs", "munger", "karpathy"])
        for res in results:
            self.assertTrue(res.ok)
            self.assertIsNotNone(res.argument)
            self.assertGreater(len(res.argument.evidence), 0)
            self.assertGreater(len(res.argument.core_conclusion), 0)
            self.assertIn(res.argument.confidence, ("high", "medium", "low"))

    def test_executor_with_custom_worker_function(self) -> None:
        executor = SubagentExecutor(max_workers=2)
        tasks = [
            SubagentTask(
                agent_id="custom-1",
                display_name="Custom Lens 1",
                short_name="C1",
                responsibility="Review 1",
                topic="Topic 1",
                profile_text="Profile 1",
            ),
            SubagentTask(
                agent_id="custom-2",
                display_name="Custom Lens 2",
                short_name="C2",
                responsibility="Review 2",
                topic="Topic 2",
                profile_text="Profile 2",
            ),
        ]

        def custom_worker(task: SubagentTask) -> SubagentResult:
            arg = AgentArgumentOutput(
                agent_id=task.agent_id,
                role_duty=task.responsibility,
                core_conclusion=f"Custom conclusion for {task.agent_id}",
                evidence=[f"Custom evidence for {task.agent_id}"],
                biggest_problem="Custom problem",
                opposed_misjudgment="Custom misjudgment",
                concrete_recommendation="Custom action",
                confidence="high",
                uncertainties=["Custom uncertainty"],
            )
            return SubagentResult(
                agent_id=task.agent_id,
                short_name=task.short_name,
                ok=True,
                argument=arg,
                raw_text=json.dumps(arg.to_dict()),
                execution_time_seconds=0.01,
            )

        results = executor.execute_parallel_blind(tasks, worker_fn=custom_worker)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].argument.core_conclusion, "Custom conclusion for custom-1")
        self.assertEqual(results[1].argument.core_conclusion, "Custom conclusion for custom-2")

    def test_harness_end_to_end_debate_passes_schema_validation(self) -> None:
        harness = SubagentDebateHarness()
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = harness.run_debate(
                "Decide whether to start product validation for AI learning assistant",
                participants=["steve-jobs", "munger", "karpathy"],
                primary_type="product",
                state_root=tmp_dir,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["action"], "parallel-subagent-debate")
            self.assertEqual(result["final_outcome"], "allow")
            self.assertGreaterEqual(result["rubric_total"], 10)
            self.assertEqual(result["subagent_count"], 3)

            debate_result = result["debate_result"]
            debate_session = result["debate_session"]

            # Validate against official JSON schemas
            result_errors = validate_instance(instance=debate_result, schema=self.result_schema)
            session_errors = validate_instance(instance=debate_session, schema=self.session_schema)
            self.assertEqual(result_errors, [], result_errors)
            self.assertEqual(session_errors, [], session_errors)

            # Check written artifacts
            self.assertTrue((Path(tmp_dir) / "debate-result.json").exists())
            self.assertTrue((Path(tmp_dir) / "debate-session.json").exists())
            self.assertTrue((Path(tmp_dir) / "summary.md").exists())

            summary_content = (Path(tmp_dir) / "summary.md").read_text(encoding="utf-8")
            self.assertIn("Parallel Subagent Debate", summary_content)
            self.assertIn("Reviewer 7-Dimension Rubric Gate", summary_content)
            self.assertIn("Final Decision", summary_content)

    def test_reviewer_7d_rubric_scoring_and_blocking(self) -> None:
        moderator_summary = {
            "topic_restatement": "The decision is whether to start validation, not build full platform.",
            "preliminary_recommendation": "Run a 7-day test with retention threshold.",
        }
        agent_arguments = [
            {
                "agent_id": "steve-jobs",
                "core_conclusion": "Focus product.",
                "concrete_recommendation": "Test with 5 users.",
                "opposed_misjudgment": "Feature bloat.",
                "uncertainties": ["First cohort size."],
            },
            {
                "agent_id": "munger",
                "core_conclusion": "Invert and set kill rules.",
                "concrete_recommendation": "Set 7-day threshold.",
                "opposed_misjudgment": "Polite feedback.",
                "uncertainties": ["Drop-off rate."],
            },
            {
                "agent_id": "karpathy",
                "core_conclusion": "Thin loop.",
                "concrete_recommendation": "Build minimal harness.",
                "opposed_misjudgment": "Early automation.",
                "uncertainties": ["Model latency."],
            },
        ]
        evidence_buckets = {
            "facts": ["3 agents participated."],
            "inferences": ["Narrow test is safer."],
            "uncertainties": ["Adoption rate."],
            "recommendations": ["Run 7-day test with explicit kill rules."],
        }

        eval_res = evaluate_reviewer_7d_rubric("Test topic", moderator_summary, agent_arguments, evidence_buckets)
        self.assertTrue(eval_res["review_applicable"])
        self.assertTrue(eval_res["allow_final_decision"])
        self.assertEqual(eval_res["blocking_dimensions"], [])
        self.assertGreaterEqual(eval_res["rubric_total"], 12)
        for dim in (
            "problem_reframing",
            "key_variables",
            "assumption_separation",
            "opposition_quality",
            "risk_to_action",
            "next_testable_step",
            "uncertainty_disclosure",
        ):
            self.assertIn(dim, eval_res["rubric_scores"])
            self.assertGreaterEqual(eval_res["rubric_scores"][dim], 1)


if __name__ == "__main__":
    unittest.main()
