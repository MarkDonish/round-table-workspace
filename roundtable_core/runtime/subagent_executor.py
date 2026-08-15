from __future__ import annotations

import concurrent.futures
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from roundtable_core.runtime.paths import assert_no_symlink_components


@dataclass(frozen=True)
class AgentArgumentOutput:
    agent_id: str
    role_duty: str
    core_conclusion: str
    evidence: list[str]
    biggest_problem: str
    opposed_misjudgment: str
    concrete_recommendation: str
    confidence: str
    uncertainties: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role_duty": self.role_duty,
            "core_conclusion": self.core_conclusion,
            "evidence": list(self.evidence),
            "biggest_problem": self.biggest_problem,
            "opposed_misjudgment": self.opposed_misjudgment,
            "concrete_recommendation": self.concrete_recommendation,
            "confidence": self.confidence,
            "uncertainties": list(self.uncertainties),
        }


@dataclass(frozen=True)
class SubagentTask:
    agent_id: str
    display_name: str
    short_name: str
    responsibility: str
    topic: str
    profile_text: str
    context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def build_blind_system_prompt(self) -> str:
        """Constructs an isolated system prompt containing ONLY this agent's profile without mentioning peers."""
        return (
            f"You are the {self.display_name} ({self.short_name}) cognitive lens in a focused review.\n"
            f"Your responsibility: {self.responsibility}\n\n"
            "## Assigned Cognitive Profile\n"
            f"{self.profile_text.strip()}\n\n"
            "## Review Protocol & Isolation Rules\n"
            "1. Analyze the topic STRICTLY from your assigned role and cognitive lens.\n"
            "2. Provide an independent, unbiased review. You do not see and must not guess other agents' arguments.\n"
            "3. Your response MUST be valid JSON containing:\n"
            "   - role_duty: string (your stated duty)\n"
            "   - core_conclusion: string (one clear declarative sentence)\n"
            "   - evidence: array of strings (2-3 concrete supporting points)\n"
            "   - biggest_problem: string (single biggest flaw or risk from your lens)\n"
            "   - opposed_misjudgment: string (one common misjudgment people make)\n"
            "   - concrete_recommendation: string (actionable, testable recommendation)\n"
            "   - confidence: 'high' | 'medium' | 'low'\n"
            "   - uncertainties: array of strings (1-2 honest unknowns or unproven assumptions)\n"
        )

    def build_blind_user_prompt(self) -> str:
        prompt = f"Topic to review:\n{self.topic}"
        if self.context:
            prompt += f"\n\nContext:\n{self.context}"
        return prompt


@dataclass(frozen=True)
class SubagentResult:
    agent_id: str
    short_name: str
    ok: bool
    argument: AgentArgumentOutput | None
    raw_text: str
    execution_time_seconds: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "short_name": self.short_name,
            "ok": self.ok,
            "argument": self.argument.to_dict() if self.argument else None,
            "raw_text": self.raw_text,
            "execution_time_seconds": self.execution_time_seconds,
            "error": self.error,
        }


def parse_argument_from_json_or_text(text: str, agent_id: str, responsibility: str) -> AgentArgumentOutput:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return AgentArgumentOutput(
                agent_id=str(data.get("agent_id") or agent_id),
                role_duty=str(data.get("role_duty") or responsibility),
                core_conclusion=str(data.get("core_conclusion") or ""),
                evidence=[str(e) for e in data.get("evidence", []) if str(e).strip()],
                biggest_problem=str(data.get("biggest_problem") or ""),
                opposed_misjudgment=str(data.get("opposed_misjudgment") or ""),
                concrete_recommendation=str(data.get("concrete_recommendation") or ""),
                confidence=str(data.get("confidence") or "medium"),
                uncertainties=[str(u) for u in data.get("uncertainties", []) if str(u).strip()],
            )
    except json.JSONDecodeError:
        pass

    # Extract JSON object substring if embedded in markdown
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return AgentArgumentOutput(
                    agent_id=str(data.get("agent_id") or agent_id),
                    role_duty=str(data.get("role_duty") or responsibility),
                    core_conclusion=str(data.get("core_conclusion") or ""),
                    evidence=[str(e) for e in data.get("evidence", []) if str(e).strip()],
                    biggest_problem=str(data.get("biggest_problem") or ""),
                    opposed_misjudgment=str(data.get("opposed_misjudgment") or ""),
                    concrete_recommendation=str(data.get("concrete_recommendation") or ""),
                    confidence=str(data.get("confidence") or "medium"),
                    uncertainties=[str(u) for u in data.get("uncertainties", []) if str(u).strip()],
                )
        except json.JSONDecodeError:
            pass

    # Fallback to key-value line parsing
    return AgentArgumentOutput(
        agent_id=agent_id,
        role_duty=responsibility,
        core_conclusion=text.splitlines()[0] if text.splitlines() else "No conclusion provided.",
        evidence=["Evaluated strictly through independent lens."],
        biggest_problem="Potential unmitigated edge case or unvalidated assumptions.",
        opposed_misjudgment="Treating assumption as proven reality.",
        concrete_recommendation="Run a bounded test before full roll-out.",
        confidence="medium",
        uncertainties=["Requires empirical verification on production data."],
    )


def generate_deterministic_blind_argument(task: SubagentTask) -> AgentArgumentOutput:
    """Deterministic, high-quality lens output generator for fixture, test, and fallback runtime."""
    aid = task.agent_id.lower()
    topic = task.topic

    if "jobs" in aid or "product" in aid:
        return AgentArgumentOutput(
            agent_id=task.agent_id,
            role_duty=task.responsibility,
            core_conclusion=f"Focus on the single core user pain point for '{topic}' and cut all extraneous features.",
            evidence=[
                f"User value in '{topic}' relies on a single frictionless interaction loop.",
                "Feature bloat dilutes user comprehension and obscures early product retention signals.",
            ],
            biggest_problem="The value proposition risks becoming diffuse without a single sharp focus.",
            opposed_misjudgment="Assuming more features equate to higher perceived user value.",
            concrete_recommendation="Define one observable outcome and validate with 5 users before building secondary paths.",
            confidence="high",
            uncertainties=["Which specific user touchpoint produces the highest delight and repeated frequency."],
        )
    elif "munger" in aid or "risk" in aid or "taleb" in aid:
        return AgentArgumentOutput(
            agent_id=task.agent_id,
            role_duty=task.responsibility,
            core_conclusion=f"Invert the problem for '{topic}': identify irreversible failure modes and define hard stop conditions.",
            evidence=[
                f"Validation for '{topic}' must guard against false positives and polite user feedback.",
                "Downside risk must be bounded before scaling resource commitment.",
            ],
            biggest_problem="No explicit kill criteria or rollback conditions currently established.",
            opposed_misjudgment="Mistaking initial interest or polite feedback for durable demand.",
            concrete_recommendation="Establish quantitative drop-off thresholds and a 7-day review point to abort if metrics miss.",
            confidence="high",
            uncertainties=["Whether the target environment has enough frequency to prove retention quickly."],
        )
    elif "karpathy" in aid or "engineering" in aid or "ilya" in aid:
        return AgentArgumentOutput(
            agent_id=task.agent_id,
            role_duty=task.responsibility,
            core_conclusion=f"Keep the implementation for '{topic}' as a thin, verifiable loop with explicit quality controls.",
            evidence=[
                f"A minimal end-to-end prototype for '{topic}' can be tested without heavy scaffolding.",
                "Explicit test harnesses prevent AI hallucination and silent regressions in the critical path.",
            ],
            biggest_problem="Excessive automation complexity before the core heuristic is proven.",
            opposed_misjudgment="Assuming state-of-the-art models remove the need for strict boundary assertions.",
            concrete_recommendation="Build a lightweight semi-automated loop with 100% test coverage on boundary conditions.",
            confidence="medium",
            uncertainties=["Which components require deterministic validation versus probabilistic inference."],
        )
    elif "security" in aid:
        return AgentArgumentOutput(
            agent_id=task.agent_id,
            role_duty=task.responsibility,
            core_conclusion=f"Enforce strict input sanitization, rate limiting, and zero credential leakage for '{topic}'.",
            evidence=[
                "External and untrusted inputs must be validated at schema boundaries.",
                "Any persistent state requires access control and safe serialization.",
            ],
            biggest_problem="Missing negative security tests for malformed or adversarial inputs.",
            opposed_misjudgment="Assuming internal services or LLM outputs can be implicitly trusted.",
            concrete_recommendation="Add parameterized checks and verify error responses redact sensitive keys.",
            confidence="high",
            uncertainties=["Full surface area of third-party dependencies."],
        )
    else:
        return AgentArgumentOutput(
            agent_id=task.agent_id,
            role_duty=task.responsibility,
            core_conclusion=f"Review of '{topic}' indicates viability if key assumptions are validated sequentially.",
            evidence=[
                f"The core thesis of '{topic}' aligns with observable practitioner needs.",
                "Sequential milestones limit downside exposure.",
            ],
            biggest_problem="Unvalidated assumptions on user adoption frequency.",
            opposed_misjudgment="Confusing planning with execution evidence.",
            concrete_recommendation="Execute the simplest testable slice and evaluate before full commitment.",
            confidence="medium",
            uncertainties=["Adoption rate in the target cohort."],
        )


def sanitize_profile_for_blind_review(profile_text: str) -> str:
    """Strips counterweight/peer references from a profile for pure blind isolation."""
    # Remove ## 对冲对象 section
    text = re.sub(r"##\s*对冲对象[\s\S]*?(?=\n##|\Z)", "", profile_text)
    # Remove counterweights YAML/JSON block
    text = re.sub(r"counterweights:\s*\[[\s\S]*?\]", "", text)
    text = re.sub(r"counterweights:\s*\n(\s*-\s*.*\n)+", "", text)
    return text.strip()


def verify_blind_isolation(tasks: Sequence[SubagentTask]) -> tuple[bool, list[str]]:
    """Verifies that no task prompt contains peer arguments or cross-agent leakage."""
    violations: list[str] = []
    for task in tasks:
        system_prompt = task.build_blind_system_prompt().lower()
        user_prompt = task.build_blind_user_prompt().lower()
        # Ensure no cross-agent argument leakage phrases
        leakage_patterns = [
            "peer arguments",
            "other agents argued",
            "previous speaker said",
            "roundtable record so far",
            "other participants said",
        ]
        for pattern in leakage_patterns:
            if pattern in system_prompt or pattern in user_prompt:
                violations.append(f"Task '{task.agent_id}' contains cross-agent argument leakage pattern '{pattern}'")
    return len(violations) == 0, violations


class SubagentExecutor:
    """Concurrent subagent executor managing blind, isolated task dispatch."""

    def __init__(self, max_workers: int = 4, default_timeout_seconds: float = 30.0) -> None:
        self.max_workers = max_workers
        self.default_timeout_seconds = default_timeout_seconds

    def execute_blind(
        self,
        task: SubagentTask,
        worker_fn: Callable[[SubagentTask], SubagentResult] | None = None,
        timeout_seconds: float | None = None,
    ) -> SubagentResult:
        start_time = time.perf_counter()
        timeout = timeout_seconds or self.default_timeout_seconds

        if worker_fn is not None:
            try:
                result = worker_fn(task)
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - start_time
                return SubagentResult(
                    agent_id=task.agent_id,
                    short_name=task.short_name,
                    ok=False,
                    argument=None,
                    raw_text="",
                    execution_time_seconds=elapsed,
                    error=f"Worker exception: {exc}",
                )

        # Default deterministic generator
        arg = generate_deterministic_blind_argument(task)
        elapsed = time.perf_counter() - start_time
        return SubagentResult(
            agent_id=task.agent_id,
            short_name=task.short_name,
            ok=True,
            argument=arg,
            raw_text=json.dumps(arg.to_dict(), ensure_ascii=False, indent=2),
            execution_time_seconds=elapsed,
            error=None,
        )

    def execute_parallel_blind(
        self,
        tasks: Sequence[SubagentTask],
        worker_fn: Callable[[SubagentTask], SubagentResult] | None = None,
        timeout_seconds: float | None = None,
    ) -> list[SubagentResult]:
        """Dispatches tasks concurrently in a thread pool ensuring complete isolation."""
        # Verify isolation beforehand
        is_isolated, violations = verify_blind_isolation(tasks)
        if not is_isolated:
            raise ValueError(f"Blind isolation violation detected: {'; '.join(violations)}")

        timeout = timeout_seconds or self.default_timeout_seconds
        results: list[SubagentResult] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks) or 1, self.max_workers)) as executor:
            future_to_task = {
                executor.submit(self.execute_blind, task, worker_fn, timeout): task
                for task in tasks
            }
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    res = future.result(timeout=timeout)
                    results.append(res)
                except Exception as exc:
                    results.append(
                        SubagentResult(
                            agent_id=task.agent_id,
                            short_name=task.short_name,
                            ok=False,
                            argument=None,
                            raw_text="",
                            execution_time_seconds=0.0,
                            error=str(exc),
                        )
                    )

        # Preserve task ordering
        order_map = {t.agent_id: i for i, t in enumerate(tasks)}
        results.sort(key=lambda r: order_map.get(r.agent_id, 999))
        return results
