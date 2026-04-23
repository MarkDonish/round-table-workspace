#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
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

    suite_started_at = utc_now_iso()
    suite_started_monotonic = time.monotonic()
    stage_timings: dict[str, dict[str, Any]] = {}

    host_preflight = run_timed_stage(
        stage_timings,
        "host_preflight",
        lambda: local_executor.check_local_host_preflight(
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
        ),
    )
    smoke_result = host_preflight["smoke"]
    write_json(regression_dir / "host-preflight.json", host_preflight)
    if not host_preflight.get("ready"):
        raise LocalCodexRegressionError(
            f"Local Codex host preflight failed before regression execution. See {regression_dir / 'host-preflight.json'}"
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
    room_report = run_timed_stage(stage_timings, "room", lambda: room_validation.run_validation(room_args))

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
    debate_allow_report = run_timed_stage(
        stage_timings,
        "debate_allow",
        lambda: debate_validation.run_validation(debate_allow_args),
    )

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
    debate_followup_report = run_timed_stage(
        stage_timings,
        "debate_followup",
        lambda: debate_validation.run_validation(debate_followup_args),
    )

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
    integration_report = run_timed_stage(
        stage_timings,
        "integration",
        lambda: integration_validation.run_validation(integration_args),
    )

    suite_finished_at = utc_now_iso()
    suite_wall_time_seconds = round(max(time.monotonic() - suite_started_monotonic, 0.0), 3)
    runtime_profile = build_runtime_profile(
        regression_dir=regression_dir,
        stage_timings=stage_timings,
        suite_started_at=suite_started_at,
        suite_finished_at=suite_finished_at,
        suite_wall_time_seconds=suite_wall_time_seconds,
    )
    write_json(regression_dir / "runtime-profile.json", runtime_profile)

    report = {
        "ok": True,
        "action": "local-codex-regression",
        "run_id": run_id,
        "started_at": suite_started_at,
        "finished_at": suite_finished_at,
        "wall_time_seconds": suite_wall_time_seconds,
        "provider_config": {
            "mode": "local_codex",
            **settings,
        },
        "artifacts": {
            "regression_dir": str(regression_dir),
            "regression_report": str(regression_dir / "local-codex-regression-report.json"),
            "runtime_profile": str(regression_dir / "runtime-profile.json"),
            "host_preflight_report": str(regression_dir / "host-preflight.json"),
            "room_validation_report": str(Path(room_report["artifacts"]["room_dir"]) / "validation-report.json"),
            "debate_allow_validation_report": str(Path(debate_allow_report["artifacts"]["debate_dir"]) / "validation-report.json"),
            "debate_followup_validation_report": str(Path(debate_followup_report["artifacts"]["debate_dir"]) / "validation-report.json"),
            "integration_report": integration_report["artifacts"]["integration_report"],
        },
        "timings": stage_timings,
        "runtime_profile": {
            "suite_wall_time_seconds": runtime_profile["suite"]["wall_time_seconds"],
            "slowest_stage": runtime_profile["summary"]["slowest_stage"],
            "slowest_policy_key": runtime_profile["summary"]["slowest_policy_key"],
            "timed_child_traces": runtime_profile["child_traces"]["timed_traces"],
        },
        "checks": {
            "host_preflight": host_preflight,
            "smoke": smoke_result,
            "room": room_report,
            "debate_allow": debate_allow_report,
            "debate_reject_followup": debate_followup_report,
            "integration": integration_report,
        },
        "pass_criteria": {
            "host_preflight_ready": bool(host_preflight.get("ready")),
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


def run_timed_stage(
    timings: dict[str, dict[str, Any]],
    stage_name: str,
    runner: Any,
) -> Any:
    started_at = utc_now_iso()
    started_monotonic = time.monotonic()
    result = runner()
    timings[stage_name] = {
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "wall_time_seconds": round(max(time.monotonic() - started_monotonic, 0.0), 3),
    }
    return result


def build_runtime_profile(
    *,
    regression_dir: Path,
    stage_timings: dict[str, dict[str, Any]],
    suite_started_at: str,
    suite_finished_at: str,
    suite_wall_time_seconds: float,
) -> dict[str, Any]:
    child_trace_records = collect_child_trace_records(regression_dir)
    stage_ranking = sorted_stage_timings(stage_timings)
    policy_ranking = sorted_policy_timings(child_trace_records)
    return {
        "schema_version": "v0.1",
        "mode": "local_codex_runtime_profile",
        "generated_at": utc_now_iso(),
        "regression_dir": str(regression_dir),
        "suite": {
            "started_at": suite_started_at,
            "finished_at": suite_finished_at,
            "wall_time_seconds": suite_wall_time_seconds,
        },
        "stages": stage_timings,
        "child_traces": summarize_child_traces(child_trace_records),
        "summary": {
            "slowest_stage": stage_ranking[0] if stage_ranking else None,
            "slowest_policy_key": policy_ranking[0] if policy_ranking else None,
        },
    }


def collect_child_trace_records(regression_dir: Path) -> list[dict[str, Any]]:
    suffix = local_executor.TRACE_MANIFEST_SUFFIX
    records: list[dict[str, Any]] = []
    for trace_path in sorted(regression_dir.rglob(f"*{suffix}")):
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        relative_path = trace_path.relative_to(regression_dir)
        task_strategy = payload.get("task_strategy") if isinstance(payload.get("task_strategy"), dict) else {}
        records.append(
            {
                "trace_manifest": str(trace_path),
                "relative_trace_manifest": str(relative_path),
                "scope": relative_path.parts[0] if relative_path.parts else "unknown",
                "task_policy_key": task_strategy.get("task_policy_key") or "unlabeled",
                "prompt_name": task_strategy.get("prompt_name"),
                "mode": task_strategy.get("mode"),
                "final_status": payload.get("final_status"),
                "final_model": payload.get("final_model"),
                "attempt_count": len(payload.get("attempts", [])) if isinstance(payload.get("attempts"), list) else 0,
                "wall_time_seconds": resolve_trace_wall_time(payload),
            }
        )
    return records


def summarize_child_traces(records: list[dict[str, Any]]) -> dict[str, Any]:
    timed_records = [record for record in records if record.get("wall_time_seconds") is not None]
    total_wall_time_seconds = round(
        sum(float(record["wall_time_seconds"]) for record in timed_records),
        3,
    ) if timed_records else 0.0
    completed_traces = sum(1 for record in records if record.get("final_status") == "child_task_succeeded")
    failed_traces = sum(1 for record in records if record.get("final_status") == "failed")
    return {
        "total_traces": len(records),
        "timed_traces": len(timed_records),
        "completed_traces": completed_traces,
        "failed_traces": failed_traces,
        "total_wall_time_seconds": total_wall_time_seconds,
        "average_wall_time_seconds": round(total_wall_time_seconds / len(timed_records), 3) if timed_records else None,
        "by_scope": sorted_scope_timings(records),
        "by_policy_key": sorted_policy_timings(records),
        "slowest_tasks": sorted_slowest_tasks(records),
    }


def sorted_scope_timings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = {}
    for record in records:
        duration = record.get("wall_time_seconds")
        if duration is None:
            continue
        scope = str(record.get("scope") or "unknown")
        entry = bucket.setdefault(
            scope,
            {"scope": scope, "count": 0, "total_wall_time_seconds": 0.0, "max_wall_time_seconds": 0.0},
        )
        entry["count"] += 1
        entry["total_wall_time_seconds"] += float(duration)
        entry["max_wall_time_seconds"] = max(entry["max_wall_time_seconds"], float(duration))
    ranked = []
    for entry in bucket.values():
        entry["total_wall_time_seconds"] = round(entry["total_wall_time_seconds"], 3)
        entry["average_wall_time_seconds"] = round(entry["total_wall_time_seconds"] / entry["count"], 3)
        entry["max_wall_time_seconds"] = round(entry["max_wall_time_seconds"], 3)
        ranked.append(entry)
    ranked.sort(key=lambda item: item["total_wall_time_seconds"], reverse=True)
    return ranked


def sorted_policy_timings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = {}
    for record in records:
        duration = record.get("wall_time_seconds")
        if duration is None:
            continue
        policy_key = str(record.get("task_policy_key") or "unlabeled")
        entry = bucket.setdefault(
            policy_key,
            {"task_policy_key": policy_key, "count": 0, "total_wall_time_seconds": 0.0, "max_wall_time_seconds": 0.0},
        )
        entry["count"] += 1
        entry["total_wall_time_seconds"] += float(duration)
        entry["max_wall_time_seconds"] = max(entry["max_wall_time_seconds"], float(duration))
    ranked = []
    for entry in bucket.values():
        entry["total_wall_time_seconds"] = round(entry["total_wall_time_seconds"], 3)
        entry["average_wall_time_seconds"] = round(entry["total_wall_time_seconds"] / entry["count"], 3)
        entry["max_wall_time_seconds"] = round(entry["max_wall_time_seconds"], 3)
        ranked.append(entry)
    ranked.sort(key=lambda item: item["total_wall_time_seconds"], reverse=True)
    return ranked


def sorted_stage_timings(stage_timings: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for stage_name, timing in stage_timings.items():
        ranked.append({"stage": stage_name, **timing})
    ranked.sort(key=lambda item: item.get("wall_time_seconds", 0.0), reverse=True)
    return ranked


def sorted_slowest_tasks(records: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    timed_records = [record for record in records if record.get("wall_time_seconds") is not None]
    ranked = sorted(timed_records, key=lambda item: float(item["wall_time_seconds"]), reverse=True)
    return ranked[:limit]


def resolve_trace_wall_time(payload: dict[str, Any]) -> float | None:
    direct = parse_float(payload.get("wall_time_seconds"))
    if direct is not None:
        return round(direct, 3)
    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        return None
    durations = [parse_float(item.get("duration_seconds")) for item in attempts if isinstance(item, dict)]
    timed_durations = [value for value in durations if value is not None]
    if not timed_durations:
        return None
    return round(sum(timed_durations), 3)


def parse_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


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
