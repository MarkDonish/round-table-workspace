#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import chat_completions_executor as provider_executor
import room_debate_e2e_validation as integration_validation
import room_e2e_validation as room_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "chat-completions-live"


class ChatCompletionsLiveValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_validation(args)
    except (
        ChatCompletionsLiveValidationError,
        provider_executor.ProviderConfigError,
        integration_validation.RoomDebateE2EValidationError,
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
            "Run the checked-in external-provider validation wrapper for /room -> /debate. "
            "It preflights both env scopes first, then launches the chat-completions integration flow."
        )
    )
    parser.add_argument(
        "--room-env-file",
        required=True,
        help="Explicit .env file for /room Chat Completions config.",
    )
    parser.add_argument(
        "--debate-env-file",
        required=True,
        help="Explicit .env file for /debate Chat Completions config.",
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted live-validation evidence.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional stable live validation run id.",
    )
    parser.add_argument(
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for the live validation flow.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=room_validation.DEFAULT_FOLLOW_UP,
        help="Follow-up /room input for the live validation flow.",
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
        help="Sampling temperature for both provider-backed prompt lanes.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only run room/debate provider preflight without launching the integration flow.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"chat-completions-live-{uuid.uuid4().hex[:8]}"
    run_dir = state_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    room_env_file = Path(args.room_env_file).expanduser().resolve()
    debate_env_file = Path(args.debate_env_file).expanduser().resolve()

    report: dict[str, Any] = {
        "ok": False,
        "action": "chat-completions-live-validation",
        "run_id": run_id,
        "artifacts": {
            "run_dir": str(run_dir),
            "live_validation_report": str(run_dir / "chat-completions-live-validation-report.json"),
            "room_env_file": str(room_env_file),
            "debate_env_file": str(debate_env_file),
        },
        "checks": {
            "room_provider_preflight": None,
            "debate_provider_preflight": None,
        },
        "pass_criteria": {
            "room_provider_ready": False,
            "debate_provider_ready": False,
        },
    }
    report_path = Path(report["artifacts"]["live_validation_report"])
    try:
        room_provider = read_provider_preflight(env_file=room_env_file, provider_scope="room")
        debate_provider = read_provider_preflight(env_file=debate_env_file, provider_scope="debate")
        report["checks"]["room_provider_preflight"] = room_provider
        report["checks"]["debate_provider_preflight"] = debate_provider
        report["pass_criteria"]["room_provider_ready"] = bool(room_provider.get("ready"))
        report["pass_criteria"]["debate_provider_ready"] = bool(debate_provider.get("ready"))

        if args.check_only:
            report["ok"] = True
            report["mode"] = "preflight_only"
            report["pass_criteria"]["preflight_only_completed"] = True
            report["pass_criteria"]["ready_for_live_run"] = all(bool(value) for value in report["pass_criteria"].values())
            write_json(report_path, report)
            return report

        integration_args = argparse.Namespace(
            executor="chat_completions",
            room_env_file=str(room_env_file),
            debate_env_file=str(debate_env_file),
            room_fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
            debate_fixtures_dir=str(integration_validation.debate_validation.DEFAULT_FIXTURES_DIR),
            state_root=str(run_dir / "integration"),
            flow_id=None,
            topic=args.topic,
            follow_up_input=args.follow_up_input,
            scenario=args.scenario,
            temperature=args.temperature,
            local_codex_preset=integration_validation.DEFAULT_LOCAL_CODEX_PRESET,
            local_codex_model=None,
            local_codex_fallback_models=None,
            local_codex_profile=None,
            local_codex_reasoning_effort=None,
            local_codex_sandbox=None,
            local_codex_timeout_seconds=None,
            local_codex_timeout_retries=None,
            local_codex_retry_timeout_multiplier=None,
            local_codex_persist_session=False,
        )
        integration_report = integration_validation.run_validation(integration_args)
        report["ok"] = True
        report["mode"] = "live_run"
        report["checks"]["integration"] = integration_report
        report["artifacts"]["integration_report"] = integration_report["artifacts"]["integration_report"]
        report["pass_criteria"]["integration_passed"] = bool(integration_report["pass_criteria"]["full_chain_passed"])
        report["pass_criteria"]["live_run_passed"] = all(bool(value) for value in report["pass_criteria"].values())
        write_json(report_path, report)
        return report
    except Exception as exc:
        report["error"] = str(exc)
        write_json(report_path, report)
        raise


def read_provider_preflight(*, env_file: Path, provider_scope: str) -> dict[str, Any]:
    env = provider_executor.load_env_file(env_file)
    config = provider_executor.read_provider_config(env, provider_scope=provider_scope)
    return {
        "ready": True,
        "provider_scope": provider_scope,
        "env_file": str(env_file),
        "url": provider_executor.mask_value(config["url"]),
        "model": provider_executor.mask_value(config["model"]),
        "auth_configured": bool(config.get("auth_bearer")),
        "timeout_seconds": config["timeout_seconds"],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
