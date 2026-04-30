from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DIMENSIONS = [
    "problem_reframing",
    "key_variables",
    "assumption_separation",
    "opposition_quality",
    "risk_to_action",
    "next_testable_step",
    "uncertainty_disclosure",
]

BLOCKING_DIMENSIONS = {"next_testable_step", "uncertainty_disclosure"}


@dataclass(frozen=True)
class RubricResult:
    rubric_scores: dict[str, int]
    total: int
    blocking_dimensions: list[str]
    quality_pass: bool
    expected_pass: bool
    expected_result_met: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_scores": self.rubric_scores,
            "total": self.total,
            "blocking_dimensions": self.blocking_dimensions,
            "quality_pass": self.quality_pass,
            "expected_pass": self.expected_pass,
            "expected_result_met": self.expected_result_met,
        }


def evaluate_case(case: dict[str, Any]) -> RubricResult:
    output = str(case["fixture_output"])
    text = output.lower()
    expected_scores_min = case.get("expected_scores_min", {})
    rubric_scores = {
        "problem_reframing": score_problem_reframing(text),
        "key_variables": score_key_variables(text, case),
        "assumption_separation": score_assumption_separation(text),
        "opposition_quality": score_opposition_quality(text),
        "risk_to_action": score_risk_to_action(text),
        "next_testable_step": score_next_testable_step(text, case),
        "uncertainty_disclosure": score_uncertainty_disclosure(text, case),
    }
    forbidden_present = [item for item in case.get("must_not", []) if str(item).lower() in text]
    below_min = [
        dimension
        for dimension, minimum in expected_scores_min.items()
        if rubric_scores.get(dimension, 0) < int(minimum)
    ]
    blocking_dimensions = sorted(
        {
            dimension
            for dimension, score in rubric_scores.items()
            if score == 0 and (dimension in BLOCKING_DIMENSIONS or dimension in case.get("blocking_rules", []))
        }
        | set(below_min)
    )
    total = sum(rubric_scores.values())
    quality_pass = total >= int(case.get("minimum_total", 10)) and not blocking_dimensions and not forbidden_present
    expected_pass = bool(case.get("expected_pass", True))
    return RubricResult(
        rubric_scores=rubric_scores,
        total=total,
        blocking_dimensions=blocking_dimensions + [f"forbidden:{item}" for item in forbidden_present],
        quality_pass=quality_pass,
        expected_pass=expected_pass,
        expected_result_met=quality_pass is expected_pass,
    )


def score_problem_reframing(text: str) -> int:
    if any(token in text for token in ["reframed decision", "the decision is whether", "not whether"]):
        return 2
    if any(token in text for token in ["decision", "whether", "should"]):
        return 1
    return 0


def score_key_variables(text: str, case: dict[str, Any]) -> int:
    required = [str(item).lower() for item in case.get("must_identify", [])]
    matched = [item for item in required if item in text]
    if len(matched) >= max(2, len(required)):
        return 2
    if matched or any(token in text for token in ["key variables", "threshold", "channel", "cost"]):
        return 1
    return 0


def score_assumption_separation(text: str) -> int:
    fact_markers = any(token in text for token in ["fact:", "facts:", "current revenue is unknown", "no live"])
    assumption_markers = any(token in text for token in ["assumption", "assumptions", "unknown", "uncertainty"])
    if fact_markers and assumption_markers:
        return 2
    if fact_markers or assumption_markers:
        return 1
    return 0


def score_opposition_quality(text: str) -> int:
    if any(token in text for token in ["opposition:", "risk:", "may hide", "increases fragility", "false validation"]):
        return 2
    if any(token in text for token in ["risk", "but", "however", "downside"]):
        return 1
    return 0


def score_risk_to_action(text: str) -> int:
    if any(token in text for token in ["risk-to-action", "stop if", "threshold", "milestone", "kill rule"]):
        return 2
    if any(token in text for token in ["risk", "action", "mitigate", "review"]):
        return 1
    return 0


def score_next_testable_step(text: str, case: dict[str, Any]) -> int:
    expected = str(case.get("expected_next_testable_step", "")).lower()
    if expected and expected in text:
        return 2
    if any(token in text for token in ["next testable step", "interview", "run", "test", "cohort", "users"]):
        return 1
    return 0


def score_uncertainty_disclosure(text: str, case: dict[str, Any]) -> int:
    required = [str(item).lower() for item in case.get("uncertainty_requirements", [])]
    matched = [item for item in required if item in text]
    if matched and any(token in text for token in ["uncertainty", "unknown", "unknowns", "missing evidence"]):
        return 2
    if matched or any(token in text for token in ["uncertainty", "unknown", "unknowns"]):
        return 1
    return 0
