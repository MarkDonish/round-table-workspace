#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import local_codex_executor as local_executor
import room_e2e_validation as room_validation
import room_debate_e2e_validation as integration_validation


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEBATE_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "debate-roundtable-skill" / "runtime"
if str(DEBATE_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(DEBATE_RUNTIME_DIR))

import debate_e2e_validation as debate_validation


DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "local-codex-regression"
DEFAULT_LOCAL_CODEX_PRESET = "gpt54_family"
DEFAULT_REGRESSION_FOLLOW_UP = (
    "/focus 先只盯最小可验证切口，并明确争论：首轮验证到底该优先看同型变体题完成率，还是优先看无提示复述与迁移能力？"
)


class LocalCodexRegressionError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_regression(args)
    except (
        LocalCodexRegressionError,
        local_executor.LocalCodexExecutorError,
        room_validation.RoomE2EValidationError,
        debate_validation.DebateE2EValidationError,
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
            "Run the checked-in local Codex regression suite for /room and /debate, "
            "including smoke, room E2E, debate allow, debate reject-followup, and full integration."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted regression evidence.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional stable regression run id.",
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
        "--topic",
        default=room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for the regression suite.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=DEFAULT_REGRESSION_FOLLOW_UP,
        help="Follow-up /room input for the regression suite.",
    )
    return parser


def run_regression(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"local-codex-regression-{uuid.uuid4().hex[:8]}"
    regression_dir = state_root / run_id
    regression_dir.mkdir(parents=True, exist_ok=True)
    settings = resolve_local_codex_settings(args)

    smoke_result = local_executor.check_local_exec(
        repo_root=REPO_ROOT,
        model=settings["model"],
        fallback_models=settings["fallback_models"],
        profile=settings["profile"],
        reasoning_effort=settings["reasoning_effort"],
        sandbox=settings["sandbox"],
        timeout_seconds=settings["timeout_seconds"],
        timeout_retries=settings["timeout_retries"],
        retry_timeout_multiplier=settings["retry_timeout_multiplier"],
        ephemeral=settings["ephemeral"],
        preset_name=settings["preset"],
    )

    room_args = argparse.Namespace(
        executor="local_codex",
        env_file=None,
        fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(regression_dir / "room"),
        room_id=None,
        topic=args.topic,
        follow_up_input=args.follow_up_input,
        temperature=0.1,
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
    )
    room_report = room_validation.run_validation(room_args)

    debate_allow_args = argparse.Namespace(
        executor="local_codex",
        scenario="allow",
        env_file=None,
        packet_json=None,
        fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(regression_dir / "debate-allow"),
        debate_id=None,
        temperature=0.1,
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
    )
    debate_allow_report = debate_validation.run_validation(debate_allow_args)

    debate_followup_args = argparse.Namespace(
        executor="local_codex",
        scenario="reject_followup",
        env_file=None,
        packet_json=None,
        fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(regression_dir / "debate-followup"),
        debate_id=None,
        temperature=0.1,
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
    )
    debate_followup_report = debate_validation.run_validation(debate_followup_args)

    integration_args = argparse.Namespace(
        executor="local_codex",
        room_env_file=None,
        debate_env_file=None,
        room_fixtures_dir=str(room_validation.DEFAULT_FIXTURES_DIR),
        debate_fixtures_dir=str(debate_validation.DEFAULT_FIXTURES_DIR),
        state_root=str(regression_dir / "integration"),
        flow_id=None,
        topic=args.topic,
        follow_up_input=args.follow_up_input,
        scenario="reject_followup",
        temperature=0.1,
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
    )
    integration_report = integration_validation.run_validation(integration_args)

    report = {
        "ok": True,
        "action": "local-codex-regression",
        "run_id": run_id,
        "provider_config": {
            "mode": "local_codex",
            **settings,
        },
        "artifacts": {
            "regression_dir": str(regression_dir),
            "regression_report": str(regression_dir / "local-codex-regression-report.json"),
            "room_validation_report": str(Path(room_report["artifacts"]["room_dir"]) / "validation-report.json"),
            "debate_allow_validation_report": str(Path(debate_allow_report["artifacts"]["debate_dir"]) / "validation-report.json"),
            "debate_followup_validation_report": str(Path(debate_followup_report["artifacts"]["debate_dir"]) / "validation-report.json"),
            "integration_report": integration_report["artifacts"]["integration_report"],
        },
        "checks": {
            "smoke": smoke_result,
            "room": room_report,
            "debate_allow": debate_allow_report,
            "debate_reject_followup": debate_followup_report,
            "integration": integration_report,
        },
        "pass_criteria": {
            "smoke_ready": bool(smoke_result.get("ready")),
            "room_passed": all(bool(value) for value in room_report["pass_criteria"].values()),
            "debate_allow_passed": debate_validation.debate_report_passed(debate_allow_report),
            "debate_followup_passed": debate_validation.debate_report_passed(debate_followup_report),
            "integration_passed": bool(integration_report["pass_criteria"]["full_chain_passed"]),
        },
    }
    report["pass_criteria"]["full_suite_passed"] = all(bool(value) for value in report["pass_criteria"].values())
    write_json(regression_dir / "local-codex-regression-report.json", report)
    return report


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_local_codex_settings(args: argparse.Namespace) -> dict[str, Any]:
    return local_executor.resolve_execution_settings(
        preset_name=args.local_codex_preset,
        model=args.local_codex_model,
        fallback_models=local_executor.parse_model_list(args.local_codex_fallback_models)
        if args.local_codex_fallback_models is not None
        else None,
        profile=args.local_codex_profile,
        reasoning_effort=args.local_codex_reasoning_effort,
        sandbox=args.local_codex_sandbox,
        timeout_seconds=args.local_codex_timeout_seconds,
        timeout_retries=args.local_codex_timeout_retries,
        retry_timeout_multiplier=args.local_codex_retry_timeout_multiplier,
        persist_session=args.local_codex_persist_session,
    )


if __name__ == "__main__":
    sys.exit(main())
