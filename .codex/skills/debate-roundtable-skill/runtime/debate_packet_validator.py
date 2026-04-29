#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.agents.registry import load_agent_registry
from roundtable_core.protocol.handoff import runtime_packet_to_portable_handoff, portable_handoff_to_runtime_packet

REGISTRY_PATH = REPO_ROOT / "agents" / "registry.json"

VALID_TASK_TYPES = {"startup", "product", "learning", "content", "risk", "planning", "strategy", "writing"}
VALID_REASON_CODES = {
    "reached_decision_stage_with_tension",
    "forced_rebalance_repeated",
    "token_budget_repeatedly_exceeded",
    "user_explicit_request",
}
VALID_TRIGGERED_BY = {"auto_rule", "user_explicit"}
VALID_SUB_PROBLEM_STATUS = {"open", "converged", "abandoned"}
VALID_RELIABILITY = {"sourced", "asserted", "contested"}

DEFAULT_AGENT_COMBINATIONS = {
    "startup": ["paul-graham", "steve-jobs", "munger", "taleb"],
    "product": ["steve-jobs", "zhang-yiming", "elon-musk", "munger"],
    "learning": ["karpathy", "feynman", "ilya-sutskever"],
    "content": ["mrbeast", "feynman", "zhangxuefeng", "naval"],
    "risk": ["taleb", "munger", "elon-musk"],
    "planning": ["naval", "munger", "taleb"],
    "strategy": ["paul-graham", "munger", "taleb", "zhang-yiming"],
    "writing": ["feynman", "naval", "zhangxuefeng", "paul-graham"],
}


class DebatePacketValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        payload = load_json(Path(args.packet_json))
        result = validate_handoff_packet(payload)
    except (DebatePacketValidationError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"accepted": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executable /debate preflight validator for /room handoff packets."
    )
    parser.add_argument("--packet-json", required=True, help="Path to a handoff packet JSON file.")
    return parser


def validate_handoff_packet(payload: dict[str, Any]) -> dict[str, Any]:
    packet = payload.get("handoff_packet") if isinstance(payload, dict) and "handoff_packet" in payload else payload
    if not isinstance(packet, dict):
        raise DebatePacketValidationError("Packet payload must be an object or {handoff_packet: {...}} wrapper.")
    if packet.get("schema_version") == "0.1.0":
        packet = portable_handoff_to_runtime_packet(packet)

    registry = load_registry()

    require(packet.get("schema_version") == "v0.1", "schema_version must be v0.1.")
    require(
        isinstance(packet.get("generated_at_turn"), int) and packet["generated_at_turn"] >= 1,
        "generated_at_turn must be a positive integer.",
    )
    require(
        isinstance(packet.get("source_room_id"), str) and bool(packet["source_room_id"].strip()),
        "source_room_id must be a non-empty string.",
    )
    require(
        isinstance(packet.get("field_01_original_topic"), str) and bool(packet["field_01_original_topic"].strip()),
        "field_01_original_topic must be a non-empty string.",
    )
    require(
        isinstance(packet.get("field_02_room_title"), str) and bool(packet["field_02_room_title"].strip()),
        "field_02_room_title must be a non-empty string.",
    )

    field_03 = packet.get("field_03_type")
    require(isinstance(field_03, dict), "field_03_type must be an object.")
    primary_type = field_03.get("primary")
    secondary_type = field_03.get("secondary")
    require(primary_type in VALID_TASK_TYPES, "field_03_type.primary is invalid.")
    require(secondary_type is None or secondary_type in VALID_TASK_TYPES, "field_03_type.secondary is invalid.")

    validate_sub_problems(packet.get("field_04_sub_problems"))
    validate_string_list(packet.get("field_05_consensus_points"), "field_05_consensus_points")
    validate_string_list(packet.get("field_06_tension_points"), "field_06_tension_points")
    validate_string_list(packet.get("field_07_open_questions"), "field_07_open_questions")
    require(
        len(packet["field_05_consensus_points"]) + len(packet["field_06_tension_points"]) + len(packet["field_07_open_questions"]) > 0,
        "At least one of consensus_points, tension_points, or open_questions must be non-empty.",
    )
    validate_candidate_solutions(packet.get("field_08_candidate_solutions"))
    validate_factual_claims(packet.get("field_09_factual_claims"))
    validate_string_list(packet.get("field_10_uncertainty_points"), "field_10_uncertainty_points")

    suggested_agents = validate_suggested_agents(packet.get("field_11_suggested_agents"), registry)
    role_warnings = validate_suggested_agent_roles(
        packet.get("field_12_suggested_agent_roles"),
        suggested_agents=suggested_agents,
    )
    upgrade_reason = validate_upgrade_reason(packet.get("field_13_upgrade_reason"))

    balance = summarize_balance(suggested_agents, registry)
    warnings = list(role_warnings)
    if balance["defensive_count"] < 1:
        warnings.append("candidate_pool_missing_defensive")
    if balance["grounded_count"] < 1:
        warnings.append("candidate_pool_missing_grounded")
    if balance["dominant_ratio"] > 0.5:
        warnings.append("candidate_pool_dominant_ratio_exceeds_half")

    return {
        "accepted": True,
        "checked_against": str(Path(__file__).resolve()),
        "reason": (
            "handoff packet passed executable /debate preflight and provides a usable "
            "candidate pool plus packet fields for debate-side reselection."
        ),
        "source_room_id": packet["source_room_id"],
        "primary_type": primary_type,
        "secondary_type": secondary_type,
        "starting_agents": suggested_agents,
        "default_agents_for_type": DEFAULT_AGENT_COMBINATIONS[primary_type],
        "packet_balance": balance,
        "debate_reselection_required": bool(warnings),
        "minimum_overlap_target": min(2, len(suggested_agents)),
        "warnings": warnings,
        "upgrade_reason": {
            "reason_code": upgrade_reason["reason_code"],
            "triggered_by": upgrade_reason["triggered_by"],
            "confidence": upgrade_reason["confidence"],
        },
        "portable_handoff": runtime_packet_to_portable_handoff(packet),
    }


def validate_sub_problems(value: Any) -> None:
    require(isinstance(value, list) and len(value) >= 1, "field_04_sub_problems must be a non-empty array.")
    for item in value:
        require(isinstance(item, dict), "Each field_04_sub_problems item must be an object.")
        require(isinstance(item.get("text"), str) and bool(item["text"].strip()), "SubProblem.text must be non-empty.")
        tags = item.get("tags")
        require(isinstance(tags, list) and len(tags) >= 1, "SubProblem.tags must be a non-empty array.")
        require(all(isinstance(tag, str) and bool(tag.strip()) for tag in tags), "SubProblem.tags must be strings.")
        discussed_in_turns = item.get("discussed_in_turns")
        require(
            isinstance(discussed_in_turns, list) and all(isinstance(turn, int) and turn >= 1 for turn in discussed_in_turns),
            "SubProblem.discussed_in_turns must be an integer array.",
        )
        require(item.get("status") in VALID_SUB_PROBLEM_STATUS, "SubProblem.status is invalid.")


def validate_string_list(value: Any, field_name: str) -> None:
    require(isinstance(value, list), f"{field_name} must be an array.")
    require(all(isinstance(item, str) for item in value), f"{field_name} must contain strings only.")


def validate_candidate_solutions(value: Any) -> None:
    require(isinstance(value, list) and len(value) >= 1, "field_08_candidate_solutions must contain at least one solution.")
    for item in value:
        require(isinstance(item, dict), "Each candidate solution must be an object.")
        require(
            isinstance(item.get("solution_text"), str) and bool(item["solution_text"].strip()),
            "CandidateSolution.solution_text must be non-empty.",
        )
        proposed_by = item.get("proposed_by")
        require(isinstance(proposed_by, list) and len(proposed_by) >= 1, "CandidateSolution.proposed_by must be a non-empty array.")
        require(all(isinstance(agent_id, str) and bool(agent_id.strip()) for agent_id in proposed_by), "CandidateSolution.proposed_by must contain strings.")
        require(item.get("support_level") in {"high", "medium", "low"}, "CandidateSolution.support_level is invalid.")
        unresolved = item.get("unresolved_concerns")
        require(isinstance(unresolved, list), "CandidateSolution.unresolved_concerns must be an array.")
        require(all(isinstance(entry, str) for entry in unresolved), "CandidateSolution.unresolved_concerns must contain strings.")


def validate_factual_claims(value: Any) -> None:
    require(isinstance(value, list), "field_09_factual_claims must be an array.")
    for item in value:
        require(isinstance(item, dict), "Each factual claim must be an object.")
        require(
            isinstance(item.get("claim_text"), str) and bool(item["claim_text"].strip()),
            "FactualClaim.claim_text must be non-empty.",
        )
        cited_by = item.get("cited_by")
        require(isinstance(cited_by, list) and len(cited_by) >= 1, "FactualClaim.cited_by must be a non-empty array.")
        require(all(isinstance(agent_id, str) and bool(agent_id.strip()) for agent_id in cited_by), "FactualClaim.cited_by must contain strings.")
        require(isinstance(item.get("source_hint"), str), "FactualClaim.source_hint must be a string.")
        require(item.get("reliability") in VALID_RELIABILITY, "FactualClaim.reliability is invalid.")


def validate_suggested_agents(value: Any, registry: dict[str, dict[str, Any]]) -> list[str]:
    require(isinstance(value, list) and 3 <= len(value) <= 5, "field_11_suggested_agents must contain 3-5 agents.")
    seen: set[str] = set()
    normalized: list[str] = []
    for agent_id in value:
        require(isinstance(agent_id, str) and bool(agent_id.strip()), "field_11_suggested_agents entries must be non-empty strings.")
        require(agent_id in registry, f"Suggested agent is not registered: {agent_id}")
        require(agent_id not in seen, f"Duplicate suggested agent: {agent_id}")
        seen.add(agent_id)
        normalized.append(agent_id)
    return normalized


def validate_suggested_agent_roles(value: Any, *, suggested_agents: list[str]) -> list[str]:
    require(isinstance(value, dict), "field_12_suggested_agent_roles must be an object.")
    warnings: list[str] = []
    for agent_id in suggested_agents:
        role_text = value.get(agent_id)
        require(isinstance(role_text, str) and bool(role_text.strip()), f"Missing suggested role text for {agent_id}.")
        role_length = len(role_text.strip())
        if role_length < 20 or role_length > 120:
            warnings.append(f"suggested_role_length_out_of_band:{agent_id}")
    return warnings


def validate_upgrade_reason(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "field_13_upgrade_reason must be an object.")
    require(value.get("reason_code") in VALID_REASON_CODES, "field_13_upgrade_reason.reason_code is invalid.")
    require(value.get("triggered_by") in VALID_TRIGGERED_BY, "field_13_upgrade_reason.triggered_by is invalid.")
    require(
        isinstance(value.get("reason_text"), str) and bool(value["reason_text"].strip()),
        "field_13_upgrade_reason.reason_text must be non-empty.",
    )
    confidence = value.get("confidence")
    require(isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0, "field_13_upgrade_reason.confidence must be 0-1.")
    warning_flags = value.get("warning_flags", [])
    require(isinstance(warning_flags, list), "field_13_upgrade_reason.warning_flags must be an array when present.")
    return value


def summarize_balance(agent_ids: list[str], registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    defensive_count = sum(1 for agent_id in agent_ids if registry[agent_id]["structural_role"] == "defensive")
    grounded_count = sum(1 for agent_id in agent_ids if registry[agent_id]["expression"] == "grounded")
    dominant_count = sum(1 for agent_id in agent_ids if registry[agent_id]["strength"] == "dominant")
    dominant_ratio = dominant_count / len(agent_ids)
    return {
        "defensive_count": defensive_count,
        "grounded_count": grounded_count,
        "dominant_count": dominant_count,
        "dominant_ratio": round(dominant_ratio, 4),
        "passes_debate_balance": defensive_count >= 1 and grounded_count >= 1 and dominant_ratio <= 0.5,
    }


def load_registry() -> dict[str, dict[str, Any]]:
    try:
        return load_agent_registry(REGISTRY_PATH)
    except Exception as exc:
        raise DebatePacketValidationError(f"Could not load machine-readable agent registry: {exc}") from exc


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DebatePacketValidationError(f"JSON file does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def clean_table_cell(text: str) -> str:
    return text.strip().strip("`")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DebatePacketValidationError(message)


if __name__ == "__main__":
    sys.exit(main())
