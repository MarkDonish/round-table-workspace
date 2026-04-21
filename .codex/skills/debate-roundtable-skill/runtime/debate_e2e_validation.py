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

RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
ROOM_RUNTIME_DIR = REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime"
if str(ROOM_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(ROOM_RUNTIME_DIR))

import chat_completions_executor as provider_executor
import debate_runtime as runtime


DEFAULT_FIXTURES_DIR = RUNTIME_DIR / "fixtures" / "canonical"
DEBATE_ROUNDTABLE_PROMPT = REPO_ROOT / "prompts" / "debate-roundtable.md"
DEBATE_REVIEWER_PROMPT = REPO_ROOT / "prompts" / "debate-reviewer.md"
DEBATE_FOLLOWUP_PROMPT = REPO_ROOT / "prompts" / "debate-followup.md"


class DebateE2EValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_validation(args)
    except (
        DebateE2EValidationError,
        runtime.DebateRuntimeError,
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
            "Run the checked-in /debate end-to-end validation flow through either "
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
        "--scenario",
        default="reject_followup",
        choices=["allow", "reject_followup"],
        help="Which canonical /debate path to validate.",
    )
    parser.add_argument(
        "--env-file",
        help="Explicit env file for /debate Chat Completions mode.",
    )
    parser.add_argument(
        "--packet-json",
        help=(
            "Optional /room handoff packet JSON to consume directly. "
            "When omitted, the checked-in canonical upgrade fixture is used."
        ),
    )
    parser.add_argument(
        "--fixtures-dir",
        default=str(DEFAULT_FIXTURES_DIR),
        help="Fixture directory for fixture mode.",
    )
    parser.add_argument(
        "--state-root",
        default=str(runtime.DEFAULT_STATE_ROOT),
        help="Directory for persisted debate runtime artifacts.",
    )
    parser.add_argument(
        "--debate-id",
        help="Optional stable debate id. Defaults to a generated validation id.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for Chat Completions mode.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    launch_bundle, packet_source = resolve_launch_bundle(args)
    debate_id = launch_bundle["debate_id"]
    room_id = launch_bundle["source_room_id"]
    debate_dir = runtime.get_debate_dir(state_root, debate_id)
    runtime.ensure_directory(debate_dir)

    runtime.ensure_directory(debate_dir / "launch")
    runtime.write_json(debate_dir / "launch" / "launch-bundle.json", launch_bundle)

    executor = build_prompt_executor(args, debate_id=debate_id, room_id=room_id)

    roundtable_input = build_roundtable_input(launch_bundle=launch_bundle, scenario=args.scenario)
    roundtable_record = execute_prompt(
        executor=executor,
        debate_dir=debate_dir,
        prompt_path=DEBATE_ROUNDTABLE_PROMPT,
        step_index=1,
        step_name="roundtable",
        prompt_input=roundtable_input,
    )
    roundtable_validation = runtime.validate_roundtable_record(roundtable_record, launch_bundle)
    runtime.ensure_directory(debate_dir / "roundtable")
    runtime.write_json(debate_dir / "roundtable" / "roundtable-record.json", roundtable_record)
    runtime.write_json(debate_dir / "roundtable" / "roundtable.validation.json", roundtable_validation)

    review_packet = runtime.build_review_packet(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        source_launch_bundle="e2e_validation",
    )
    review_packet_validation = runtime.validate_review_packet(review_packet)
    runtime.ensure_directory(debate_dir / "review")
    runtime.write_json(debate_dir / "review" / "review-packet.json", review_packet)
    runtime.write_json(debate_dir / "review" / "review-packet.validation.json", review_packet_validation)

    initial_review_input = build_reviewer_input(
        debate_id=launch_bundle["debate_id"],
        source_room_id=launch_bundle["source_room_id"],
        review_packet=review_packet,
        scenario=args.scenario,
        followup_round=0,
    )
    initial_review_result = execute_prompt(
        executor=executor,
        debate_dir=debate_dir,
        prompt_path=DEBATE_REVIEWER_PROMPT,
        step_index=2,
        step_name="reviewer.initial",
        prompt_input=initial_review_input,
    )
    initial_review_validation = runtime.validate_review_result(initial_review_result, review_packet)

    report: dict[str, Any] = {
        "ok": True,
        "action": "debate-e2e-validation",
        "scenario": args.scenario,
        "executor": args.executor,
        "debate_id": debate_id,
        "source_room_id": room_id,
        "source_packet": packet_source,
        "provider_config": describe_executor(args),
        "prompt_call_dir": str(debate_dir / "prompt-calls"),
        "artifacts": {
            "debate_dir": str(debate_dir),
            "launch_bundle": str(debate_dir / "launch" / "launch-bundle.json"),
            "roundtable_record": str(debate_dir / "roundtable" / "roundtable-record.json"),
            "roundtable_validation": str(debate_dir / "roundtable" / "roundtable.validation.json"),
            "review_packet": str(debate_dir / "review" / "review-packet.json"),
            "review_packet_validation": str(debate_dir / "review" / "review-packet.validation.json"),
        },
        "launch_summary": {
            "selected_agents": launch_bundle["candidate_pool"]["final_agents"],
            "speaker_order": launch_bundle["speaker_order"],
            "actual_overlap": launch_bundle["candidate_pool"]["actual_overlap"],
            "minimum_overlap_target": launch_bundle["candidate_pool"]["minimum_overlap_target"],
            "balance_after_reselection": launch_bundle["candidate_pool"]["balance_after_reselection"],
        },
        "roundtable_validation": roundtable_validation,
        "review_packet_validation": review_packet_validation,
        "initial_review_validation": initial_review_validation,
    }

    if args.scenario == "allow":
        runtime.write_json(debate_dir / "review" / "review-result.json", initial_review_result)
        runtime.write_json(debate_dir / "review" / "review-result.validation.json", initial_review_validation)
        report["artifacts"]["review_result"] = str(debate_dir / "review" / "review-result.json")
        report["pass_criteria"] = {
            "launch_bundle_persisted": bool((debate_dir / "launch" / "launch-bundle.json").exists()),
            "roundtable_record_accepted": roundtable_validation["accepted"],
            "review_packet_accepted": review_packet_validation["accepted"],
            "initial_review_accepted": initial_review_validation["accepted"],
            "allow_final_decision": initial_review_result["allow_final_decision"],
        }
        runtime.write_json(debate_dir / "validation-report.json", report)
        return report

    require_reject(initial_review_result)
    runtime.write_json(debate_dir / "review" / "review-result.reject.json", initial_review_result)
    runtime.write_json(debate_dir / "review" / "review-result.reject.validation.json", initial_review_validation)

    followup_input = build_followup_input(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        review_packet=review_packet,
        review_result=initial_review_result,
        scenario=args.scenario,
    )
    followup_record = execute_prompt(
        executor=executor,
        debate_dir=debate_dir,
        prompt_path=DEBATE_FOLLOWUP_PROMPT,
        step_index=3,
        step_name="followup",
        prompt_input=followup_input,
    )
    followup_validation = runtime.validate_followup_record(followup_record, initial_review_result, review_packet)
    runtime.ensure_directory(debate_dir / "followup")
    runtime.write_json(debate_dir / "followup" / "followup-record.json", followup_record)
    runtime.write_json(debate_dir / "followup" / "followup.validation.json", followup_validation)

    rereview_packet = runtime.build_rereview_packet(
        review_packet=review_packet,
        review_result=initial_review_result,
        followup_record=followup_record,
    )
    rereview_packet_validation = runtime.validate_review_packet(rereview_packet)
    runtime.write_json(debate_dir / "followup" / "rereview-packet.json", rereview_packet)
    runtime.write_json(debate_dir / "followup" / "rereview-packet.validation.json", rereview_packet_validation)

    final_review_input = build_reviewer_input(
        debate_id=launch_bundle["debate_id"],
        source_room_id=launch_bundle["source_room_id"],
        review_packet=rereview_packet,
        scenario=args.scenario,
        followup_round=1,
    )
    final_review_result = execute_prompt(
        executor=executor,
        debate_dir=debate_dir,
        prompt_path=DEBATE_REVIEWER_PROMPT,
        step_index=4,
        step_name="reviewer.rereview",
        prompt_input=final_review_input,
    )
    final_review_validation = runtime.validate_review_result(final_review_result, rereview_packet)
    runtime.write_json(debate_dir / "followup" / "review-result.allow.json", final_review_result)
    runtime.write_json(debate_dir / "followup" / "review-result.allow.validation.json", final_review_validation)

    report["artifacts"].update(
        {
            "reject_review_result": str(debate_dir / "review" / "review-result.reject.json"),
            "reject_review_result_validation": str(debate_dir / "review" / "review-result.reject.validation.json"),
            "followup_record": str(debate_dir / "followup" / "followup-record.json"),
            "followup_validation": str(debate_dir / "followup" / "followup.validation.json"),
            "rereview_packet": str(debate_dir / "followup" / "rereview-packet.json"),
            "rereview_packet_validation": str(debate_dir / "followup" / "rereview-packet.validation.json"),
            "final_review_result": str(debate_dir / "followup" / "review-result.allow.json"),
            "final_review_result_validation": str(debate_dir / "followup" / "review-result.allow.validation.json"),
        }
    )
    report["followup_validation"] = followup_validation
    report["rereview_packet_validation"] = rereview_packet_validation
    report["final_review_validation"] = final_review_validation
    report["pass_criteria"] = {
        "launch_bundle_persisted": bool((debate_dir / "launch" / "launch-bundle.json").exists()),
        "roundtable_record_accepted": roundtable_validation["accepted"],
        "review_packet_accepted": review_packet_validation["accepted"],
        "initial_reject_accepted": initial_review_validation["accepted"],
        "initial_reject_required_followups": len(initial_review_result["required_followups"]) >= 1,
        "followup_record_accepted": followup_validation["accepted"],
        "rereview_packet_accepted": rereview_packet_validation["accepted"],
        "final_review_accepted": final_review_validation["accepted"],
        "allow_final_decision_after_followup": final_review_result["allow_final_decision"],
    }
    runtime.write_json(debate_dir / "validation-report.json", report)
    return report


def resolve_launch_bundle(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.packet_json:
        packet_path = Path(args.packet_json).expanduser().resolve()
        launch_bundle, packet_acceptance = build_launch_bundle_from_packet(
            packet_path=packet_path,
            debate_id=args.debate_id,
        )
        return launch_bundle, {
            "mode": "packet_json",
            "packet_json": str(packet_path),
            "packet_acceptance": packet_acceptance,
        }

    debate_id = args.debate_id or f"debate-e2e-{uuid.uuid4().hex[:8]}"
    room_id = f"room-{debate_id}"
    launch_bundle, packet_acceptance = build_canonical_launch_bundle(debate_id=debate_id, room_id=room_id)
    return launch_bundle, {
        "mode": "canonical_fixture",
        "packet_json": str(runtime.ROOM_UPGRADE_FIXTURE),
        "packet_acceptance": packet_acceptance,
    }


def build_canonical_launch_bundle(*, debate_id: str, room_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture_payload = runtime.materialize_placeholders(runtime.load_json(runtime.ROOM_UPGRADE_FIXTURE), {"__ROOM_ID__": room_id})
    packet = runtime.unwrap_packet(fixture_payload)
    packet_acceptance = runtime.validate_packet_payload(fixture_payload)
    registry = runtime.packet_validator.load_registry()
    launch_bundle = runtime.build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=debate_id,
        source_packet_path=str(runtime.ROOM_UPGRADE_FIXTURE),
    )
    return launch_bundle, packet_acceptance


def build_launch_bundle_from_packet(*, packet_path: Path, debate_id: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = runtime.load_json(packet_path)
    packet = runtime.unwrap_packet(payload)
    packet_acceptance = runtime.validate_packet_payload(payload)
    registry = runtime.packet_validator.load_registry()
    resolved_debate_id = debate_id or runtime.derive_debate_id(packet["source_room_id"])
    launch_bundle = runtime.build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=resolved_debate_id,
        source_packet_path=str(packet_path),
    )
    return launch_bundle, packet_acceptance


def build_prompt_executor(args: argparse.Namespace, *, debate_id: str, room_id: str):
    if args.executor == "fixture":
        fixtures_dir = Path(args.fixtures_dir).expanduser().resolve()

        def execute(prompt_path: Path, prompt_input: dict[str, Any]) -> dict[str, Any]:
            return load_fixture_output(
                fixtures_dir=fixtures_dir,
                debate_id=debate_id,
                room_id=room_id,
                prompt_path=prompt_path,
                prompt_input=prompt_input,
            )

        return execute

    env = dict(os.environ)
    if args.env_file:
        env.update(provider_executor.load_env_file(Path(args.env_file)))
    config = provider_executor.read_provider_config(env, provider_scope="debate")

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
    config = provider_executor.read_provider_config(env, provider_scope="debate")
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
    debate_dir: Path,
    prompt_path: Path,
    step_index: int,
    step_name: str,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    output = executor(prompt_path, prompt_input)
    persist_prompt_call(
        debate_dir=debate_dir,
        step_index=step_index,
        step_name=step_name,
        prompt_path=prompt_path,
        prompt_input=prompt_input,
        prompt_output=output,
    )
    return output


def persist_prompt_call(
    *,
    debate_dir: Path,
    step_index: int,
    step_name: str,
    prompt_path: Path,
    prompt_input: dict[str, Any],
    prompt_output: dict[str, Any],
) -> None:
    call_dir = debate_dir / "prompt-calls"
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


def build_roundtable_input(*, launch_bundle: dict[str, Any], scenario: str) -> dict[str, Any]:
    return {
        "mode": "debate_roundtable",
        "scenario": scenario,
        "debate_id": launch_bundle["debate_id"],
        "source_room_id": launch_bundle["source_room_id"],
        "topic": launch_bundle["topic"],
        "room_title": launch_bundle["room_title"],
        "primary_type": launch_bundle["primary_type"],
        "secondary_type": launch_bundle.get("secondary_type"),
        "participants": launch_bundle["participants"],
        "moderator": launch_bundle["moderator"],
        "speaker_order": launch_bundle["speaker_order"],
        "packet_materials": launch_bundle["packet_materials"],
        "prompt_inputs": launch_bundle["prompt_inputs"]["roundtable"],
    }


def build_reviewer_input(
    *,
    debate_id: str,
    source_room_id: str,
    review_packet: dict[str, Any],
    scenario: str,
    followup_round: int,
) -> dict[str, Any]:
    return {
        "mode": "debate_review",
        "debate_id": debate_id,
        "source_room_id": source_room_id,
        "scenario": scenario,
        "followup_round": followup_round,
        "review_packet": review_packet,
    }


def build_followup_input(
    *,
    launch_bundle: dict[str, Any],
    roundtable_record: dict[str, Any],
    review_packet: dict[str, Any],
    review_result: dict[str, Any],
    scenario: str,
) -> dict[str, Any]:
    return {
        "mode": "debate_followup",
        "scenario": scenario,
        "debate_id": launch_bundle["debate_id"],
        "source_room_id": launch_bundle["source_room_id"],
        "participants": launch_bundle["participants"],
        "moderator": launch_bundle["moderator"],
        "review_packet": review_packet,
        "review_result": review_result,
        "roundtable_record": roundtable_record,
        "prompt_inputs": launch_bundle["prompt_inputs"]["followup"],
    }


def load_fixture_output(
    *,
    fixtures_dir: Path,
    debate_id: str,
    room_id: str,
    prompt_path: Path,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    if prompt_path == DEBATE_ROUNDTABLE_PROMPT:
        fixture_name = "roundtable_record.json"
    elif prompt_path == DEBATE_REVIEWER_PROMPT:
        if prompt_input.get("followup_round") == 1:
            fixture_name = "followup_review_result_allow.json"
        elif prompt_input.get("scenario") == "allow":
            fixture_name = "review_result.json"
        else:
            fixture_name = "followup_review_result_reject.json"
    elif prompt_path == DEBATE_FOLLOWUP_PROMPT:
        fixture_name = "followup_record.json"
    else:
        raise DebateE2EValidationError(f"unsupported prompt in fixture mode: {prompt_path}")

    payload = runtime.load_json(fixtures_dir / fixture_name)
    return runtime.materialize_placeholders(
        payload,
        {
            "__ROOM_ID__": room_id,
            "__DEBATE_ID__": debate_id,
        },
    )


def require_reject(review_result: dict[str, Any]) -> None:
    if review_result.get("allow_final_decision") is not False:
        raise DebateE2EValidationError("reject_followup scenario requires the initial reviewer result to reject.")


if __name__ == "__main__":
    sys.exit(main())
