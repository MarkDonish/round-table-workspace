#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "rooms"
REGISTRY_PATH = REPO_ROOT / "docs" / "agent-registry.md"
DEBATE_SKILL_PATH = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "SKILL.md"
DEBATE_PACKET_VALIDATOR_PATH = (
    REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime" / "debate_packet_validator.py"
)

VALID_STAGES = {"explore", "simulate", "stress_test", "converge", "decision"}
VALID_TURN_ROLES = {"primary", "support", "challenge", "synthesizer"}
VALID_UPGRADE_REASONS = {
    "reached_decision_stage_with_tension",
    "forced_rebalance_repeated",
    "token_budget_repeatedly_exceeded",
    "user_explicit_request",
}
VALID_UPGRADE_HINTS = {"reached_decision_stage_with_tension", "forced_rebalance_repeated", None}


class RoomRuntimeError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        command = args.command
        if command == "start-room":
            result = command_start_room(args)
        elif command == "run-turn":
            result = command_run_turn(args)
        elif command == "run-summary":
            result = command_run_summary(args)
        elif command == "run-upgrade":
            result = command_run_upgrade(args)
        elif command == "patch-roster":
            result = command_patch_roster(args)
        elif command == "validate-canonical":
            result = command_validate_canonical(args)
        else:
            raise RoomRuntimeError(f"Unsupported command: {command}")
    except RoomRuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Portable /room runtime bridge that validates prompt JSON and writes room state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser(
        "start-room",
        help="Create a room from room_full output and optionally continue into the first turn.",
    )
    start_parser.add_argument("--topic", required=True, help="Original /room topic text.")
    start_parser.add_argument("--selection-json", required=True, help="room_full prompt JSON output.")
    start_parser.add_argument(
        "--room-id",
        help="Optional stable room id. Defaults to a generated id.",
    )
    start_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )
    start_parser.add_argument(
        "--initial-turn-selection-json",
        help="Optional room_turn selection output for the first immediate turn.",
    )
    start_parser.add_argument(
        "--initial-turn-chat-json",
        help="Optional room-chat output for the first immediate turn.",
    )
    start_parser.add_argument(
        "--initial-turn-user-input",
        help="Optional first-turn user input. Defaults to the normalized room topic.",
    )

    turn_parser = subparsers.add_parser(
        "run-turn",
        help="Apply a room_turn selection output plus a room-chat output to an existing room.",
    )
    turn_parser.add_argument("--room-id", required=True)
    turn_parser.add_argument("--user-input", required=True)
    turn_parser.add_argument("--selection-json", required=True)
    turn_parser.add_argument("--chat-json", required=True)
    turn_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )

    summary_parser = subparsers.add_parser(
        "run-summary",
        help="Apply a room-summary output and persist the summary fields.",
    )
    summary_parser.add_argument("--room-id", required=True)
    summary_parser.add_argument("--summary-json", required=True)
    summary_parser.add_argument("--trigger", default="/summary")
    summary_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )

    upgrade_parser = subparsers.add_parser(
        "run-upgrade",
        help="Apply a room-upgrade output, persist the handoff packet, and verify debate compatibility.",
    )
    upgrade_parser.add_argument("--room-id", required=True)
    upgrade_parser.add_argument("--upgrade-json", required=True)
    upgrade_parser.add_argument(
        "--explicit-user-request",
        action="store_true",
        help="Treat this upgrade as an explicit user request when no prior upgrade_signal exists.",
    )
    upgrade_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )

    patch_parser = subparsers.add_parser(
        "patch-roster",
        help="Apply a roster_patch output for /add or /remove.",
    )
    patch_parser.add_argument("--room-id", required=True)
    patch_parser.add_argument("--action", required=True, choices=["add", "remove"])
    patch_parser.add_argument("--selection-json", required=True)
    patch_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )

    canonical_parser = subparsers.add_parser(
        "validate-canonical",
        help="Replay the checked-in canonical fixture chain and generate a room evidence bundle.",
    )
    canonical_parser.add_argument(
        "--fixtures-dir",
        default=str(Path(__file__).resolve().parent / "fixtures" / "canonical"),
        help="Directory containing canonical fixture JSON files.",
    )
    canonical_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )
    canonical_parser.add_argument(
        "--room-id",
        help="Optional stable room id. Defaults to a generated canonical room id.",
    )

    return parser


def command_start_room(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    registry = load_registry()
    room_full = load_json(Path(args.selection_json))
    topic = normalize_room_topic(args.topic)
    room_id = args.room_id or generate_room_id()

    validate_room_full_output(room_full, registry)

    state = build_initial_state(topic=topic, room_id=room_id, room_full=room_full, registry=registry)
    room_dir = get_room_dir(state_root, room_id)
    ensure_directory(room_dir)

    write_json(room_dir / "room_full.selection.json", room_full)
    save_state(state_root, state)

    first_turn_result: dict[str, Any] | None = None
    if args.initial_turn_selection_json or args.initial_turn_chat_json:
        if not args.initial_turn_selection_json or not args.initial_turn_chat_json:
            raise RoomRuntimeError(
                "Both --initial-turn-selection-json and --initial-turn-chat-json are required together."
            )
        first_turn_input = args.initial_turn_user_input or topic
        initial_selection = load_json(Path(args.initial_turn_selection_json))
        initial_chat = load_json(Path(args.initial_turn_chat_json))
        state, first_turn_result = apply_turn(
            state=state,
            raw_user_input=first_turn_input,
            selection_output=initial_selection,
            chat_output=initial_chat,
            state_root=state_root,
        )

    return {
        "ok": True,
        "action": "start-room",
        "room_id": room_id,
        "state_path": str(get_room_dir(state_root, room_id) / "state.json"),
        "turn_count": state["turn_count"],
        "agents": state["agents"],
        "last_stage": state["last_stage"],
        "initial_turn_applied": first_turn_result is not None,
        "initial_turn_result": first_turn_result,
    }


def command_run_turn(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state = load_state(state_root, args.room_id)
    selection_output = load_json(Path(args.selection_json))
    chat_output = load_json(Path(args.chat_json))
    updated_state, result = apply_turn(
        state=state,
        raw_user_input=args.user_input,
        selection_output=selection_output,
        chat_output=chat_output,
        state_root=state_root,
    )
    return {
        "ok": True,
        "action": "run-turn",
        "room_id": updated_state["room_id"],
        **result,
    }


def command_run_summary(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state = load_state(state_root, args.room_id)
    summary_output = load_json(Path(args.summary_json))
    updated_state, result = apply_summary(
        state=state,
        summary_output=summary_output,
        trigger=args.trigger,
        state_root=state_root,
    )
    return {
        "ok": True,
        "action": "run-summary",
        "room_id": updated_state["room_id"],
        **result,
    }


def command_run_upgrade(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state = load_state(state_root, args.room_id)
    upgrade_output = load_json(Path(args.upgrade_json))
    updated_state, result = apply_upgrade(
        state=state,
        upgrade_output=upgrade_output,
        explicit_user_request=args.explicit_user_request,
        state_root=state_root,
    )
    return {
        "ok": True,
        "action": "run-upgrade",
        "room_id": updated_state["room_id"],
        **result,
    }


def command_patch_roster(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state = load_state(state_root, args.room_id)
    selection_output = load_json(Path(args.selection_json))
    updated_state, result = apply_roster_patch(
        state=state,
        action=args.action,
        selection_output=selection_output,
        state_root=state_root,
    )
    return {
        "ok": True,
        "action": "patch-roster",
        "room_id": updated_state["room_id"],
        **result,
    }


def command_validate_canonical(args: argparse.Namespace) -> dict[str, Any]:
    fixtures_dir = Path(args.fixtures_dir).expanduser().resolve()
    state_root = Path(args.state_root).expanduser().resolve()
    registry = load_registry()

    room_id = args.room_id or f"room-canonical-{uuid.uuid4().hex[:8]}"
    topic = (
        "我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，"
        "先把方向、切口、风险一步一步推出来。"
    )

    room_full = materialize_placeholders(load_json(fixtures_dir / "room_full.selection.json"), {"__ROOM_ID__": room_id})
    initial_selection = materialize_placeholders(
        load_json(fixtures_dir / "initial_turn.selection.json"), {"__ROOM_ID__": room_id}
    )
    initial_chat = materialize_placeholders(load_json(fixtures_dir / "initial_turn.chat.json"), {"__ROOM_ID__": room_id})
    focus_selection = materialize_placeholders(
        load_json(fixtures_dir / "focus_turn.selection.json"), {"__ROOM_ID__": room_id}
    )
    focus_chat = materialize_placeholders(load_json(fixtures_dir / "focus_turn.chat.json"), {"__ROOM_ID__": room_id})
    summary_output = materialize_placeholders(load_json(fixtures_dir / "summary.json"), {"__ROOM_ID__": room_id})
    upgrade_output = materialize_placeholders(load_json(fixtures_dir / "upgrade.json"), {"__ROOM_ID__": room_id})

    validate_room_full_output(room_full, registry)
    state = build_initial_state(topic=topic, room_id=room_id, room_full=room_full, registry=registry)
    room_dir = get_room_dir(state_root, room_id)
    ensure_directory(room_dir)
    write_json(room_dir / "room_full.selection.json", room_full)
    save_state(state_root, state)

    state, first_turn_result = apply_turn(
        state=state,
        raw_user_input=topic,
        selection_output=initial_selection,
        chat_output=initial_chat,
        state_root=state_root,
    )
    state, second_turn_result = apply_turn(
        state=state,
        raw_user_input="/focus 先只盯最小可验证切口",
        selection_output=focus_selection,
        chat_output=focus_chat,
        state_root=state_root,
    )
    state, summary_result = apply_summary(
        state=state,
        summary_output=summary_output,
        trigger="/summary",
        state_root=state_root,
    )
    state, upgrade_result = apply_upgrade(
        state=state,
        upgrade_output=upgrade_output,
        explicit_user_request=True,
        state_root=state_root,
    )

    report = {
        "ok": True,
        "action": "validate-canonical",
        "room_id": room_id,
        "state_path": str(room_dir / "state.json"),
        "conversation_turns": state["turn_count"],
        "summary_turn": state["last_summary_turn"],
        "upgrade_signal": state["upgrade_signal"],
        "artifacts": {
            "room_dir": str(room_dir),
            "room_full_selection": str(room_dir / "room_full.selection.json"),
            "turn_001": str(room_dir / "turns" / "turn-001.turn.json"),
            "turn_002": str(room_dir / "turns" / "turn-002.turn.json"),
            "summary": str(room_dir / "summary" / "summary-turn-002.json"),
            "handoff_packet": str(room_dir / "handoff" / "packet-turn-002.json"),
            "debate_acceptance": str(room_dir / "handoff" / "debate-acceptance.json"),
        },
        "steps": {
            "start_room": first_turn_result,
            "follow_up_turn": second_turn_result,
            "summary": summary_result,
            "upgrade": upgrade_result,
        },
        "pass_criteria": {
            "stable_state_object": bool((room_dir / "state.json").exists()),
            "at_least_two_turns": state["turn_count"] >= 2,
            "summary_persisted": bool((room_dir / "summary" / "summary-turn-002.json").exists()),
            "handoff_packet_persisted": bool((room_dir / "handoff" / "packet-turn-002.json").exists()),
            "debate_preflight_accepts_packet": upgrade_result["debate_acceptance"]["accepted"],
        },
    }
    write_json(room_dir / "validation-report.json", report)
    return report


def apply_turn(
    *,
    state: dict[str, Any],
    raw_user_input: str,
    selection_output: dict[str, Any],
    chat_output: dict[str, Any],
    state_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_state = copy.deepcopy(state)
    registry = load_registry()
    validate_room_turn_output(selection_output, updated_state, registry)

    normalized_input, new_focus = normalize_turn_input(raw_user_input)
    if new_focus is not None:
        updated_state["active_focus"] = new_focus

    turn_id = updated_state["turn_count"] + 1
    stage = selection_output["parsed_topic"]["stage"]
    assigned_speakers = assign_turn_roles(selection_output, updated_state, registry)

    turn = validate_chat_output(
        chat_output=chat_output,
        assigned_speakers=assigned_speakers,
        turn_id=turn_id,
        stage=stage,
        active_focus=updated_state["active_focus"],
        user_input=normalized_input,
    )

    turn["forced_rebalance"] = selection_output.get("forced_rebalance")
    turn["selection_structural_check"] = selection_output.get("structural_check")
    turn["selection_explanation"] = selection_output.get("explanation")
    updated_state["conversation_log"].append(turn)
    updated_state["turn_count"] = turn_id
    updated_state["last_stage"] = stage
    updated_state["silent_rounds"] = compute_silent_rounds(updated_state, turn)
    updated_state["recent_log"] = build_recent_log(updated_state["conversation_log"])
    updated_state["upgrade_signal"] = detect_upgrade_signal(updated_state)

    room_dir = get_room_dir(state_root, updated_state["room_id"])
    ensure_directory(room_dir / "turns")
    write_json(room_dir / "turns" / f"turn-{turn_id:03d}.selection.json", selection_output)
    write_json(room_dir / "turns" / f"turn-{turn_id:03d}.chat.json", chat_output)
    write_json(room_dir / "turns" / f"turn-{turn_id:03d}.turn.json", turn)
    save_state(state_root, updated_state)

    result = {
        "turn_id": turn_id,
        "turn_path": str(room_dir / "turns" / f"turn-{turn_id:03d}.turn.json"),
        "state_path": str(room_dir / "state.json"),
        "stage": updated_state["last_stage"],
        "active_focus": updated_state["active_focus"],
        "selected_speakers": [speaker["agent_id"] for speaker in turn["speakers"]],
        "upgrade_signal": updated_state["upgrade_signal"],
    }
    return updated_state, result


def apply_summary(
    *,
    state: dict[str, Any],
    summary_output: dict[str, Any],
    trigger: str,
    state_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_state = copy.deepcopy(state)
    validate_summary_output(summary_output, updated_state)

    summary_update = summary_output["summary_update"]
    updated_state["consensus_points"] = summary_update["consensus_points"]
    updated_state["open_questions"] = summary_update["open_questions"]
    updated_state["tension_points"] = summary_update["tension_points"]
    updated_state["recommended_next_step"] = summary_update["recommended_next_step"]
    updated_state["last_summary_turn"] = updated_state["turn_count"]

    upgrade_hint = summary_output.get("meta", {}).get("upgrade_hint")
    if upgrade_hint not in VALID_UPGRADE_HINTS:
        raise RoomRuntimeError(f"Unsupported summary upgrade_hint: {upgrade_hint}")
    if upgrade_hint and updated_state.get("upgrade_signal") is None:
        updated_state["upgrade_signal"] = {
            "triggered_at_turn": updated_state["turn_count"],
            "reason": upgrade_hint,
            "tension_unresolved": bool(updated_state["tension_points"]),
            "confidence": 0.7,
            "handoff_ready": False,
        }

    room_dir = get_room_dir(state_root, updated_state["room_id"])
    ensure_directory(room_dir / "summary")
    summary_path = room_dir / "summary" / f"summary-turn-{updated_state['turn_count']:03d}.json"
    write_json(summary_path, summary_output)
    save_state(state_root, updated_state)

    result = {
        "summary_path": str(summary_path),
        "state_path": str(room_dir / "state.json"),
        "last_summary_turn": updated_state["last_summary_turn"],
        "consensus_points": updated_state["consensus_points"],
        "open_questions": updated_state["open_questions"],
        "tension_points": updated_state["tension_points"],
        "recommended_next_step": updated_state["recommended_next_step"],
        "trigger": trigger,
    }
    return updated_state, result


def apply_upgrade(
    *,
    state: dict[str, Any],
    upgrade_output: dict[str, Any],
    explicit_user_request: bool,
    state_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_state = copy.deepcopy(state)
    if updated_state.get("upgrade_signal") is None:
        if not explicit_user_request:
            raise RoomRuntimeError("Upgrade requires an existing upgrade_signal or --explicit-user-request.")
        updated_state["upgrade_signal"] = {
            "triggered_at_turn": updated_state["turn_count"],
            "reason": "user_explicit_request",
            "tension_unresolved": bool(updated_state["tension_points"]),
            "confidence": 0.8,
            "handoff_ready": False,
        }

    validate_upgrade_output(upgrade_output, updated_state)
    packet = upgrade_output["handoff_packet"]
    acceptance = validate_debate_acceptance(packet)

    updated_state["mode"] = "upgrading"
    updated_state["upgrade_signal"]["handoff_ready"] = True

    room_dir = get_room_dir(state_root, updated_state["room_id"])
    ensure_directory(room_dir / "handoff")
    packet_path = room_dir / "handoff" / f"packet-turn-{updated_state['turn_count']:03d}.json"
    acceptance_path = room_dir / "handoff" / "debate-acceptance.json"
    write_json(packet_path, upgrade_output)
    write_json(acceptance_path, acceptance)
    save_state(state_root, updated_state)

    result = {
        "packet_path": str(packet_path),
        "state_path": str(room_dir / "state.json"),
        "debate_acceptance": acceptance,
        "mode": updated_state["mode"],
        "upgrade_signal": updated_state["upgrade_signal"],
    }
    return updated_state, result


def apply_roster_patch(
    *,
    state: dict[str, Any],
    action: str,
    selection_output: dict[str, Any],
    state_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_state = copy.deepcopy(state)
    registry = load_registry()
    validate_roster_patch_output(selection_output, updated_state, action, registry)

    new_roster = selection_output["roster"]
    new_agents = [item["agent"] for item in new_roster]
    old_agents = set(updated_state["agents"])
    new_agent_set = set(new_agents)

    updated_state["agents"] = new_agents
    new_agent_roles: dict[str, Any] = {}
    for item in new_roster:
        agent_id = item["agent"]
        registry_entry = registry[agent_id]
        previous = updated_state["agent_roles"].get(agent_id, {})
        new_agent_roles[agent_id] = {
            "short_name": item.get("short_name") or previous.get("short_name") or registry_entry["short_name"],
            "role_summary": item.get("role", previous.get("role_summary", "")),
            "structural_role": item.get("structural_role")
            or previous.get("structural_role")
            or registry_entry["structural_role"],
            "expression": registry_entry["expression"],
            "strength": registry_entry["strength"],
            "task_types": registry_entry["task_types"],
            "stage_fit": registry_entry["stage_fit"],
            "sub_problem_tags": registry_entry["sub_problem_tags"],
        }
    updated_state["agent_roles"] = new_agent_roles

    new_silent_rounds: dict[str, int] = {}
    for agent_id in new_agents:
        if agent_id in old_agents:
            new_silent_rounds[agent_id] = updated_state["silent_rounds"].get(agent_id, 0)
        else:
            new_silent_rounds[agent_id] = 0
    updated_state["silent_rounds"] = new_silent_rounds

    room_dir = get_room_dir(state_root, updated_state["room_id"])
    ensure_directory(room_dir / "patches")
    patch_index = len(list((room_dir / "patches").glob("patch-*.json"))) + 1
    patch_path = room_dir / "patches" / f"patch-{patch_index:03d}.json"
    write_json(patch_path, selection_output)
    save_state(state_root, updated_state)

    result = {
        "patch_path": str(patch_path),
        "state_path": str(room_dir / "state.json"),
        "patch_action": action,
        "agents": updated_state["agents"],
        "added": sorted(new_agent_set - old_agents),
        "removed": sorted(old_agents - new_agent_set),
        "patch_applied": selection_output["patch_applied"],
    }
    return updated_state, result


def build_initial_state(
    *,
    topic: str,
    room_id: str,
    room_full: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    parsed = room_full["parsed_topic"]
    roster = room_full["roster"]
    agent_roles: dict[str, Any] = {}
    for item in roster:
        agent_id = item["agent"]
        registry_entry = registry[agent_id]
        agent_roles[agent_id] = {
            "short_name": item.get("short_name") or registry_entry["short_name"],
            "role_summary": item.get("role", ""),
            "structural_role": item.get("structural_role") or registry_entry["structural_role"],
            "expression": registry_entry["expression"],
            "strength": registry_entry["strength"],
            "task_types": registry_entry["task_types"],
            "stage_fit": registry_entry["stage_fit"],
            "sub_problem_tags": registry_entry["sub_problem_tags"],
        }

    return {
        "room_id": room_id,
        "title": derive_room_title(topic),
        "mode": "standard",
        "original_topic": topic,
        "primary_type": parsed["main_type"],
        "secondary_type": parsed["secondary_type"],
        "active_focus": None,
        "agents": [item["agent"] for item in roster],
        "agent_roles": agent_roles,
        "consensus_points": [],
        "open_questions": [],
        "tension_points": [],
        "recommended_next_step": None,
        "silent_rounds": {item["agent"]: 0 for item in roster},
        "turn_count": 0,
        "last_stage": parsed["stage"],
        "recent_log": "",
        "conversation_log": [],
        "upgrade_signal": None,
        "last_summary_turn": None,
    }


def validate_room_full_output(room_full: dict[str, Any], registry: dict[str, dict[str, Any]]) -> None:
    if "error" in room_full:
        raise RoomRuntimeError(f"room_full returned error: {room_full['error']}")
    require(room_full.get("mode") == "room_full", "room_full output must set mode=room_full.")
    parsed = room_full.get("parsed_topic")
    require(isinstance(parsed, dict), "room_full output must include parsed_topic.")
    stage = parsed.get("stage")
    require(stage in VALID_STAGES, f"Unsupported room_full stage: {stage}")
    roster = room_full.get("roster")
    require(isinstance(roster, list) and 1 <= len(roster) <= 8, "room_full roster must contain 1-8 agents.")
    seen: set[str] = set()
    for item in roster:
        agent_id = item.get("agent")
        require(agent_id in registry, f"Unknown roster agent: {agent_id}")
        require(agent_id not in seen, f"Duplicate roster agent: {agent_id}")
        seen.add(agent_id)
    require(room_full.get("speakers") is None, "room_full output must set speakers to null.")
    structural_check = room_full.get("structural_check")
    require(isinstance(structural_check, dict), "room_full output must include structural_check.")
    require(bool(structural_check.get("passed")), "room_full structural_check must pass.")
    explanation = room_full.get("explanation", {})
    require(non_empty_list(explanation.get("why_selected")), "room_full why_selected must not be empty.")
    require(non_empty_list(explanation.get("why_not_selected")), "room_full why_not_selected must not be empty.")


def validate_room_turn_output(
    selection_output: dict[str, Any],
    state: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> None:
    if "error" in selection_output:
        raise RoomRuntimeError(f"room_turn returned error: {selection_output['error']}")
    require(selection_output.get("mode") == "room_turn", "room_turn output must set mode=room_turn.")
    parsed = selection_output.get("parsed_topic")
    require(isinstance(parsed, dict), "room_turn output must include parsed_topic.")
    require(parsed.get("stage") in VALID_STAGES, f"Unsupported room_turn stage: {parsed.get('stage')}")
    speakers = selection_output.get("speakers")
    require(isinstance(speakers, list), "room_turn output must include speakers array.")
    max_speakers = 1 if len(state["agents"]) == 1 else 4
    min_speakers = 1 if len(state["agents"]) == 1 else 2
    require(min_speakers <= len(speakers) <= max_speakers, "room_turn speakers must stay within legal range.")
    seen: set[str] = set()
    for item in speakers:
        agent_id = item.get("agent") or item.get("agent_id")
        require(agent_id in state["agents"], f"room_turn speaker is not in current roster: {agent_id}")
        require(agent_id in registry, f"Unknown room_turn speaker: {agent_id}")
        require(agent_id not in seen, f"Duplicate room_turn speaker: {agent_id}")
        seen.add(agent_id)
        require("role" not in item and "turn_role" not in item, "room_turn output must not assign turn_role.")
    explanation = selection_output.get("explanation", {})
    require(non_empty_list(explanation.get("why_selected")), "room_turn why_selected must not be empty.")
    require(non_empty_list(explanation.get("why_not_selected")), "room_turn why_not_selected must not be empty.")


def validate_roster_patch_output(
    selection_output: dict[str, Any],
    state: dict[str, Any],
    action: str,
    registry: dict[str, dict[str, Any]],
) -> None:
    if "error" in selection_output:
        raise RoomRuntimeError(f"roster_patch returned error: {selection_output['error']}")
    require(selection_output.get("mode") == "roster_patch", "roster_patch output must set mode=roster_patch.")
    roster = selection_output.get("roster")
    require(isinstance(roster, list) and 1 <= len(roster) <= 8, "roster_patch roster must contain 1-8 agents.")
    seen: set[str] = set()
    for item in roster:
        agent_id = item.get("agent")
        require(agent_id in registry, f"Unknown roster_patch agent: {agent_id}")
        require(agent_id not in seen, f"Duplicate roster_patch agent: {agent_id}")
        seen.add(agent_id)

    patch_applied = selection_output.get("patch_applied")
    require(isinstance(patch_applied, dict), "roster_patch output must include patch_applied.")
    require(patch_applied.get("action") == action, "roster_patch action must match the bridge command.")
    explanation = selection_output.get("explanation", {})
    require(non_empty_list(explanation.get("why_selected")), "roster_patch why_selected must not be empty.")
    require(non_empty_list(explanation.get("why_not_selected")), "roster_patch why_not_selected must not be empty.")

    if action == "add":
        require(len(set(state["agents"]) & seen) >= 1, "roster_patch add must preserve the existing room core.")
        require(len(seen - set(state["agents"])) >= 1, "roster_patch add must introduce at least one new agent.")
    if action == "remove":
        require(len(set(state["agents"]) - seen) >= 1, "roster_patch remove must remove at least one existing agent.")


def assign_turn_roles(
    selection_output: dict[str, Any],
    state: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    roster_roles = state["agent_roles"]
    score_lookup = {
        entry["agent"]: entry.get("total", 0)
        for entry in selection_output.get("scorecards", [])
        if isinstance(entry, dict) and entry.get("agent")
    }
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(selection_output["speakers"]):
        agent_id = item.get("agent") or item.get("agent_id")
        role_info = roster_roles[agent_id]
        normalized.append(
            {
                "agent_id": agent_id,
                "short_name": item.get("short_name") or role_info["short_name"],
                "structural_role": item.get("structural_role") or role_info["structural_role"],
                "total": item.get("total", score_lookup.get(agent_id, len(selection_output["speakers"]) - index)),
                "turn_role": None,
            }
        )

    if len(normalized) == 1:
        normalized[0]["turn_role"] = "primary"
        return normalized

    normalized[0]["turn_role"] = "primary"
    challenger_index = first_opposite_structural_role(normalized, 0)

    if len(normalized) == 2:
        normalized[1]["turn_role"] = "challenge" if challenger_index == 1 else "support"
    elif len(normalized) == 3:
        if challenger_index is not None:
            normalized[challenger_index]["turn_role"] = "challenge"
            remaining = [idx for idx in range(1, 3) if idx != challenger_index]
            normalized[remaining[0]]["turn_role"] = "synthesizer"
        else:
            normalized[1]["turn_role"] = "support"
            normalized[2]["turn_role"] = "synthesizer"
    else:
        if challenger_index is None:
            challenger_index = min(range(1, 4), key=lambda idx: normalized[idx]["total"])
        normalized[challenger_index]["turn_role"] = "challenge"
        remaining = [idx for idx in range(1, 4) if idx != challenger_index]
        remaining.sort(key=lambda idx: normalized[idx]["total"], reverse=True)
        normalized[remaining[0]]["turn_role"] = "support"
        normalized[remaining[1]]["turn_role"] = "synthesizer"

    for speaker in normalized:
        require(
            speaker["turn_role"] in VALID_TURN_ROLES,
            f"Failed to assign a valid turn_role for {speaker['agent_id']}.",
        )
    return normalized


def validate_chat_output(
    *,
    chat_output: dict[str, Any],
    assigned_speakers: list[dict[str, Any]],
    turn_id: int,
    stage: str,
    active_focus: str | None,
    user_input: str,
) -> dict[str, Any]:
    if "error" in chat_output:
        raise RoomRuntimeError(f"room-chat returned error: {chat_output['error']}")

    require(chat_output.get("turn_id") == turn_id, f"room-chat turn_id must equal {turn_id}.")
    require(chat_output.get("stage") == stage, f"room-chat stage must equal {stage}.")
    require(chat_output.get("active_focus") == active_focus, "room-chat active_focus must match bridge state.")
    require(chat_output.get("user_input") == user_input, "room-chat user_input must match the bridged input.")

    speakers = chat_output.get("speakers")
    require(isinstance(speakers, list), "room-chat output must include speakers array.")
    require(len(speakers) == len(assigned_speakers), "room-chat must keep the bridged speaker count.")

    normalized_speakers: list[dict[str, Any]] = []
    for expected, actual in zip(assigned_speakers, speakers):
        require(actual.get("agent_id") == expected["agent_id"], "room-chat changed speaker order or identity.")
        require(actual.get("short_name") == expected["short_name"], "room-chat changed speaker short_name.")
        require(actual.get("role") == expected["turn_role"], "room-chat must keep the assigned turn_role.")
        content = normalize_whitespace(actual.get("content", ""))
        require(bool(content), f"room-chat content is empty for {expected['agent_id']}.")
        content = truncate_content(content, limit=220)
        normalized_speakers.append(
            {
                "agent_id": actual["agent_id"],
                "short_name": actual["short_name"],
                "role": actual["role"],
                "content": content,
            }
        )

    cited_agents = chat_output.get("cited_agents", [])
    warnings = chat_output.get("warnings", [])
    meta = chat_output.get("meta", {})
    require(isinstance(cited_agents, list), "room-chat cited_agents must be an array.")
    require(isinstance(warnings, list), "room-chat warnings must be an array.")
    require(isinstance(meta, dict), "room-chat meta must be an object.")
    require(meta.get("generated_at_turn") == turn_id, "room-chat meta.generated_at_turn must equal turn_id.")

    return {
        "turn_id": turn_id,
        "stage": stage,
        "active_focus": active_focus,
        "user_input": user_input,
        "speakers": normalized_speakers,
        "cited_agents": cited_agents,
        "warnings": warnings,
        "meta": {
            "generated_at_turn": turn_id,
            "prompt_version": meta.get("prompt_version"),
            "tokens_used_estimate": meta.get("tokens_used_estimate", 0),
        },
    }


def validate_summary_output(summary_output: dict[str, Any], state: dict[str, Any]) -> None:
    if "error" in summary_output:
        raise RoomRuntimeError(f"room-summary returned error: {summary_output['error']}")
    require(summary_output.get("mode") == "room_summary", "room-summary output must set mode=room_summary.")
    require(
        summary_output.get("current_turn") == state["turn_count"],
        "room-summary current_turn must match the room turn_count.",
    )
    require(summary_output.get("stage") == state["last_stage"], "room-summary stage must match the current stage.")
    summary_update = summary_output.get("summary_update")
    require(isinstance(summary_update, dict), "room-summary output must include summary_update.")
    require(isinstance(summary_update.get("consensus_points"), list), "consensus_points must be an array.")
    require(isinstance(summary_update.get("open_questions"), list), "open_questions must be an array.")
    require(isinstance(summary_update.get("tension_points"), list), "tension_points must be an array.")
    require(
        isinstance(summary_update.get("recommended_next_step"), str)
        and bool(summary_update["recommended_next_step"].strip()),
        "recommended_next_step must be a non-empty string.",
    )
    meta = summary_output.get("meta", {})
    require(meta.get("generated_at_turn") == state["turn_count"], "room-summary generated_at_turn must match.")


def validate_upgrade_output(upgrade_output: dict[str, Any], state: dict[str, Any]) -> None:
    if "error" in upgrade_output:
        raise RoomRuntimeError(f"room-upgrade returned error: {upgrade_output['error']}")

    packet = upgrade_output.get("handoff_packet")
    require(isinstance(packet, dict), "room-upgrade output must include handoff_packet.")
    require(packet.get("schema_version") == "v0.1", "handoff packet must use schema_version v0.1.")
    require(packet.get("generated_at_turn") == state["turn_count"], "handoff packet generated_at_turn must match.")
    require(packet.get("source_room_id") == state["room_id"], "handoff packet source_room_id must match room_id.")
    require(packet.get("field_01_original_topic") == state["original_topic"], "field_01 must match original_topic.")
    require(packet.get("field_02_room_title") == state["title"], "field_02 must match room title.")

    field_03 = packet.get("field_03_type")
    require(isinstance(field_03, dict), "field_03_type must be an object.")
    require(field_03.get("primary") == state["primary_type"], "field_03_type.primary must match state.")
    require(field_03.get("secondary") == state["secondary_type"], "field_03_type.secondary must match state.")

    require(isinstance(packet.get("field_04_sub_problems"), list), "field_04_sub_problems must be an array.")
    require(
        packet.get("field_05_consensus_points") == state["consensus_points"],
        "field_05_consensus_points must match the persisted summary.",
    )
    require(
        packet.get("field_06_tension_points") == state["tension_points"],
        "field_06_tension_points must match the persisted summary.",
    )
    require(
        packet.get("field_07_open_questions") == state["open_questions"],
        "field_07_open_questions must match the persisted summary.",
    )
    require(isinstance(packet.get("field_08_candidate_solutions"), list), "field_08_candidate_solutions must be an array.")
    require(isinstance(packet.get("field_09_factual_claims"), list), "field_09_factual_claims must be an array.")
    require(isinstance(packet.get("field_10_uncertainty_points"), list), "field_10_uncertainty_points must be an array.")

    suggested_agents = packet.get("field_11_suggested_agents")
    require(
        isinstance(suggested_agents, list) and 3 <= len(suggested_agents) <= 5,
        "field_11_suggested_agents must contain 3-5 agents.",
    )
    agent_roles = packet.get("field_12_suggested_agent_roles")
    require(isinstance(agent_roles, dict), "field_12_suggested_agent_roles must be an object.")
    for agent_id in suggested_agents:
        require(agent_id in load_registry(), f"Suggested agent is not registered: {agent_id}")
        require(agent_id in agent_roles, f"Missing suggested agent role text for {agent_id}")

    upgrade_reason = packet.get("field_13_upgrade_reason")
    require(isinstance(upgrade_reason, dict), "field_13_upgrade_reason must be an object.")
    require(
        upgrade_reason.get("reason_code") in VALID_UPGRADE_REASONS,
        "field_13_upgrade_reason.reason_code is invalid.",
    )
    require(
        upgrade_reason.get("reason_code") == state["upgrade_signal"]["reason"],
        "field_13_upgrade_reason.reason_code must match the room upgrade_signal.",
    )
    require(
        upgrade_reason.get("triggered_by") in {"auto_rule", "user_explicit"},
        "field_13_upgrade_reason.triggered_by is invalid.",
    )
    require(
        isinstance(upgrade_reason.get("reason_text"), str) and bool(upgrade_reason["reason_text"].strip()),
        "field_13_upgrade_reason.reason_text must be non-empty.",
    )
    confidence = upgrade_reason.get("confidence")
    require(isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0, "upgrade confidence must be 0-1.")
    warning_flags = upgrade_reason.get("warning_flags")
    require(isinstance(warning_flags, list), "field_13_upgrade_reason.warning_flags must be an array.")

    packaging_meta = upgrade_output.get("packaging_meta")
    require(isinstance(packaging_meta, dict), "packaging_meta must be an object.")
    meta = upgrade_output.get("meta")
    require(isinstance(meta, dict), "room-upgrade meta must be an object.")
    require(meta.get("generated_at_turn") == state["turn_count"], "room-upgrade generated_at_turn must match.")
    require(
        meta.get("next_action") == "pass_packet_to_debate_skill",
        "room-upgrade meta.next_action must point to debate skill.",
    )


def validate_debate_acceptance(packet: dict[str, Any]) -> dict[str, Any]:
    require(DEBATE_SKILL_PATH.exists(), "debate-roundtable-skill entry is missing.")
    require(DEBATE_PACKET_VALIDATOR_PATH.exists(), "debate packet validator runtime is missing.")

    validator = load_debate_packet_validator()
    try:
        acceptance = validator(packet)
    except Exception as exc:
        raise RoomRuntimeError(f"debate packet validator rejected handoff packet: {exc}") from exc

    require(isinstance(acceptance, dict), "debate packet validator must return an object.")
    require(acceptance.get("accepted") is True, "debate packet validator did not accept the handoff packet.")
    return acceptance


def load_debate_packet_validator():
    spec = importlib.util.spec_from_file_location(
        "round_table_debate_packet_validator",
        DEBATE_PACKET_VALIDATOR_PATH,
    )
    require(spec is not None and spec.loader is not None, "failed to load debate packet validator module.")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise RoomRuntimeError(f"failed to import debate packet validator: {exc}") from exc

    validator = getattr(module, "validate_handoff_packet", None)
    require(callable(validator), "debate packet validator must expose validate_handoff_packet().")
    return validator


def compute_silent_rounds(state: dict[str, Any], turn: dict[str, Any]) -> dict[str, int]:
    selected = {speaker["agent_id"] for speaker in turn["speakers"]}
    silent_rounds: dict[str, int] = {}
    for agent_id in state["agents"]:
        previous = state["silent_rounds"].get(agent_id, 0)
        silent_rounds[agent_id] = 0 if agent_id in selected else previous + 1
    return silent_rounds


def build_recent_log(conversation_log: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for turn in conversation_log[-3:]:
        speaker_bits = []
        for speaker in turn["speakers"]:
            speaker_bits.append(
                f"{speaker['short_name']}[{speaker['role']}] {short_text(speaker['content'], 24)}"
            )
        chunks.append(f"Turn {turn['turn_id']} ({turn['stage']}): " + ", ".join(speaker_bits))
    recent_log = "; ".join(chunks)
    return short_text(recent_log, 500)


def detect_upgrade_signal(state: dict[str, Any]) -> dict[str, Any] | None:
    turn_count = state["turn_count"]
    last_summary_turn = state.get("last_summary_turn")
    if (
        state["last_stage"] == "decision"
        and len(state["tension_points"]) >= 2
        and (last_summary_turn is None or turn_count - last_summary_turn >= 3)
    ):
        return {
            "triggered_at_turn": turn_count,
            "reason": "reached_decision_stage_with_tension",
            "tension_unresolved": True,
            "confidence": 0.8,
            "handoff_ready": False,
        }

    recent_two = state["conversation_log"][-2:]
    if len(recent_two) == 2 and all(turn.get("forced_rebalance") for turn in recent_two):
        return {
            "triggered_at_turn": turn_count,
            "reason": "forced_rebalance_repeated",
            "tension_unresolved": bool(state["tension_points"]),
            "confidence": 0.75,
            "handoff_ready": False,
        }

    recent_three = state["conversation_log"][-3:]
    tokens_high = sum(
        1 for turn in recent_three if int(turn.get("meta", {}).get("tokens_used_estimate", 0)) > 2500
    )
    if len(recent_three) == 3 and tokens_high >= 2:
        return {
            "triggered_at_turn": turn_count,
            "reason": "token_budget_repeatedly_exceeded",
            "tension_unresolved": bool(state["tension_points"]),
            "confidence": 0.7,
            "handoff_ready": False,
        }

    return state.get("upgrade_signal")


def load_registry() -> dict[str, dict[str, Any]]:
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("| agent_id | short_name | structural_role |"):
            start = index + 2
            break
    if start is None:
        raise RoomRuntimeError("Could not locate the registry table in docs/agent-registry.md.")

    registry: dict[str, dict[str, Any]] = {}
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [clean_table_cell(part) for part in stripped.strip("|").split("|")]
        if len(cells) != 9:
            continue
        agent_id = cells[0]
        registry[agent_id] = {
            "agent_id": agent_id,
            "short_name": cells[1],
            "structural_role": cells[2],
            "expression": cells[3],
            "strength": cells[4],
            "default_excluded": cells[5] == "yes",
            "task_types": split_csv_field(cells[6]),
            "stage_fit": split_csv_field(cells[7]),
            "sub_problem_tags": split_csv_field(cells[8]),
        }
    if not registry:
        raise RoomRuntimeError("Agent registry is empty after parsing docs/agent-registry.md.")
    return registry


def load_state(state_root: Path, room_id: str) -> dict[str, Any]:
    state_path = get_room_dir(state_root, room_id) / "state.json"
    if not state_path.exists():
        raise RoomRuntimeError(f"Room state does not exist: {state_path}")
    return load_json(state_path)


def save_state(state_root: Path, state: dict[str, Any]) -> None:
    room_dir = get_room_dir(state_root, state["room_id"])
    ensure_directory(room_dir)
    write_json(room_dir / "state.json", state)


def get_room_dir(state_root: Path, room_id: str) -> Path:
    return state_root / room_id


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RoomRuntimeError(f"JSON file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RoomRuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def materialize_placeholders(payload: Any, replacements: dict[str, str]) -> Any:
    if isinstance(payload, dict):
        return {key: materialize_placeholders(value, replacements) for key, value in payload.items()}
    if isinstance(payload, list):
        return [materialize_placeholders(item, replacements) for item in payload]
    if isinstance(payload, str):
        return replacements.get(payload, payload)
    return payload


def normalize_room_topic(topic: str) -> str:
    text = topic.strip()
    if text.startswith("/room"):
        text = text[5:].strip()
    if not text:
        raise RoomRuntimeError("Room topic cannot be empty.")
    return text


def normalize_turn_input(raw_user_input: str) -> tuple[str, str | None]:
    text = raw_user_input.strip()
    if text.startswith("/focus"):
        focus = text[6:].strip()
        require(bool(focus), "/focus requires non-empty focus text.")
        return text, focus
    return text, None


def derive_room_title(topic: str) -> str:
    text = normalize_room_topic(topic)
    text = re.sub(r"^(我想讨论一个|我想讨论|想讨论一个|想讨论)\s*", "", text)
    title = re.split(r"[，。！？?！]", text, maxsplit=1)[0].strip()
    title = re.sub(r"\s+", " ", title)
    return short_text(title or text, 32)


def truncate_content(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    window = text[:limit]
    sentence_end = max(window.rfind("。"), window.rfind("！"), window.rfind("？"), window.rfind("."))
    if sentence_end >= 0:
        return window[: sentence_end + 1] + "[...]"
    return window.rstrip() + "[...]"


def short_text(text: str, limit: int) -> str:
    compact = normalize_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 3)].rstrip() + "..."


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def split_csv_field(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def clean_table_cell(text: str) -> str:
    return text.strip().strip("`")


def first_opposite_structural_role(speakers: list[dict[str, Any]], primary_index: int) -> int | None:
    primary_role = speakers[primary_index]["structural_role"]
    for index in range(primary_index + 1, len(speakers)):
        if speakers[index]["structural_role"] != primary_role:
            return index
    return None


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RoomRuntimeError(message)


def generate_room_id() -> str:
    return f"room-{uuid.uuid4().hex[:8]}"


if __name__ == "__main__":
    sys.exit(main())
