from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from roundtable_core.agents.registry import load_agent_registry


PORTABLE_HANDOFF_VERSION = "0.1.0"
LEGACY_HANDOFF_VERSION = "v0.1"
DEFAULT_TASK_TYPE = "product"
DEFAULT_SECONDARY_TASK_TYPE = "startup"


def runtime_packet_to_portable_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    packet = unwrap_runtime_packet(payload)
    registry = load_agent_registry()
    known_evidence = [
        {
            "kind": "fact",
            "text": str(item.get("claim_text", "")).strip(),
            "source": str(item.get("source_hint") or ",".join(item.get("cited_by", [])) or "runtime_packet"),
        }
        for item in packet.get("field_09_factual_claims", [])
        if isinstance(item, dict) and str(item.get("claim_text", "")).strip()
    ]
    known_evidence.extend(
        {
            "kind": "recommendation",
            "text": str(item.get("solution_text", "")).strip(),
            "source": "runtime_packet.field_08_candidate_solutions",
        }
        for item in packet.get("field_08_candidate_solutions", [])
        if isinstance(item, dict) and str(item.get("solution_text", "")).strip()
    )

    risk_flags = [
        {"risk": str(text).strip(), "why_it_matters": "Carried from room tension points."}
        for text in packet.get("field_06_tension_points", [])
        if isinstance(text, str) and text.strip()
    ]
    risk_flags.extend(
        {"risk": str(text).strip(), "why_it_matters": "Carried from room uncertainty points."}
        for text in packet.get("field_10_uncertainty_points", [])
        if isinstance(text, str) and text.strip()
    )

    roles = packet.get("field_12_suggested_agent_roles", {})
    if not isinstance(roles, dict):
        roles = {}

    recommended_panel: list[dict[str, Any]] = []
    for agent_id in packet.get("field_11_suggested_agents", []):
        if not isinstance(agent_id, str):
            continue
        meta = registry.get(agent_id, {})
        recommended_panel.append(
            {
                "agent_id": agent_id,
                "display_name": str(meta.get("display_name") or meta.get("short_name") or agent_id),
                "cognitive_lens": list(meta.get("cognitive_lens") or [str(meta.get("short_name") or agent_id)]),
                "responsibility": str(roles.get(agent_id) or meta.get("style_rule") or "Review the decision from this lens."),
            }
        )

    return {
        "schema_version": PORTABLE_HANDOFF_VERSION,
        "source_room_session_id": packet["source_room_id"],
        "decision_question": build_decision_question(packet),
        "context_summary": build_context_summary(packet),
        "key_assumptions": list(packet.get("field_05_consensus_points", [])),
        "known_evidence": known_evidence,
        "open_questions": list(packet.get("field_07_open_questions", [])),
        "risk_flags": risk_flags,
        "recommended_panel": recommended_panel,
        "handoff_created_at": iso_now(),
        "claim_boundary": claim_boundary(),
    }


def portable_handoff_to_runtime_packet(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != PORTABLE_HANDOFF_VERSION:
        raise ValueError("Portable handoff schema_version must be 0.1.0.")
    recommended_panel = payload.get("recommended_panel")
    if not isinstance(recommended_panel, list) or len(recommended_panel) < 3:
        raise ValueError("Portable handoff recommended_panel must contain at least 3 members.")

    suggested_agents = [
        item["agent_id"]
        for item in recommended_panel
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str) and item["agent_id"].strip()
    ]
    roles = {
        item["agent_id"]: str(item.get("responsibility") or "Review the decision from this lens.")
        for item in recommended_panel
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    open_questions = [str(item) for item in payload.get("open_questions", []) if str(item).strip()]
    key_assumptions = [str(item) for item in payload.get("key_assumptions", []) if str(item).strip()]
    risk_flags = [
        str(item.get("risk") or item.get("why_it_matters") or "").strip()
        for item in payload.get("risk_flags", [])
        if isinstance(item, dict) and str(item.get("risk") or item.get("why_it_matters") or "").strip()
    ]

    known_evidence = [
        item
        for item in payload.get("known_evidence", [])
        if isinstance(item, dict) and str(item.get("text", "")).strip()
    ]
    candidate_solution = first_text(
        [
            item.get("text")
            for item in known_evidence
            if item.get("kind") in {"recommendation", "inference"}
        ]
        + [payload.get("decision_question")]
    )

    return {
        "schema_version": LEGACY_HANDOFF_VERSION,
        "generated_at_turn": 1,
        "source_room_id": payload["source_room_session_id"],
        "field_01_original_topic": payload["decision_question"],
        "field_02_room_title": short_title(payload["decision_question"]),
        "field_03_type": {
            "primary": DEFAULT_TASK_TYPE,
            "secondary": DEFAULT_SECONDARY_TASK_TYPE,
        },
        "field_04_sub_problems": [
            {
                "text": question,
                "tags": ["decision_question"],
                "discussed_in_turns": [1],
                "status": "open",
            }
            for question in (open_questions or [payload["decision_question"]])
        ],
        "field_05_consensus_points": key_assumptions or [payload["context_summary"]],
        "field_06_tension_points": risk_flags,
        "field_07_open_questions": open_questions,
        "field_08_candidate_solutions": [
            {
                "solution_text": candidate_solution,
                "proposed_by": suggested_agents[:2],
                "support_level": "medium",
                "unresolved_concerns": open_questions[:2],
            }
        ],
        "field_09_factual_claims": [
            {
                "claim_text": item["text"],
                "cited_by": suggested_agents[:1],
                "source_hint": item.get("source", "portable_handoff"),
                "reliability": "asserted",
            }
            for item in known_evidence
            if item.get("kind") == "fact"
        ],
        "field_10_uncertainty_points": risk_flags + open_questions,
        "field_11_suggested_agents": suggested_agents[:5],
        "field_12_suggested_agent_roles": roles,
        "field_13_upgrade_reason": {
            "reason_code": "user_explicit_request",
            "reason_text": "Portable handoff was converted for legacy debate runtime compatibility.",
            "triggered_by": "user_explicit",
            "confidence": 0.75,
            "warning_flags": ["portable_handoff_converted_to_legacy_runtime_packet"],
        },
    }


def unwrap_runtime_packet(payload: dict[str, Any]) -> dict[str, Any]:
    packet = payload.get("handoff_packet") if "handoff_packet" in payload else payload
    if not isinstance(packet, dict):
        raise ValueError("Runtime handoff packet must be an object.")
    if packet.get("schema_version") != LEGACY_HANDOFF_VERSION:
        raise ValueError("Runtime handoff packet schema_version must be v0.1.")
    return packet


def build_decision_question(packet: dict[str, Any]) -> str:
    candidates = packet.get("field_08_candidate_solutions", [])
    if isinstance(candidates, list) and candidates:
        first = candidates[0]
        if isinstance(first, dict) and isinstance(first.get("solution_text"), str):
            return f"是否应该推进：{first['solution_text']}"
    return str(packet["field_01_original_topic"])


def build_context_summary(packet: dict[str, Any]) -> str:
    sections = []
    for label, field in [
        ("Consensus", "field_05_consensus_points"),
        ("Tensions", "field_06_tension_points"),
        ("Open questions", "field_07_open_questions"),
    ]:
        values = [str(item) for item in packet.get(field, []) if str(item).strip()]
        if values:
            sections.append(f"{label}: " + " / ".join(values))
    return "\n".join(sections) if sections else str(packet["field_01_original_topic"])


def claim_boundary() -> dict[str, Any]:
    return {
        "local_first": True,
        "host_live": "not_claimed",
        "provider_live": "not_claimed",
        "notes": [
            "Portable handoff is generated from fixture-backed or local runtime artifacts.",
            "It is not host-live or provider-live evidence.",
        ],
    }


def first_text(values: list[Any]) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Run a bounded debate before making a final decision."


def short_title(text: str) -> str:
    compact = " ".join(str(text).split())
    return compact[:48] or "Room handoff"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
