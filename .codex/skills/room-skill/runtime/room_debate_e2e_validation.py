#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import uuid
from pathlib import Path
from typing import Any

import generic_agent_executor as generic_executor
import chat_completions_executor as provider_executor
import local_codex_executor as local_executor
import room_e2e_validation as room_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEBATE_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"
if str(DEBATE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(DEBATE_RUNTIME_DIR))

import debate_e2e_validation as debate_validation


DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "room-debate-e2e"
DEFAULT_LOCAL_CODEX_PRESET = "gpt54_family"


class RoomDebateE2EValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_validation(args)
    except (
        RoomDebateE2EValidationError,
        room_validation.RoomE2EValidationError,
        debate_validation.DebateE2EValidationError,
        provider_executor.ProviderConfigError,
        generic_executor.GenericAgentExecutorError,
        local_executor.LocalCodexExecutorError,
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
            "Run the checked-in /room -> /debate integration validation flow through either "
            "canonical fixtures, local agent CLIs, local Codex child tasks, or Chat Completions-compatible providers."
        )
    )
    parser.add_argument(
        "--executor",
        required=True,
        choices=["fixture", "generic_cli", "claude_code", "local_codex", "chat_completions"],
        help="Execution backend for both /room and /debate prompt calls.",
    )
    parser.add_argument(
        "--room-env-file",
        help="Explicit env file for /room Chat Completions mode.",
    )
    parser.add_argument(
        "--debate-env-file",
        help="Explicit env file for /debate Chat Completions mode.",
    )
    parser.add_argument(
        "--room-fixtures-dir",
        default=str(room_validation.DEFAULT_FIXTURES_DIR),
        help="Fixture directory for /room fixture mode.",
    )
    parser.add_argument(
        "--debate-fixtures-dir",
        default=str(debate_validation.DEFAULT_FIXTURES_DIR),
        help="Fixture directory for /debate fixture mode.",
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted integration evidence.",
    )
    parser.add_argument(
        "--flow-id",
        help="Optional stable integration flow id.",
    )
    parser.add_argument(
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="The initial /room topic to validate.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=room_validation.DEFAULT_FOLLOW_UP,
        help="The second-step follow-up input for /room.",
    )
    parser.add_argument(
        "--scenario",
        default="reject_followup",
        choices=["allow", "reject_followup"],
        help="Which checked-in /debate path to validate after /room produces the packet.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for Chat Completions mode.",
    )
    parser.add_argument(
        "--local-codex-preset",
        choices=sorted(local_executor.LOCAL_CODEX_PRESETS),
        default=DEFAULT_LOCAL_CODEX_PRESET,
        help="Checked-in local Codex preset. Defaults to the validated local mainline preset.",
    )
    parser.add_argument("--local-codex-model", help="Optional model override for local Codex child tasks.")
    parser.add_argument(
        "--local-codex-fallback-models",
        help="Optional comma-separated fallback models for local Codex child tasks.",
    )
    parser.add_argument("--local-codex-profile", help="Optional Codex profile for local Codex child tasks.")
    parser.add_argument(
        "--local-codex-reasoning-effort",
        default=None,
        help="Reasoning effort override for local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-sandbox",
        default=None,
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode for local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-timeout-seconds",
        type=int,
        default=None,
        help="Timeout for one local Codex child task.",
    )
    parser.add_argument(
        "--local-codex-timeout-retries",
        type=int,
        default=None,
        help="How many times to retry a timed-out or transiently disconnected local Codex child task.",
    )
    parser.add_argument(
        "--local-codex-retry-timeout-multiplier",
        type=float,
        default=None,
        help="Multiplier applied to the timeout on each retry after a timeout.",
    )
    parser.add_argument(
        "--local-codex-persist-session",
        action="store_true",
        help="Keep local Codex child sessions on disk instead of using --ephemeral.",
    )
    parser.add_argument(
        "--agent-command",
        help=(
            "Local agent CLI command for generic_cli or claude_code mode. The adapter passes the task prompt on stdin "
            "and supports {prompt_file}, {input_file}, {output_file}, and {repo_root} placeholders."
        ),
    )
    parser.add_argument(
        "--agent-timeout-seconds",
        type=int,
        default=generic_executor.DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for one generic local agent CLI prompt call.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    flow_id = args.flow_id or f"room-debate-e2e-{uuid.uuid4().hex[:8]}"
    flow_dir = state_root / flow_id
    room_state_root = flow_dir / "rooms"
    debate_state_root = flow_dir / "debates"
    room_id = f"{flow_id}-room"
    debate_id = f"{flow_id}-debate"

    room_args = argparse.Namespace(
        executor=args.executor,
        env_file=args.room_env_file,
        fixtures_dir=args.room_fixtures_dir,
        state_root=str(room_state_root),
        room_id=room_id,
        topic=args.topic,
        follow_up_input=args.follow_up_input,
        temperature=args.temperature,
        local_codex_preset=args.local_codex_preset,
        local_codex_model=args.local_codex_model,
        local_codex_fallback_models=args.local_codex_fallback_models,
        local_codex_profile=args.local_codex_profile,
        local_codex_reasoning_effort=args.local_codex_reasoning_effort,
        local_codex_sandbox=args.local_codex_sandbox,
        local_codex_timeout_seconds=args.local_codex_timeout_seconds,
        local_codex_timeout_retries=args.local_codex_timeout_retries,
        local_codex_retry_timeout_multiplier=args.local_codex_retry_timeout_multiplier,
        local_codex_persist_session=args.local_codex_persist_session,
        agent_command=args.agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
    )
    room_report = room_validation.run_validation(room_args)
    handoff_packet = room_report["artifacts"]["handoff_packet"]

    debate_args = argparse.Namespace(
        executor=args.executor,
        scenario=args.scenario,
        env_file=args.debate_env_file,
        fixtures_dir=args.debate_fixtures_dir,
        state_root=str(debate_state_root),
        debate_id=debate_id,
        temperature=args.temperature,
        packet_json=handoff_packet,
        local_codex_preset=args.local_codex_preset,
        local_codex_model=args.local_codex_model,
        local_codex_fallback_models=args.local_codex_fallback_models,
        local_codex_profile=args.local_codex_profile,
        local_codex_reasoning_effort=args.local_codex_reasoning_effort,
        local_codex_sandbox=args.local_codex_sandbox,
        local_codex_timeout_seconds=args.local_codex_timeout_seconds,
        local_codex_timeout_retries=args.local_codex_timeout_retries,
        local_codex_retry_timeout_multiplier=args.local_codex_retry_timeout_multiplier,
        local_codex_persist_session=args.local_codex_persist_session,
        agent_command=args.agent_command,
        agent_timeout_seconds=args.agent_timeout_seconds,
    )
    debate_report = debate_validation.run_validation(debate_args)

    flow_dir.mkdir(parents=True, exist_ok=True)
    integration_report = {
        "ok": True,
        "action": "room-debate-e2e-validation",
        "executor": args.executor,
        "flow_id": flow_id,
        "topic": room_report["topic"],
        "follow_up_input": room_report["follow_up_input"],
        "scenario": args.scenario,
        "room_id": room_report["room_id"],
        "debate_id": debate_report["debate_id"],
        "artifacts": {
            "flow_dir": str(flow_dir),
            "integration_report": str(flow_dir / "integration-report.json"),
            "room_validation_report": str(Path(room_report["artifacts"]["room_dir"]) / "validation-report.json"),
            "debate_validation_report": str(Path(debate_report["artifacts"]["debate_dir"]) / "validation-report.json"),
            "handoff_packet": handoff_packet,
            "room_dir": room_report["artifacts"]["room_dir"],
            "debate_dir": debate_report["artifacts"]["debate_dir"],
        },
        "room": {
            "provider_config": room_report["provider_config"],
            "pass_criteria": room_report["pass_criteria"],
            "upgrade_signal": room_report["upgrade_signal"],
        },
        "debate": {
            "provider_config": debate_report["provider_config"],
            "source_packet": debate_report["source_packet"],
            "launch_summary": debate_report["launch_summary"],
            "pass_criteria": debate_report["pass_criteria"],
        },
        "pass_criteria": {
            "room_flow_passed": all(bool(value) for value in room_report["pass_criteria"].values()),
            "handoff_packet_forwarded": debate_report["source_packet"]["packet_json"] == handoff_packet,
            "debate_flow_passed": debate_validation.debate_report_passed(debate_report),
        },
    }
    integration_report["pass_criteria"]["full_chain_passed"] = all(
        bool(value) for value in integration_report["pass_criteria"].values()
    )

    write_json(flow_dir / "integration-report.json", integration_report)
    return integration_report


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
