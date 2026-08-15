from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.runtime.subagent_executor import (
    SubagentExecutor,
    SubagentTask,
    verify_blind_isolation,
)


class SubagentExecutorTest(unittest.TestCase):
    def test_blind_isolation_verification(self) -> None:
        t1 = SubagentTask(
            agent_id="jobs",
            display_name="Steve Jobs",
            short_name="Jobs",
            responsibility="Product vision and simplicity",
            topic="Refactor auth layer",
            profile_text="Focus on user simplicity.",
        )
        t2 = SubagentTask(
            agent_id="security",
            display_name="Security Auditor",
            short_name="SecAuditor",
            responsibility="Defensive review and vulnerability audit",
            topic="Refactor auth layer",
            profile_text="Focus on OWASP and token safety.",
        )
        is_isolated, violations = verify_blind_isolation([t1, t2])
        self.assertTrue(is_isolated)
        self.assertEqual(len(violations), 0)

    def test_parallel_blind_execution(self) -> None:
        executor = SubagentExecutor(max_workers=2)
        t1 = SubagentTask(
            agent_id="jobs",
            display_name="Steve Jobs",
            short_name="Jobs",
            responsibility="Product simplicity",
            topic="Launch feature",
            profile_text="Simplicity is the ultimate sophistication.",
        )
        t2 = SubagentTask(
            agent_id="munger",
            display_name="Charlie Munger",
            short_name="Munger",
            responsibility="Inversion and risk analysis",
            topic="Launch feature",
            profile_text="Invert, always invert.",
        )
        results = executor.execute_parallel_blind([t1, t2])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].agent_id, "jobs")
        self.assertEqual(results[1].agent_id, "munger")
        self.assertTrue(results[0].ok)
        self.assertTrue(results[1].ok)
        self.assertIsNotNone(results[0].argument)
        self.assertIsNotNone(results[1].argument)


if __name__ == "__main__":
    unittest.main()
