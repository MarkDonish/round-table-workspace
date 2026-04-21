#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import uuid
from pathlib import Path
from typing import Any

import chat_completions_executor as provider_executor
import room_runtime as runtime


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_FIXTURES_DIR = RUNTIME_DIR / "fixtures" / "canonical"
ROOM_SELECTION_PROMPT = REPO_ROOT / "prompts" / "room-selection.md"
ROOM_CHAT_PROMPT = REPO_ROOT / "prompts" / "room-chat.md"
ROOM_SUMMARY_PROMPT = REPO_ROOT / "prompts" / "room-summary.md"
ROOM_UPGRADE_PROMPT = REPO_ROOT / "prompts" / "room-upgrade.md"
DEFAULT_TOPIC = "我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。"
DEFAULT_FOLLOW_UP = "/focus 先只盯最小可验证切口"


class RoomE2EValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_validation(args)
    except (
        RoomE2EValidationError,
        runtime.RoomRuntimeError,
        provider_executor.ProviderConfigError,
        urllib.error.URLError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the checked-in /room end-to-end validation flow through either "
            "canonical fixtures or a Chat Completions-compatible provider."
        )
    )
    parser.add_argument(
        "--executor",
        required=True,
        choices=["fixture", "chat_completions"],
        help="Execution backend for prompt calls.",
    )
    parser.add_argument(
        "--env-file",
        help="Explicit env file for Chat Completions mode.",
    )
    parser.add_argument(
        "--fixtures-dir",
        default=str(DEFAULT_FIXTURES_DIR),
        help="Fixture directory for fixture mode.",
    )
    parser.add_argument(
        "--state-root",
        default=str(runtime.DEFAULT_STATE_ROOT),
        help="Directory for persisted room state.",
    )
    parser.add_argument(
        "--room-id",
        help="Optional stable room id. Defaults to a generated validation id.",
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help="The initial /room topic to validate.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=DEFAULT_FOLLOW_UP,
        help="The second-step follow-up input. Defaults to the canonical focus turn.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for Chat Completions mode.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    topic = runtime.normalize_room_topic(args.topic)
    follow_up_input = args.follow_up_input.strip()
    if not follow_up_input:
        raise RoomE2EValidationError("follow-up input cannot be empty.")

    state_root = Path(args.state_root).expanduser().resolve()
    room_id = args.room_id or f"room-e2e-{uuid.uuid4().hex[:8]}"
    registry = runtime.load_registry()
    room_dir = runtime.get_room_dir(state_root, room_id)
    runtime.ensure_directory(room_dir)

    executor = build_prompt_executor(args, room_id)

    room_full_input = build_selection_input(mode="room_full", request_text=topic, state=None)
    room_full_output = execute_prompt(
        executor=executor,
        room_dir=room_dir,
        prompt_path=ROOM_SELECTION_PROMPT,
        step_index=1,
        step_name="room_full.selection",
        prompt_input=room_full_input,
    )
    runtime.validate_room_full_output(room_full_output, registry)
    state = runtime.build_initial_state(topic=topic, room_id=room_id, room_full=room_full_output, registry=registry)
    runtime.write_json(room_dir / "room_full.selection.json", room_full_output)
    runtime.save_state(state_root, state)

    latest_sub_problems = room_full_output["parsed_topic"].get("sub_problems", [])

    state, first_turn_result, first_selection_output, first_chat_output = run_turn_step(
        executor=executor,
        state=state,
        state_root=state_root,
        room_dir=room_dir,
        raw_user_input=topic,
        step_index=2,
        registry=registry,
    )
    latest_sub_problems = first_selection_output["parsed_topic"].get("sub_problems", latest_sub_problems)

    state, second_turn_result, second_selection_output, second_chat_output = run_turn_step(
        executor=executor,
        state=state,
        state_root=state_root,
        room_dir=room_dir,
        raw_user_input=follow_up_input,
        step_index=4,
        registry=registry,
    )
    latest_sub_problems = second_selection_output["parsed_topic"].get("sub_problems", latest_sub_problems)

    summary_input = build_summary_input(state=state, trigger="user_request")
    summary_output = execute_prompt(
        executor=executor,
        room_dir=room_dir,
        prompt_path=ROOM_SUMMARY_PROMPT,
        step_index=6,
        step_name="summary",
        prompt_input=summary_input,
    )
    state, summary_result = runtime.apply_summary(
        state=state,
        summary_output=summary_output,
        trigger="/summary",
        state_root=state_root,
    )

    effective_upgrade_signal = build_effective_upgrade_signal(state)
    upgrade_input = build_upgrade_input(
        state=state,
        upgrade_signal=effective_upgrade_signal,
        selection_sub_problems=latest_sub_problems,
    )
    upgrade_output = execute_prompt(
        executor=executor,
        room_dir=room_dir,
        prompt_path=ROOM_UPGRADE_PROMPT,
        step_index=7,
        step_name="upgrade",
        prompt_input=upgrade_input,
    )
    state, upgrade_result = runtime.apply_upgrade(
        state=state,
        upgrade_output=upgrade_output,
        explicit_user_request=effective_upgrade_signal["reason"] == "user_explicit_request",
        state_root=state_root,
    )

    report = {
        "ok": True,
        "action": "room-e2e-validation",
        "executor": args.executor,
        "room_id": room_id,
        "topic": topic,
        "follow_up_input": follow_up_input,
        "state_path": str(room_dir / "state.json"),
        "prompt_call_dir": str(room_dir / "prompt-calls"),
        "conversation_turns": state["turn_count"],
        "summary_turn": state["last_summary_turn"],
        "upgrade_signal": state["upgrade_signal"],
        "provider_config": describe_executor(args),
        "artifacts": {
            "room_dir": str(room_dir),
            "room_full_selection": str(room_dir / "room_full.selection.json"),
            "turn_001_selection": str(room_dir / "turns" / "turn-001.selection.json"),
            "turn_001_chat": str(room_dir / "turns" / "turn-001.chat.json"),
            "turn_001": str(room_dir / "turns" / "turn-001.turn.json"),
            "turn_002_selection": str(room_dir / "turns" / "turn-002.selection.json"),
            "turn_002_chat": str(room_dir / "turns" / "turn-002.chat.json"),
            "turn_002": str(room_dir / "turns" / "turn-002.turn.json"),
            "summary": str(room_dir / "summary" / f"summary-turn-{state['last_summary_turn']:03d}.json"),
            "handoff_packet": str(room_dir / "handoff" / f"packet-turn-{state['turn_count']:03d}.json"),
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
            "summary_persisted": bool((room_dir / "summary" / f"summary-turn-{state['last_summary_turn']:03d}.json").exists()),
            "handoff_packet_persisted": bool((room_dir / "handoff" / f"packet-turn-{state['turn_count']:03d}.json").exists()),
            "debate_preflight_accepts_packet": upgrade_result["debate_acceptance"]["accepted"],
        },
    }
    runtime.write_json(room_dir / "validation-report.json", report)
    return report


def build_prompt_executor(args: argparse.Namespace, room_id: str):
    if args.executor == "fixture":
        topic = runtime.normalize_room_topic(args.topic)
        if topic != DEFAULT_TOPIC or args.follow_up_input.strip() != DEFAULT_FOLLOW_UP:
            raise RoomE2EValidationError(
                "fixture mode only supports the checked-in canonical topic and follow-up input."
            )
        fixtures_dir = Path(args.fixtures_dir).expanduser().resolve()

        def execute(prompt_path: Path, prompt_input: dict[str, Any]) -> dict[str, Any]:
            return load_fixture_output(
                fixtures_dir=fixtures_dir,
                room_id=room_id,
                prompt_path=prompt_path,
                prompt_input=prompt_input,
            )

        return execute

    env = dict(os.environ)
    if args.env_file:
        env.update(provider_executor.load_env_file(Path(args.env_file)))
    config = provider_executor.read_provider_config(env)

    def execute(prompt_path: Path, prompt_input: dict[str, Any]) -> dict[str, Any]:
        return provider_executor.call_chat_completions(
            config=config,
            prompt_text=prompt_path.read_text(encoding="utf-8"),
            prompt_input=prompt_input,
            temperature=args.temperature,
        )

    return execute


def describe_executor(args: argparse.Namespace) -> dict[str, Any]:
    if args.executor == "fixture":
        return {
            "mode": "fixture",
            "fixtures_dir": str(Path(args.fixtures_dir).expanduser().resolve()),
        }

    env = dict(os.environ)
    if args.env_file:
        env.update(provider_executor.load_env_file(Path(args.env_file)))
    config = provider_executor.read_provider_config(env)
    return {
        "mode": "chat_completions",
        "env_file": str(Path(args.env_file).expanduser().resolve()) if args.env_file else None,
        "url": provider_executor.mask_value(config["url"]),
        "model": provider_executor.mask_value(config["model"]),
        "auth_configured": bool(config.get("auth_bearer")),
        "timeout_seconds": config["timeout_seconds"],
        "temperature": args.temperature,
    }


def execute_prompt(
    *,
    executor,
    room_dir: Path,
    prompt_path: Path,
    step_index: int,
    step_name: str,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    output = executor(prompt_path, prompt_input)
    persist_prompt_call(
        room_dir=room_dir,
        step_index=step_index,
        step_name=step_name,
        prompt_path=prompt_path,
        prompt_input=prompt_input,
        prompt_output=output,
    )
    return output


def persist_prompt_call(
    *,
    room_dir: Path,
    step_index: int,
    step_name: str,
    prompt_path: Path,
    prompt_input: dict[str, Any],
    prompt_output: dict[str, Any],
) -> None:
    call_dir = room_dir / "prompt-calls"
    runtime.ensure_directory(call_dir)
    base_name = f"{step_index:03d}-{step_name.replace('.', '-')}"
    runtime.write_json(call_dir / f"{base_name}.input.json", prompt_input)
    runtime.write_json(call_dir / f"{base_name}.output.json", prompt_output)
    runtime.write_json(
        call_dir / f"{base_name}.meta.json",
        {
            "step": step_name,
            "prompt_path": str(prompt_path),
        },
    )


def run_turn_step(
    *,
    executor,
    state: dict[str, Any],
    state_root: Path,
    room_dir: Path,
    raw_user_input: str,
    step_index: int,
    registry: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    selection_input = build_selection_input(mode="room_turn", request_text=raw_user_input, state=state)
    selection_output = execute_prompt(
        executor=executor,
        room_dir=room_dir,
        prompt_path=ROOM_SELECTION_PROMPT,
        step_index=step_index,
        step_name=f"turn-{state['turn_count'] + 1:03d}.selection",
        prompt_input=selection_input,
    )
    runtime.validate_room_turn_output(selection_output, state, registry)
    assigned_speakers = runtime.assign_turn_roles(selection_output, state, registry)

    chat_input = build_chat_input(
        state=state,
        raw_user_input=raw_user_input,
        selection_output=selection_output,
        assigned_speakers=assigned_speakers,
    )
    chat_output = execute_prompt(
        executor=executor,
        room_dir=room_dir,
        prompt_path=ROOM_CHAT_PROMPT,
        step_index=step_index + 1,
        step_name=f"turn-{state['turn_count'] + 1:03d}.chat",
        prompt_input=chat_input,
    )
    updated_state, result = runtime.apply_turn(
        state=state,
        raw_user_input=raw_user_input,
        selection_output=selection_output,
        chat_output=chat_output,
        state_root=state_root,
    )
    return updated_state, result, selection_output, chat_output


def build_selection_input(
    *,
    mode: str,
    request_text: str,
    state: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "topic": request_text,
        "user_constraints": build_user_constraints(request_text),
        "current_state": {
            "roster": state["agents"] if state else None,
            "last_stage": state["last_stage"] if state else None,
            "recent_log": state["recent_log"] if state else None,
            "silent_rounds": state["silent_rounds"] if state else None,
        },
        "patch_action": None,
    }


def build_chat_input(
    *,
    state: dict[str, Any],
    raw_user_input: str,
    selection_output: dict[str, Any],
    assigned_speakers: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_input, new_focus = runtime.normalize_turn_input(raw_user_input)
    active_focus = new_focus if new_focus is not None else state["active_focus"]
    stage = selection_output["parsed_topic"]["stage"]

    agents = [
        {
            "id": agent_id,
            "short_name": role["short_name"],
            "structural_role": role["structural_role"],
            "long_role": role["role_summary"],
        }
        for agent_id, role in state["agent_roles"].items()
    ]
    speakers = [
        {
            "id": speaker["agent_id"],
            "short_name": speaker["short_name"],
            "turn_role": speaker["turn_role"],
            "long_role": state["agent_roles"][speaker["agent_id"]]["role_summary"],
            "structural_role": speaker["structural_role"],
            "total_score": speaker["total"],
        }
        for speaker in assigned_speakers
    ]
    conversation_history = [
        {
            "turn_id": turn["turn_id"],
            "stage": turn["stage"],
            "speakers": [
                {
                    "id": speaker["agent_id"],
                    "short_name": speaker["short_name"],
                    "role": speaker["role"],
                    "content_summary": runtime.short_text(speaker["content"], 80),
                }
                for speaker in turn["speakers"]
            ],
        }
        for turn in state["conversation_log"]
    ]

    return {
        "mode": "room_chat",
        "turn_id": state["turn_count"] + 1,
        "stage": stage,
        "active_focus": active_focus,
        "primary_type": state["primary_type"],
        "secondary_type": state["secondary_type"],
        "user_input": normalized_input,
        "agents": agents,
        "speakers": speakers,
        "recent_log": state["recent_log"],
        "conversation_history": conversation_history,
    }


def build_summary_input(*, state: dict[str, Any], trigger: str) -> dict[str, Any]:
    return {
        "mode": "room_summary",
        "trigger": trigger,
        "current_turn": state["turn_count"],
        "stage": state["last_stage"],
        "primary_type": state["primary_type"],
        "secondary_type": state["secondary_type"],
        "active_focus": state["active_focus"],
        "original_topic": state["original_topic"],
        "agents": [
            {
                "id": agent_id,
                "short_name": role["short_name"],
                "structural_role": role["structural_role"],
            }
            for agent_id, role in state["agent_roles"].items()
        ],
        "conversation_log": state["conversation_log"],
        "previous_summary": {
            "consensus_points": state["consensus_points"],
            "open_questions": state["open_questions"],
            "tension_points": state["tension_points"],
            "recommended_next_step": state["recommended_next_step"],
            "last_summary_turn": state.get("last_summary_turn"),
        },
    }


def build_effective_upgrade_signal(state: dict[str, Any]) -> dict[str, Any]:
    upgrade_signal = state.get("upgrade_signal")
    if upgrade_signal is not None:
        return upgrade_signal
    return {
        "triggered_at_turn": state["turn_count"],
        "reason": "user_explicit_request",
        "tension_unresolved": bool(state["tension_points"]),
        "confidence": 0.8,
        "handoff_ready": False,
    }


def build_upgrade_input(
    *,
    state: dict[str, Any],
    upgrade_signal: dict[str, Any],
    selection_sub_problems: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "mode": "room_upgrade",
        "current_turn": state["turn_count"],
        "trigger": "user_explicit" if upgrade_signal["reason"] == "user_explicit_request" else "auto_rule",
        "upgrade_signal": upgrade_signal,
        "room_state": {
            "room_id": state["room_id"],
            "title": state["title"],
            "mode": state["mode"],
            "original_topic": state["original_topic"],
            "primary_type": state["primary_type"],
            "secondary_type": state["secondary_type"],
            "active_focus": state["active_focus"],
            "agents": [
                {
                    "id": agent_id,
                    "short_name": role["short_name"],
                    "structural_role": role["structural_role"],
                    "long_role": role["role_summary"],
                }
                for agent_id, role in state["agent_roles"].items()
            ],
            "agent_roles": {
                agent_id: role["role_summary"] for agent_id, role in state["agent_roles"].items()
            },
            "consensus_points": state["consensus_points"],
            "open_questions": state["open_questions"],
            "tension_points": state["tension_points"],
            "recommended_next_step": state["recommended_next_step"],
            "silent_rounds": state["silent_rounds"],
        },
        "conversation_log": state["conversation_log"],
        "previous_summary_meta": {
            "last_summary_turn": state.get("last_summary_turn"),
        },
        "selection_context": {
            "sub_problems": selection_sub_problems,
        },
    }


def build_user_constraints(request_text: str) -> dict[str, Any]:
    mentioned_agents = parse_mentions(request_text)
    return {
        "with": [],
        "without": [],
        "mentions": mentioned_agents,
        "topic_hint": None,
    }


def parse_mentions(request_text: str) -> list[str]:
    registry = runtime.load_registry()
    lookup: dict[str, str] = {}
    for agent_id, entry in registry.items():
        lookup[agent_id.lower()] = agent_id
        lookup[entry["short_name"].lower()] = agent_id

    mentions: list[str] = []
    for token in request_text.split():
        if not token.startswith("@") or len(token) <= 1:
            continue
        normalized = token[1:].strip(",，。.!?:：;；").lower()
        agent_id = lookup.get(normalized)
        if agent_id and agent_id not in mentions:
            mentions.append(agent_id)
    return mentions


def load_fixture_output(
    *,
    fixtures_dir: Path,
    room_id: str,
    prompt_path: Path,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    if prompt_path == ROOM_SELECTION_PROMPT:
        mode = prompt_input["mode"]
        if mode == "room_full":
            fixture_name = "room_full.selection.json"
        elif mode == "room_turn":
            topic = str(prompt_input.get("topic", ""))
            fixture_name = "focus_turn.selection.json" if topic.startswith("/focus") else "initial_turn.selection.json"
        else:
            raise RoomE2EValidationError(f"fixture mode does not support selection mode: {mode}")
    elif prompt_path == ROOM_CHAT_PROMPT:
        turn_id = prompt_input.get("turn_id")
        if turn_id == 1:
            fixture_name = "initial_turn.chat.json"
        elif turn_id == 2:
            fixture_name = "focus_turn.chat.json"
        else:
            raise RoomE2EValidationError(f"fixture mode only supports turn 1-2 chat fixtures, got {turn_id}")
    elif prompt_path == ROOM_SUMMARY_PROMPT:
        fixture_name = "summary.json"
    elif prompt_path == ROOM_UPGRADE_PROMPT:
        fixture_name = "upgrade.json"
    else:
        raise RoomE2EValidationError(f"unsupported prompt in fixture mode: {prompt_path}")

    payload = runtime.load_json(fixtures_dir / fixture_name)
    return runtime.materialize_placeholders(payload, {"__ROOM_ID__": room_id})


if __name__ == "__main__":
    sys.exit(main())
