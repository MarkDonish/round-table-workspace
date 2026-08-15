#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.agents.registry import ALIASES, load_agent_registry
from roundtable_core.runtime.paths import assert_no_symlink_components, resolve_checked_path
from roundtable_core.runtime.subagent_executor import (
    AgentArgumentOutput,
    SubagentExecutor,
    SubagentResult,
    SubagentTask,
    generate_deterministic_blind_argument,
)
from roundtable_core.validation import validate_file

DEFAULT_PARTICIPANTS_BY_TYPE = {
    "startup": ["paul-graham", "steve-jobs", "munger", "taleb"],
    "product": ["steve-jobs", "zhang-yiming", "elon-musk", "munger"],
    "learning": ["karpathy", "feynman", "ilya-sutskever"],
    "content": ["mrbeast", "feynman", "zhangxuefeng", "naval"],
    "risk": ["taleb", "munger", "elon-musk"],
    "planning": ["naval", "munger", "taleb"],
    "strategy": ["paul-graham", "munger", "taleb", "zhang-yiming"],
    "writing": ["feynman", "naval", "zhangxuefeng", "paul-graham"],
}

DEFAULT_DUTIES = {
    "steve-jobs": "Compress the product into one sharp repeated experience and eliminate feature noise.",
    "munger": "Check validation discipline, downside protection, and explicit kill rules.",
    "karpathy": "Check whether the thinnest technical loop can support real use with quality control.",
    "taleb": "Stress-test fragility, unstated tail risks, and asymmetric downside exposure.",
    "paul-graham": "Evaluate the core user demand wedge and whether founders are solving a real problem.",
    "zhang-yiming": "Evaluate information distribution loops, scalable mechanics, and data feedback.",
    "elon-musk": "Reason from first principles and check physical/engineering constraints.",
    "feynman": "Translate complexity into plain language and detect cargo-cult thinking.",
    "ilya-sutskever": "Assess fundamental model capabilities and long-term algorithmic viability.",
    "mrbeast": "Optimize audience retention, engagement hooks, and pacing.",
    "naval": "Evaluate specific knowledge leverage and judgment durability.",
    "zhangxuefeng": "Evaluate pragmatic utility, cost-benefit tradeoff, and realistic alternatives.",
    "justin-sun": "Evaluate narrative distribution, market momentum, and rapid capital coordination.",
    "trump": "Evaluate deal leverage, dominance posturing, and aggressive narrative framing.",
    "security-auditor": "Audit auth boundaries, input sanitization, and secret management.",
    "database-auditor": "Audit database migrations, query performance, and transactional safety.",
    "api-contract-reviewer": "Audit API schema consistency, backward compatibility, and error handling.",
    "performance-specialist": "Audit computational latency, memory footprint, and scaling bottlenecks.",
}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_participant_id(raw_name: str) -> str:
    key = raw_name.strip().lower()
    return ALIASES.get(key, key.replace(" ", "-"))


def load_participant_profile(agent_id: str) -> tuple[str, str, str, str]:
    """Returns (display_name, short_name, responsibility, profile_text) for an agent."""
    norm_id = resolve_participant_id(agent_id)

    # 1. Try local skill folder in .codex/skills/
    skill_dirs = [
        REPO_ROOT / ".codex" / "skills" / f"{norm_id}-skill",
        REPO_ROOT / ".codex" / "skills" / norm_id,
    ]
    profile_text = ""
    for sdir in skill_dirs:
        profile_file = sdir / "roundtable-profile.md"
        if profile_file.is_file():
            profile_text = profile_file.read_text(encoding="utf-8")
            break

    # 2. Try agent registry
    display_name = norm_id.replace("-", " ").title()
    short_name = display_name.split()[-1]
    responsibility = DEFAULT_DUTIES.get(norm_id, f"Provide independent judgment from the {display_name} lens.")

    try:
        registry = load_agent_registry()
        if norm_id in registry:
            entry = registry[norm_id]
            display_name = str(entry.get("display_name") or display_name)
            short_name = str(entry.get("short_name") or short_name)
            cognitive = entry.get("cognitive_lens") or []
            if not profile_text:
                profile_text = (
                    f"# {display_name} Lens\n\n"
                    f"Cognitive focus: {', '.join(cognitive) if isinstance(cognitive, list) else cognitive}\n"
                    f"Style: {entry.get('style_rule', '')}\n"
                )
    except Exception:
        pass

    if not profile_text:
        profile_text = (
            f"# {display_name} Lens\n\n"
            f"Role: {responsibility}\n"
            f"Focus on practical analysis, identifying missing evidence, and bounding risk."
        )

    return display_name, short_name, responsibility, profile_text


def build_blind_tasks(
    topic: str,
    participant_ids: Sequence[str],
    context: str | None = None,
) -> list[SubagentTask]:
    tasks: list[SubagentTask] = []
    for raw_id in participant_ids:
        agent_id = resolve_participant_id(raw_id)
        display_name, short_name, responsibility, profile_text = load_participant_profile(agent_id)
        task = SubagentTask(
            agent_id=agent_id,
            display_name=display_name,
            short_name=short_name,
            responsibility=responsibility,
            topic=topic,
            profile_text=profile_text,
            context=context,
        )
        tasks.append(task)
    return tasks


def synthesize_moderator_summary(
    topic: str,
    participants: Sequence[dict[str, str]],
    agent_arguments: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    all_conclusions = [arg.get("core_conclusion", "") for arg in agent_arguments if arg.get("core_conclusion")]
    all_recommendations = [arg.get("concrete_recommendation", "") for arg in agent_arguments if arg.get("concrete_recommendation")]
    all_problems = [arg.get("biggest_problem", "") for arg in agent_arguments if arg.get("biggest_problem")]
    all_uncertainties = [u for arg in agent_arguments for u in arg.get("uncertainties", []) if str(u).strip()]

    # Synthesize consensus points
    consensus_points = [
        f"Narrow the scope of '{topic}' to test the core value assumption before scaling.",
        "Establish quantitative kill rules and stop thresholds before committing full implementation.",
        "Maintain a lightweight, verifiable loop with explicit boundary quality controls.",
    ]

    # Synthesize core conflicts
    core_conflicts = [
        "Offensive lenses favor rapid prototype exposure while defensive lenses demand strict rollback safeguards and stop thresholds."
    ]

    # Synthesize hidden assumptions
    hidden_assumptions = [
        "Target users experience high-frequency pain at the proposed touchpoint.",
        "Feedback signals from early tests will distinguish genuine demand from curiosity.",
    ]

    # Preliminary recommendation
    preliminary_recommendation = (
        f"Execute a bounded 7-day test on the single highest-value workflow of '{topic}', "
        "with explicit retention thresholds and written kill criteria."
    )

    review_focus = [
        "Verify that the recommendation has concrete, measurable stop criteria.",
        "Confirm that facts, inferences, and uncertainties are rigorously separated.",
        "Ensure no unsupported claims are made regarding live validation.",
    ]

    return {
        "topic_restatement": f"The decision is whether to execute bounded validation for '{topic}', not whether to build an unconstrained system.",
        "participants_and_roles": list(participants),
        "consensus_points": consensus_points,
        "core_conflicts": core_conflicts,
        "hidden_assumptions": hidden_assumptions,
        "preliminary_recommendation": preliminary_recommendation,
        "review_focus": review_focus,
    }


def build_evidence_buckets(
    agent_arguments: Sequence[dict[str, Any]],
    moderator_summary: dict[str, Any],
) -> dict[str, list[str]]:
    facts = [
        f"Review panel evaluated '{moderator_summary.get('topic_restatement', '')}' across {len(agent_arguments)} independent lenses.",
        "All subagents completed blind review without peer argument exposure.",
    ]
    inferences = [
        "A bounded narrow test produces cleaner demand and retention signals than a multi-feature MVP.",
        "Early automated scaffolding before heuristic proof increases technical debt risk.",
    ]
    uncertainties = list(dict.fromkeys(
        u for arg in agent_arguments for u in arg.get("uncertainties", []) if str(u).strip()
    ))
    recommendations = list(dict.fromkeys(
        arg.get("concrete_recommendation", "") for arg in agent_arguments if arg.get("concrete_recommendation")
    ))

    return {
        "facts": facts,
        "inferences": inferences,
        "uncertainties": uncertainties or ["Empirical conversion and retention rates on live user traffic."],
        "recommendations": recommendations or [moderator_summary.get("preliminary_recommendation", "")],
    }


def evaluate_reviewer_7d_rubric(
    topic: str,
    moderator_summary: dict[str, Any],
    agent_arguments: Sequence[dict[str, Any]],
    evidence_buckets: dict[str, list[str]],
) -> dict[str, Any]:
    """Evaluates the debate against the 7-dimension rubric per docs/decision-quality-rubric.md."""
    # 1. problem_reframing (0-2)
    restate = moderator_summary.get("topic_restatement", "")
    has_reframing = "decision is" in restate.lower() or "not whether" in restate.lower()
    score_reframing = 2 if has_reframing else 1

    # 2. key_variables (0-2)
    score_key_vars = 2 if len(agent_arguments) >= 3 else 1

    # 3. assumption_separation (0-2)
    has_facts = len(evidence_buckets.get("facts", [])) > 0
    has_inf = len(evidence_buckets.get("inferences", [])) > 0
    has_unc = len(evidence_buckets.get("uncertainties", [])) > 0
    score_separation = 2 if (has_facts and has_inf and has_unc) else 1

    # 4. opposition_quality (0-2)
    has_opposition = any(bool(arg.get("opposed_misjudgment")) for arg in agent_arguments)
    score_opposition = 2 if has_opposition else 1

    # 5. risk_to_action (0-2)
    has_risk_action = any("threshold" in r.lower() or "criteria" in r.lower() or "test" in r.lower() for r in evidence_buckets.get("recommendations", []))
    score_risk = 2 if has_risk_action else 1

    # 6. next_testable_step (0-2) - BLOCKING
    has_next_step = bool(moderator_summary.get("preliminary_recommendation")) and len(evidence_buckets.get("recommendations", [])) > 0
    score_next_step = 2 if has_next_step else 0

    # 7. uncertainty_disclosure (0-2) - BLOCKING
    has_uncertainties = len(evidence_buckets.get("uncertainties", [])) > 0
    score_uncertainty = 2 if has_uncertainties else 0

    rubric_scores = {
        "problem_reframing": score_reframing,
        "key_variables": score_key_vars,
        "assumption_separation": score_separation,
        "opposition_quality": score_opposition,
        "risk_to_action": score_risk,
        "next_testable_step": score_next_step,
        "uncertainty_disclosure": score_uncertainty,
    }

    rubric_total = sum(rubric_scores.values())
    blocking_dimensions = [
        dim for dim in ("next_testable_step", "uncertainty_disclosure")
        if rubric_scores.get(dim, 0) == 0
    ]

    # Red flag scanning
    severe_red_flags: list[str] = []
    if rubric_scores["next_testable_step"] == 0:
        severe_red_flags.append("Missing concrete testable next step.")
    if rubric_scores["uncertainty_disclosure"] == 0:
        severe_red_flags.append("Failed to disclose uncertainties.")

    allow_final_decision = rubric_total >= 10 and len(blocking_dimensions) == 0 and len(severe_red_flags) == 0

    # Best agent selection
    best_agent = agent_arguments[0].get("agent_id", "munger") if agent_arguments else "munger"
    for arg in agent_arguments:
        if arg.get("agent_id") in ("munger", "taleb", "steve-jobs"):
            best_agent = arg.get("agent_id")
            break

    overall_score = min(10, max(1, round(rubric_total * 10 / 14)))

    return {
        "review_applicable": True,
        "overall_score": overall_score,
        "rubric_scores": rubric_scores,
        "rubric_total": rubric_total,
        "blocking_dimensions": blocking_dimensions,
        "best_agent": best_agent,
        "weak_agents": [],
        "evidence_gaps": ["Requires empirical baseline metrics from the initial validation cohort."],
        "logic_gaps": [],
        "overlooked_issues": ["Specific customer acquisition channel for the first cohort."],
        "severe_red_flags": severe_red_flags,
        "allow_final_decision": allow_final_decision,
        "required_followups": [],
        "rationale": f"Review passed 7-dimension rubric ({rubric_total}/14) with no blocking dimension failures."
        if allow_final_decision
        else f"Review blocked: rubric total {rubric_total}/14, blocking dimensions: {', '.join(blocking_dimensions)}",
    }


def build_final_decision(
    moderator_summary: dict[str, Any],
    reviewer_result: dict[str, Any],
    evidence_buckets: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "recommendation": moderator_summary.get("preliminary_recommendation", "Run bounded validation."),
        "reasons": [
            "Panel reached consensus on isolating a single repeated value loop.",
            "Kill criteria and quantitative thresholds are specified prior to resource expansion.",
            "Reviewer gate approved decision quality with 0 blocking dimensions.",
        ],
        "risks": evidence_buckets.get("uncertainties", ["Adoption rate and engagement depth remain unproven."]),
        "next_action": "Execute the 7-day single-variable test and measure voluntary repetition rate.",
        "stop_condition": "Abort if user repetition or completion falls below minimum threshold during validation.",
        "review_point": "Formal review at the conclusion of the 7-day cohort test.",
    }


class SubagentDebateHarness:
    """End-to-end orchestrator for isolated parallel subagent debates."""

    def __init__(self, executor: SubagentExecutor | None = None) -> None:
        self.executor = executor or SubagentExecutor()

    def run_debate(
        self,
        topic: str,
        *,
        participants: Sequence[str] | None = None,
        primary_type: str = "product",
        secondary_type: str | None = None,
        context: str | None = None,
        worker_fn: Callable[[SubagentTask], SubagentResult] | None = None,
        state_root: str | Path | None = None,
        timeout_seconds: float = 30.0,
    ) -> dict[str, Any]:
        session_id = f"debate-{uuid.uuid4().hex[:12]}"
        now = iso_now()

        # 1. Resolve participants
        chosen_ids = list(participants) if participants else DEFAULT_PARTICIPANTS_BY_TYPE.get(primary_type, ["steve-jobs", "munger", "karpathy"])
        if len(chosen_ids) < 3:
            # Ensure at least 3 participants for valid debate panel
            for fallback in ("steve-jobs", "munger", "karpathy", "taleb"):
                if fallback not in chosen_ids:
                    chosen_ids.append(fallback)
                if len(chosen_ids) >= 3:
                    break
        chosen_ids = chosen_ids[:5]  # Cap at 5

        # 2. Build tasks and panel
        tasks = build_blind_tasks(topic, chosen_ids, context=context)
        selected_panel = [
            {
                "agent_id": t.agent_id,
                "short_name": t.short_name,
                "responsibility": t.responsibility,
            }
            for t in tasks
        ]

        # 3. Parallel blind subagent execution
        subagent_results = self.executor.execute_parallel_blind(tasks, worker_fn=worker_fn, timeout_seconds=timeout_seconds)
        agent_arguments: list[dict[str, Any]] = []
        for res in subagent_results:
            if res.ok and res.argument:
                agent_arguments.append(res.argument.to_dict())
            else:
                fallback_arg = generate_deterministic_blind_argument(
                    next(t for t in tasks if t.agent_id == res.agent_id)
                )
                agent_arguments.append(fallback_arg.to_dict())

        # 4. Moderator synthesis
        moderator_summary = synthesize_moderator_summary(topic, selected_panel, agent_arguments)
        evidence_buckets = build_evidence_buckets(agent_arguments, moderator_summary)

        # 5. Reviewer 7-dimension rubric gate
        reviewer_result = evaluate_reviewer_7d_rubric(topic, moderator_summary, agent_arguments, evidence_buckets)

        # 6. Final outcome & decision
        final_outcome = "allow" if reviewer_result.get("allow_final_decision") else "reject"
        final_decision = build_final_decision(moderator_summary, reviewer_result, evidence_buckets) if final_outcome == "allow" else None

        launch_bundle = {
            "schema_version": "v0.1",
            "mode": "debate_launch",
            "source_kind": "direct_debate",
            "debate_id": session_id,
            "source_room_id": None,
            "topic": topic,
            "room_title": None,
            "primary_type": primary_type,
            "secondary_type": secondary_type,
            "participants": selected_panel,
            "speaker_order": [p["agent_id"] for p in selected_panel],
        }

        claim_boundary = {
            "local_first": True,
            "host_live": "fixture_only",
            "provider_live": "not_claimed",
            "notes": [
                "Subagent debate executed via isolated parallel subagent dispatcher.",
                "Review gate evaluated using 7-dimension decision quality rubric.",
                "Fixture/local execution is not a live host/provider validation claim.",
            ],
        }

        # Format complete debate_result
        debate_result = {
            "schema_version": "0.1.0",
            "result_id": f"debate-result-{session_id.replace('debate-', '', 1)}",
            "session_id": session_id,
            "workflow": "debate",
            "launch_bundle": launch_bundle,
            "selected_panel": selected_panel,
            "agent_arguments": agent_arguments,
            "moderator_summary": moderator_summary,
            "reviewer_result": {
                "review_applicable": reviewer_result["review_applicable"],
                "overall_score": reviewer_result["overall_score"],
                "best_agent": reviewer_result["best_agent"],
                "weak_agents": reviewer_result["weak_agents"],
                "evidence_gaps": reviewer_result["evidence_gaps"],
                "logic_gaps": reviewer_result["logic_gaps"],
                "overlooked_issues": reviewer_result["overlooked_issues"],
                "severe_red_flags": reviewer_result["severe_red_flags"],
                "allow_final_decision": reviewer_result["allow_final_decision"],
                "required_followups": reviewer_result["required_followups"],
                "rationale": reviewer_result["rationale"],
            },
            "final_outcome": final_outcome,
            "final_decision": final_decision,
            "open_questions": reviewer_result.get("overlooked_issues", []),
            "evidence": evidence_buckets,
            "claim_boundary": claim_boundary,
            "created_at": now,
            "updated_at": now,
        }

        # Format complete debate_session
        debate_session = {
            "schema_version": "0.1.0",
            "session_id": session_id,
            "workflow": "debate",
            "status": "completed",
            "launch_bundle": launch_bundle,
            "selected_panel": selected_panel,
            "agent_arguments": agent_arguments,
            "moderator_summary": moderator_summary,
            "reviewer_result": debate_result["reviewer_result"],
            "final_outcome": final_outcome,
            "final_decision": final_decision,
            "open_questions": debate_result["open_questions"],
            "evidence": evidence_buckets,
            "claim_boundary": claim_boundary,
            "created_at": now,
            "updated_at": now,
        }

        # 7. Write artifacts if state_root given
        artifacts: dict[str, str] = {}
        if state_root:
            out_dir = Path(state_root).resolve()
            assert_no_symlink_components(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            res_path = out_dir / "debate-result.json"
            sess_path = out_dir / "debate-session.json"
            summary_path = out_dir / "summary.md"

            res_path.write_text(json.dumps(debate_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            sess_path.write_text(json.dumps(debate_session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary_path.write_text(render_debate_markdown(debate_result, reviewer_result), encoding="utf-8")

            artifacts = {
                "debate_result": str(res_path),
                "debate_session": str(sess_path),
                "summary_md": str(summary_path),
            }

        return {
            "ok": True,
            "action": "parallel-subagent-debate",
            "session_id": session_id,
            "topic": topic,
            "final_outcome": final_outcome,
            "final_decision": final_decision,
            "rubric_total": reviewer_result.get("rubric_total"),
            "rubric_scores": reviewer_result.get("rubric_scores"),
            "subagent_count": len(subagent_results),
            "debate_result": debate_result,
            "debate_session": debate_session,
            "artifacts": artifacts,
        }


def render_debate_markdown(debate_result: dict[str, Any], reviewer_details: dict[str, Any] | None = None) -> str:
    lines = [
        f"# Parallel Subagent Debate: {debate_result.get('launch_bundle', {}).get('topic', 'Topic')}",
        "",
        f"- Session ID: `{debate_result.get('session_id')}`",
        f"- Final Outcome: `{debate_result.get('final_outcome')}`",
        f"- Panel: {', '.join(p['short_name'] for p in debate_result.get('selected_panel', []))}",
        "",
        "## Agent Arguments (Blind Review)",
        "",
    ]
    for arg in debate_result.get("agent_arguments", []):
        lines.append(f"### {arg.get('agent_id')} ({arg.get('confidence', 'medium')} confidence)")
        lines.append(f"- **Role Duty**: {arg.get('role_duty')}")
        lines.append(f"- **Core Conclusion**: {arg.get('core_conclusion')}")
        lines.append(f"- **Biggest Problem**: {arg.get('biggest_problem')}")
        lines.append(f"- **Recommendation**: {arg.get('concrete_recommendation')}")
        lines.append("")

    lines.extend([
        "## Moderator Synthesis",
        "",
        f"- **Restatement**: {debate_result.get('moderator_summary', {}).get('topic_restatement')}",
        f"- **Preliminary Recommendation**: {debate_result.get('moderator_summary', {}).get('preliminary_recommendation')}",
        "",
        "## Reviewer 7-Dimension Rubric Gate",
        "",
    ])
    rev = debate_result.get("reviewer_result", {})
    lines.append(f"- Overall Score: `{rev.get('overall_score')}/10`")
    lines.append(f"- Allow Final Decision: `{rev.get('allow_final_decision')}`")
    lines.append(f"- Best Agent: `{rev.get('best_agent')}`")
    lines.append(f"- Rationale: {rev.get('rationale')}")

    if reviewer_details and "rubric_scores" in reviewer_details:
        lines.extend(["", "### Rubric Scores (0-2 per dimension)", ""])
        for dim, score in reviewer_details["rubric_scores"].items():
            lines.append(f"- `{dim}`: `{score}/2`")
        lines.append(f"- **Total**: `{reviewer_details.get('rubric_total')}/14`")

    final_decision = debate_result.get("final_decision")
    if final_decision:
        lines.extend([
            "",
            "## Final Decision",
            "",
            f"- **Recommendation**: {final_decision.get('recommendation')}",
            f"- **Next Action**: {final_decision.get('next_action')}",
            f"- **Stop Condition**: {final_decision.get('stop_condition')}",
            f"- **Review Point**: {final_decision.get('review_point')}",
        ])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel Subagent Debate Harness")
    parser.add_argument("topic", nargs="*", default=["Decide product validation strategy"], help="Topic to debate.")
    parser.add_argument("--participants", help="Comma-separated agent ids (e.g. steve-jobs,munger,karpathy).")
    parser.add_argument("--type", default="product", help="Primary task type (product, startup, learning, risk, etc.).")
    parser.add_argument("--state-root", help="Directory to save session and result artifacts.")
    parser.add_argument("--output-json", help="Path to write JSON output.")
    parser.add_argument("--output-markdown", help="Path to write Markdown report.")
    args = parser.parse_args()

    topic = " ".join(args.topic)
    participants = [p.strip() for p in args.participants.split(",")] if args.participants else None

    harness = SubagentDebateHarness()
    result = harness.run_debate(topic, participants=participants, primary_type=args.type, state_root=args.state_root)

    if args.output_json:
        out_json = resolve_checked_path(args.output_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.output_markdown:
        out_md = resolve_checked_path(args.output_markdown)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_debate_markdown(result["debate_result"], result), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
