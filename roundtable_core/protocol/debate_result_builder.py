from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from roundtable_core.protocol.handoff import runtime_packet_to_portable_handoff


def build_debate_result(
    *,
    launch_bundle: dict[str, Any],
    roundtable_record: dict[str, Any],
    review_packet: dict[str, Any],
    review_result: dict[str, Any],
    optional_followup: dict[str, Any] | None = None,
    handoff_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = iso_now()
    final_outcome = decide_final_outcome(review_result, optional_followup)
    final_decision = (
        build_final_decision(roundtable_record, review_result, optional_followup)
        if final_outcome == "allow"
        else None
    )
    evidence_buckets = roundtable_record.get("evidence_buckets", {})
    moderator_summary = roundtable_record.get("moderator_summary", {})
    session_id = str(launch_bundle["debate_id"])
    return {
        "schema_version": "0.1.0",
        "result_id": f"debate-result-{session_id.replace('debate-', '', 1)}",
        "session_id": session_id,
        "workflow": "debate",
        "launch_bundle": normalize_launch_bundle(launch_bundle),
        "selected_panel": normalize_participants(launch_bundle.get("participants", [])),
        "agent_arguments": list(roundtable_record.get("agent_outputs", [])),
        "moderator_summary": normalize_moderator_summary(moderator_summary, launch_bundle.get("participants", [])),
        "reviewer_result": normalize_review_result(review_result),
        "final_outcome": final_outcome,
        "final_decision": final_decision,
        "open_questions": collect_open_questions(evidence_buckets, review_result, optional_followup),
        "evidence": {
            "facts": list(evidence_buckets.get("facts", [])),
            "inferences": list(evidence_buckets.get("inferences", [])),
            "uncertainties": list(evidence_buckets.get("uncertainties", [])),
            "recommendations": list(evidence_buckets.get("recommendations", [])),
        },
        "claim_boundary": fixture_claim_boundary(handoff_packet, review_packet),
        "created_at": now,
        "updated_at": now,
    }


def build_debate_result_from_artifacts(debate_artifacts: dict[str, Any]) -> dict[str, Any]:
    launch_bundle = as_payload(debate_artifacts["launch_bundle"])
    roundtable_record = as_payload(debate_artifacts["roundtable_record"])
    review_packet = as_payload(debate_artifacts["review_packet"])
    review_result = as_payload(debate_artifacts["review_result"])
    optional_followup = load_optional_json(debate_artifacts.get("optional_followup"))
    handoff_packet = load_optional_json(debate_artifacts.get("portable_handoff_packet"))
    if handoff_packet is None:
        legacy_packet = load_optional_json(debate_artifacts.get("legacy_handoff_packet") or launch_bundle.get("source_packet_path"))
        if isinstance(legacy_packet, dict):
            handoff_packet = runtime_packet_to_portable_handoff(legacy_packet)
    return build_debate_result(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        review_packet=review_packet,
        review_result=review_result,
        optional_followup=optional_followup,
        handoff_packet=handoff_packet,
    )


def decide_final_outcome(review_result: dict[str, Any], optional_followup: dict[str, Any] | None = None) -> str:
    if review_result.get("allow_final_decision") is True:
        return "allow"
    if review_result.get("final_outcome") == "reject" or review_result.get("rejected") is True:
        return "reject"
    if review_result.get("severe_red_flags"):
        return "reject"
    if review_result.get("required_followups") or (optional_followup and optional_followup.get("required_followups")):
        return "follow_up_required"
    return "follow_up_required"


def build_final_decision(
    roundtable_record: dict[str, Any],
    review_result: dict[str, Any],
    optional_followup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    moderator = roundtable_record.get("moderator_summary", {})
    evidence = roundtable_record.get("evidence_buckets", {})
    recommendations = [str(item) for item in evidence.get("recommendations", []) if str(item).strip()]
    risks = [str(item) for item in evidence.get("uncertainties", []) if str(item).strip()]
    reasons = [str(item) for item in moderator.get("consensus_points", []) if str(item).strip()]
    if review_result.get("rationale"):
        reasons.append(str(review_result["rationale"]))
    if optional_followup and optional_followup.get("accepted_revision"):
        reasons.append(str(optional_followup["accepted_revision"]))
    return {
        "recommendation": str(moderator.get("preliminary_recommendation") or first_or_default(recommendations, "Run a bounded validation.")),
        "reasons": reasons or ["Reviewer allowed final decision."],
        "risks": risks,
        "next_action": first_or_default(recommendations, "Run the next bounded validation step."),
        "stop_condition": first_or_default(risks, "Stop if the core validation signal is not observed."),
        "review_point": "Review after the next bounded validation run or if a severe red flag appears.",
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
        "required_followups": normalize_required_followups(review_result.get("required_followups", [])),
        "rationale": review_result["rationale"],
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


def collect_open_questions(
    evidence_buckets: dict[str, Any],
    review_result: dict[str, Any],
    optional_followup: dict[str, Any] | None,
) -> list[str]:
    items = [str(item) for item in evidence_buckets.get("uncertainties", []) if str(item).strip()]
    items.extend(required_followup_text(item) for item in review_result.get("required_followups", []) if required_followup_text(item))
    if optional_followup:
        items.extend(required_followup_text(item) for item in optional_followup.get("required_followups", []) if required_followup_text(item))
    return list(dict.fromkeys(items))


def normalize_required_followups(items: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            agent_id = str(item.get("agent_id") or "reviewer")
            needs = str(item.get("needs") or item.get("need") or item.get("text") or "").strip()
        else:
            agent_id = "reviewer"
            needs = str(item).strip()
        if needs:
            normalized.append({"agent_id": agent_id, "needs": needs})
    return normalized


def required_followup_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("needs") or item.get("need") or item.get("text") or "").strip()
    return str(item).strip()


def fixture_claim_boundary(handoff_packet: dict[str, Any] | None, review_packet: dict[str, Any]) -> dict[str, Any]:
    notes = [
        "debate result was built from fixture-backed local runtime artifacts.",
        "This is not host-live or provider-live evidence.",
    ]
    if handoff_packet:
        notes.append("handoff packet was normalized through the portable handoff projection.")
    if review_packet:
        notes.append("review packet was consumed by the checked-in result builder.")
    return {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": notes,
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
