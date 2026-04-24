#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chat_completions_executor as provider_executor


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_ROOM_ENV_FILE = REPO_ROOT / ".env.room"
DEFAULT_DEBATE_ENV_FILE = REPO_ROOT / ".env.debate"
PROVIDER_LANE_DESCRIPTION = (
    "optional Chat Completions-compatible fallback/regression lane; "
    "not required for the Codex local mainline /room or /debate flow"
)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = build_readiness_report(args)
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict:
        return 0 if report["pass_criteria"]["ready_for_live_run"] else 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check Chat Completions-compatible provider live readiness without sending provider requests. "
            "This separates config readiness from mock regression and real live validation."
        )
    )
    parser.add_argument("--room-env-file", default=str(DEFAULT_ROOM_ENV_FILE), help="Room provider env file.")
    parser.add_argument("--debate-env-file", default=str(DEFAULT_DEBATE_ENV_FILE), help="Debate provider env file.")
    parser.add_argument("--output-json", help="Optional path to persist the readiness report.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero unless both room and debate provider configs are ready for live validation.",
    )
    return parser


def build_readiness_report(args: argparse.Namespace) -> dict[str, Any]:
    room_env_file = Path(args.room_env_file).expanduser().resolve()
    debate_env_file = Path(args.debate_env_file).expanduser().resolve()
    room = check_scope(env_file=room_env_file, provider_scope="room")
    debate = check_scope(env_file=debate_env_file, provider_scope="debate")
    ready_for_live_run = room["ready"] and debate["ready"]
    return {
        "ok": True,
        "action": "chat-completions-readiness",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "provider_lane": provider_lane_boundary(),
        "checks": {
            "room": room,
            "debate": debate,
        },
        "pass_criteria": {
            "room_provider_ready": room["ready"],
            "debate_provider_ready": debate["ready"],
            "ready_for_live_run": ready_for_live_run,
        },
        "next_action": build_next_action(ready_for_live_run=ready_for_live_run, room=room, debate=debate),
        "live_validation_command": (
            "python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py "
            "--room-env-file .env.room --debate-env-file .env.debate "
            "--state-root /tmp/round-table-chat-completions-live"
        ),
    }


def check_scope(*, env_file: Path, provider_scope: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ready": False,
        "provider_scope": provider_scope,
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "local_mainline_blocker": False,
    }
    if not env_file.exists():
        result["blocker"] = "env_file_missing"
        result["error"] = f"Env file does not exist: {env_file}"
        return result
    try:
        env = provider_executor.load_env_file(env_file)
        config = provider_executor.read_provider_config(env, provider_scope=provider_scope)
    except provider_executor.ProviderConfigError as exc:
        result["blocker"] = "provider_config_invalid"
        result["error"] = str(exc)
        return result
    result.update(
        {
            "ready": True,
            "blocker": None,
            "local_mainline_blocker": False,
            "url": provider_executor.mask_value(config["url"]),
            "model": provider_executor.mask_value(config["model"]),
            "auth_configured": bool(config.get("auth_bearer")),
            "timeout_seconds": config["timeout_seconds"],
        }
    )
    return result


def build_next_action(*, ready_for_live_run: bool, room: dict[str, Any], debate: dict[str, Any]) -> str:
    if ready_for_live_run:
        return (
            "Provider env is ready. Run the checked-in chat_completions_live_validation.py wrapper "
            "only if you intentionally want to validate the optional provider-live lane."
        )
    missing = []
    for scope, check in (("room", room), ("debate", debate)):
        if not check["ready"]:
            missing.append(f"{scope}: {check.get('blocker')} ({check.get('error')})")
    return (
        "No provider URL is required for the Codex local mainline. "
        "Fix provider env readiness only if you intentionally want optional provider-live validation. "
        "Blockers: "
        + "; ".join(missing)
    )


def provider_lane_boundary() -> dict[str, Any]:
    return {
        "description": PROVIDER_LANE_DESCRIPTION,
        "local_mainline_requires_provider_url": False,
        "local_mainline_recommended_command": (
            "python3 .codex/skills/room-skill/runtime/local_codex_regression.py "
            "--state-root /tmp/round-table-local-codex-regression"
        ),
        "provider_live_claim_requires": (
            "valid local .env.room and .env.debate files plus "
            "chat_completions_live_validation.py returning live_run_passed=true"
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
