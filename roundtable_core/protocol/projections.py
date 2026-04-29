from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from roundtable_core.protocol.handoff import runtime_packet_to_portable_handoff


def project_room_state_to_session(room_state: dict[str, Any], artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = artifacts or {}
    now = iso_now()
    agent_roles = room_state.get("agent_roles", {})
    panel = []
    for agent_id in room_state.get("agents", []):
        role = agent_roles.get(agent_id, {}) if isinstance(agent_roles, dict) else {}
        panel.append(
            {
                "agent_id": agent_id,
                "short_name": str(role.get("short_name") or agent_id),
                "role_summary": str(role.get("role_summary") or "Runtime-selected panel member."),
                "structural_role": str(role.get("structural_role") or "moderate"),
            }
        )

    handoff_packet = load_optional_json(artifacts.get("portable_handoff_packet"))
    if handoff_packet is None:
        legacy_packet = load_optional_json(artifacts.get("legacy_handoff_packet") or artifacts.get("handoff_packet"))
        if isinstance(legacy_packet, dict):
            if "handoff_packet" in legacy_packet:
                legacy_packet = legacy_packet["handoff_packet"]
            handoff_packet = runtime_packet_to_portable_handoff(legacy_packet)

    summaries = []
    if room_state.get("last_summary_turn") is not None:
        summaries.append(
            {
                "turn_id": room_state.get("last_summary_turn") or 0,
                "consensus_points": list(room_state.get("consensus_points", [])),
                "open_questions": list(room_state.get("open_questions", [])),
                "tension_points": list(room_state.get("tension_points", [])),
                "recommended_next_step": str(room_state.get("recommended_next_step") or "No recommended next step recorded."),
                "generated_at": now,
            }
        )

    return {
        "schema_version": "0.1.0",
        "session_id": room_state["room_id"],
        "workflow": "room",
        "user_question": room_state["original_topic"],
        "current_focus": room_state.get("active_focus"),
        "panel": panel,
        "turns": [normalize_room_turn(turn) for turn in room_state.get("conversation_log", [])],
        "summaries": summaries,
        "handoff_packet": handoff_packet,
        "claim_boundary": fixture_claim_boundary("room"),
        "created_at": now,
        "updated_at": now,
    }


def project_debate_artifacts_to_session(debate_artifacts: dict[str, Any]) -> dict[str, Any]:
    result = _project_debate_common(debate_artifacts)
    result.pop("result_id", None)
    return result


def project_debate_artifacts_to_result(debate_artifacts: dict[str, Any]) -> dict[str, Any]:
    common = _project_debate_common(debate_artifacts)
    common["result_id"] = f"debate-result-{common['session_id'].replace('debate-', '', 1)}"
    ordered = {
        "schema_version": common["schema_version"],
        "result_id": common["result_id"],
        "session_id": common["session_id"],
        "workflow": common["workflow"],
        "launch_bundle": common["launch_bundle"],
        "selected_panel": common["selected_panel"],
        "agent_arguments": common["agent_arguments"],
        "moderator_summary": common["moderator_summary"],
        "reviewer_result": common["reviewer_result"],
        "final_outcome": common["final_outcome"],
        "final_decision": common["final_decision"],
        "open_questions": common["open_questions"],
        "evidence": common["evidence"],
        "claim_boundary": common["claim_boundary"],
        "created_at": common["created_at"],
        "updated_at": common["updated_at"],
    }
    return ordered


def _project_debate_common(debate_artifacts: dict[str, Any]) -> dict[str, Any]:
    now = iso_now()
    launch_bundle = as_payload(debate_artifacts["launch_bundle"])
    roundtable_record = as_payload(debate_artifacts["roundtable_record"])
    review_result = as_payload(debate_artifacts["review_result"])
    handoff_packet = load_optional_json(debate_artifacts.get("portable_handoff_packet"))
    if handoff_packet is None:
        legacy_packet = load_optional_json(debate_artifacts.get("legacy_handoff_packet") or launch_bundle.get("source_packet_path"))
        if isinstance(legacy_packet, dict):
            handoff_packet = runtime_packet_to_portable_handoff(legacy_packet)

    final_outcome = "allow" if review_result.get("allow_final_decision") is True else "follow_up_required"
    final_decision = build_final_decision(roundtable_record, review_result) if final_outcome == "allow" else None
    evidence_buckets = roundtable_record.get("evidence_buckets", {})
    moderator_summary = roundtable_record.get("moderator_summary", {})

    return {
        "schema_version": "0.1.0",
        "session_id": launch_bundle["debate_id"],
        "workflow": "debate",
        "input_source": launch_bundle.get("source_kind", "room_handoff"),
        "source_room_id": launch_bundle.get("source_room_id"),
        "handoff_packet": handoff_packet,
        "launch_bundle": normalize_launch_bundle(launch_bundle),
        "selected_panel": normalize_participants(launch_bundle.get("participants", [])),
        "agent_arguments": list(roundtable_record.get("agent_outputs", [])),
        "moderator_summary": normalize_moderator_summary(moderator_summary, launch_bundle.get("participants", [])),
        "reviewer_result": normalize_review_result(review_result),
        "final_outcome": final_outcome,
        "final_decision": final_decision,
        "open_questions": list(evidence_buckets.get("uncertainties", [])),
        "evidence": {
            "facts": list(evidence_buckets.get("facts", [])),
            "inferences": list(evidence_buckets.get("inferences", [])),
            "uncertainties": list(evidence_buckets.get("uncertainties", [])),
            "recommendations": list(evidence_buckets.get("recommendations", [])),
        },
        "claim_boundary": fixture_claim_boundary("debate"),
        "created_at": now,
        "updated_at": now,
    }


def normalize_review_result(review_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_applicable": review_result["review_applicable"],
        "overall_score": review_result["overall_score"],
        "best_agent": review_result["best_agent"],
        "weak_agents": list(review_result.get("weak_agents", [])),
        "evidence_gaps": list(review_result.get("evidence_gaps", [])),
        "logic_gaps": list(review_result.get("logic_gaps", [])),
        "overlooked_issues": list(review_result.get("overlooked_issues", [])),
        "severe_red_flags": list(review_result.get("severe_red_flags", [])),
        "allow_final_decision": review_result["allow_final_decision"],
        "required_followups": list(review_result.get("required_followups", [])),
        "rationale": review_result["rationale"],
    }


def normalize_room_turn(turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn_id": turn["turn_id"],
        "stage": turn["stage"],
        "active_focus": turn.get("active_focus"),
        "user_input": turn["user_input"],
        "speakers": list(turn.get("speakers", [])),
        "cited_agents": list(turn.get("cited_agents", [])),
        "warnings": list(turn.get("warnings", [])),
        "meta": dict(turn.get("meta", {})),
    }


def normalize_launch_bundle(launch_bundle: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(launch_bundle)
    normalized["participants"] = normalize_participants(launch_bundle.get("participants", []))
    return normalized


def normalize_participants(participants: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in participants if isinstance(participants, list) else []:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "agent_id": item["agent_id"],
                "short_name": item["short_name"],
                "responsibility": item["responsibility"],
            }
        )
    return normalized


def normalize_moderator_summary(summary: dict[str, Any], participants: Any) -> dict[str, Any]:
    normalized = dict(summary)
    short_names = {
        item["agent_id"]: item["short_name"]
        for item in participants
        if isinstance(item, dict) and "agent_id" in item and "short_name" in item
    } if isinstance(participants, list) else {}
    normalized["participants_and_roles"] = [
        {
            "agent_id": item["agent_id"],
            "short_name": item.get("short_name") or short_names.get(item["agent_id"], item["agent_id"]),
            "responsibility": item["responsibility"],
        }
        for item in summary.get("participants_and_roles", [])
        if isinstance(item, dict) and "agent_id" in item and "responsibility" in item
    ]
    return normalized


def build_final_decision(roundtable_record: dict[str, Any], review_result: dict[str, Any]) -> dict[str, Any]:
    moderator = roundtable_record.get("moderator_summary", {})
    evidence = roundtable_record.get("evidence_buckets", {})
    recommendations = [str(item) for item in evidence.get("recommendations", []) if str(item).strip()]
    risks = [str(item) for item in evidence.get("uncertainties", []) if str(item).strip()]
    reasons = [str(item) for item in moderator.get("consensus_points", []) if str(item).strip()]
    if review_result.get("rationale"):
        reasons.append(str(review_result["rationale"]))
    return {
        "recommendation": str(moderator.get("preliminary_recommendation") or first_or_default(recommendations, "Run a bounded validation.")),
        "reasons": reasons or ["Reviewer allowed final decision."],
        "risks": risks,
        "next_action": first_or_default(recommendations, "Run the next bounded validation step."),
        "stop_condition": first_or_default(risks, "Stop if the core validation signal is not observed."),
        "review_point": "Review after the next bounded validation run or if a severe red flag appears.",
    }


def fixture_claim_boundary(workflow: str) -> dict[str, Any]:
    return {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": [
            f"{workflow} projection was generated from fixture-backed local runtime artifacts.",
            "This is not host-live or provider-live evidence.",
        ],
    }


def as_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, Path):
        return json.loads(value.read_text(encoding="utf-8"))
    if isinstance(value, str):
        return json.loads(Path(value).read_text(encoding="utf-8"))
    raise TypeError(f"Expected dict or JSON path, got {type(value).__name__}")


def load_optional_json(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        return as_payload(value)
    except (FileNotFoundError, TypeError, json.JSONDecodeError):
        return None


def first_or_default(values: list[str], default: str) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return default


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
