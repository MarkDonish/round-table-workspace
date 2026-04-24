#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEBATE_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"
if str(DEBATE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(DEBATE_RUNTIME_DIR))

import debate_runtime
import room_runtime


DEFAULT_ROOM_FIXTURES_DIR = RUNTIME_DIR / "fixtures" / "canonical"
DEFAULT_DEBATE_FIXTURES_DIR = DEBATE_RUNTIME_DIR / "fixtures" / "canonical"


def main() -> int:
    task_prompt = sys.stdin.read()
    try:
        prompt_path = extract_prompt_path(task_prompt)
        prompt_input = extract_structured_input(task_prompt)
        if prompt_path is None or prompt_input is None:
            payload = {"ok": True, "mode": "generic_fixture_agent"}
        else:
            payload = load_fixture_payload(prompt_path=prompt_path, prompt_input=prompt_input)
    except (ValueError, json.JSONDecodeError, room_runtime.RoomRuntimeError, debate_runtime.DebateRuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    output_path = os.environ.get("ROUND_TABLE_OUTPUT_JSON", "").strip()
    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output_text, encoding="utf-8")
    else:
        sys.stdout.write(output_text)
    return 0


def extract_prompt_path(task_prompt: str) -> Path | None:
    for line in task_prompt.splitlines():
        if line.startswith("Prompt path: "):
            raw_path = line.split("Prompt path: ", 1)[1].strip()
            return Path(raw_path)
    return None


def extract_structured_input(task_prompt: str) -> dict[str, Any] | None:
    marker = "Structured input:"
    marker_index = task_prompt.find(marker)
    if marker_index < 0:
        return None
    after_marker = task_prompt[marker_index + len(marker) :].lstrip()
    if not after_marker.startswith("```"):
        raise ValueError("structured input block is missing a JSON fence.")
    newline_index = after_marker.find("\n")
    if newline_index < 0:
        raise ValueError("structured input JSON fence is malformed.")
    json_start = newline_index + 1
    json_end = after_marker.find("\n```", json_start)
    if json_end < 0:
        raise ValueError("structured input JSON fence is not closed.")
    payload = json.loads(after_marker[json_start:json_end])
    if not isinstance(payload, dict):
        raise ValueError("structured input must be a JSON object.")
    return payload


def load_fixture_payload(*, prompt_path: Path, prompt_input: dict[str, Any]) -> dict[str, Any]:
    prompt_name = prompt_path.name
    if prompt_name.startswith("room-"):
        return load_room_fixture(prompt_name=prompt_name, prompt_input=prompt_input)
    if prompt_name.startswith("debate-"):
        return load_debate_fixture(prompt_name=prompt_name, prompt_input=prompt_input)
    raise ValueError(f"unsupported prompt for generic fixture agent: {prompt_path}")


def load_room_fixture(*, prompt_name: str, prompt_input: dict[str, Any]) -> dict[str, Any]:
    fixtures_dir = Path(os.environ.get("ROUND_TABLE_ROOM_FIXTURES_DIR", str(DEFAULT_ROOM_FIXTURES_DIR))).expanduser()
    room_id = resolve_room_id(prompt_input)
    if prompt_name == "room-selection.md":
        mode = prompt_input.get("mode")
        if mode == "room_full":
            fixture_name = "room_full.selection.json"
        elif mode == "room_turn":
            topic = str(prompt_input.get("topic", "")).strip()
            fixture_name = "focus_turn.selection.json" if topic.startswith("/focus") else "initial_turn.selection.json"
        else:
            raise ValueError(f"unsupported room-selection mode for fixture agent: {mode}")
    elif prompt_name == "room-chat.md":
        turn_id = int(prompt_input.get("turn_id", 0))
        if turn_id == 1:
            fixture_name = "initial_turn.chat.json"
        elif turn_id == 2:
            fixture_name = "focus_turn.chat.json"
        else:
            raise ValueError(f"unsupported room-chat turn_id for fixture agent: {turn_id}")
    elif prompt_name == "room-summary.md":
        fixture_name = "summary.json"
    elif prompt_name == "room-upgrade.md":
        fixture_name = "upgrade.json"
    else:
        raise ValueError(f"unsupported room prompt for fixture agent: {prompt_name}")

    payload = room_runtime.load_json(fixtures_dir / fixture_name)
    return room_runtime.materialize_placeholders(payload, {"__ROOM_ID__": room_id})


def load_debate_fixture(*, prompt_name: str, prompt_input: dict[str, Any]) -> dict[str, Any]:
    fixtures_dir = Path(
        os.environ.get("ROUND_TABLE_DEBATE_FIXTURES_DIR", str(DEFAULT_DEBATE_FIXTURES_DIR))
    ).expanduser()
    debate_id = resolve_debate_id(prompt_input)
    room_id = resolve_room_id(prompt_input)
    if prompt_name == "debate-roundtable.md":
        fixture_name = "roundtable_record.json"
    elif prompt_name == "debate-reviewer.md":
        if prompt_input.get("followup_round") == 1:
            fixture_name = "followup_review_result_allow.json"
        elif prompt_input.get("scenario") == "allow":
            fixture_name = "review_result.json"
        else:
            fixture_name = "followup_review_result_reject.json"
    elif prompt_name == "debate-followup.md":
        fixture_name = "followup_record.json"
    else:
        raise ValueError(f"unsupported debate prompt for fixture agent: {prompt_name}")

    payload = debate_runtime.load_json(fixtures_dir / fixture_name)
    return debate_runtime.materialize_placeholders(
        payload,
        {
            "__ROOM_ID__": room_id,
            "__DEBATE_ID__": debate_id,
        },
    )


def resolve_room_id(prompt_input: dict[str, Any]) -> str:
    env_room_id = os.environ.get("ROUND_TABLE_ROOM_ID", "").strip()
    if env_room_id:
        return env_room_id
    for key in ("source_room_id", "room_id"):
        value = prompt_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    room_state = prompt_input.get("room_state")
    if isinstance(room_state, dict):
        value = room_state.get("room_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    current_state = prompt_input.get("current_state")
    if isinstance(current_state, dict):
        value = current_state.get("room_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("ROUND_TABLE_ROOM_ID is required for this generic fixture prompt.")


def resolve_debate_id(prompt_input: dict[str, Any]) -> str:
    env_debate_id = os.environ.get("ROUND_TABLE_DEBATE_ID", "").strip()
    if env_debate_id:
        return env_debate_id
    value = prompt_input.get("debate_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("ROUND_TABLE_DEBATE_ID is required for this generic fixture prompt.")


if __name__ == "__main__":
    sys.exit(main())
