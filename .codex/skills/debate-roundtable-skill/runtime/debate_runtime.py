#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any

import debate_packet_validator as packet_validator


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "debates"
ROOM_UPGRADE_FIXTURE = (
    REPO_ROOT / ".codex" / "skills" / "room-skill" / "runtime" / "fixtures" / "canonical" / "upgrade.json"
)
CANONICAL_REVIEW_PACKET = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "review_packet.json"
)
CANONICAL_ROUNDTABLE_RECORD = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "roundtable_record.json"
)
CANONICAL_REVIEW_RESULT = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "review_result.json"
)
CANONICAL_FOLLOWUP_REVIEW_RESULT_REJECT = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "followup_review_result_reject.json"
)
CANONICAL_FOLLOWUP_RECORD = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "followup_record.json"
)
CANONICAL_FOLLOWUP_REREVIEW_PACKET = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "followup_rereview_packet.json"
)
CANONICAL_FOLLOWUP_REVIEW_RESULT_ALLOW = (
    REPO_ROOT
    / ".codex"
    / "skills"
    / "debate-roundtable-skill"
    / "runtime"
    / "fixtures"
    / "canonical"
    / "followup_review_result_allow.json"
)

TASK_LABELS = {
    "startup": "创业方向",
    "product": "产品方案",
    "learning": "学习路径",
    "content": "内容策略",
    "risk": "风险审查",
    "planning": "阶段规划",
    "strategy": "战略判断",
    "writing": "写作任务",
}
VALID_CONFIDENCE = {"high", "medium", "low", "高", "中", "低"}


class DebateRuntimeError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "build-launch-bundle":
            result = command_build_launch_bundle(args)
        elif args.command == "validate-roundtable-record":
            result = command_validate_roundtable_record(args)
        elif args.command == "build-review-template":
            result = command_build_review_template(args)
        elif args.command == "build-review-packet":
            result = command_build_review_packet(args)
        elif args.command == "validate-review-packet":
            result = command_validate_review_packet(args)
        elif args.command == "validate-review-result":
            result = command_validate_review_result(args)
        elif args.command == "validate-followup-record":
            result = command_validate_followup_record(args)
        elif args.command == "build-rereview-packet":
            result = command_build_rereview_packet(args)
        elif args.command == "validate-canonical":
            result = command_validate_canonical(args)
        elif args.command == "validate-canonical-execution":
            result = command_validate_canonical_execution(args)
        elif args.command == "validate-canonical-followup":
            result = command_validate_canonical_followup(args)
        else:
            raise DebateRuntimeError(f"Unsupported command: {args.command}")
    except DebateRuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Checked-in /debate runtime bridge for launch bundles and reviewer packets."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch_parser = subparsers.add_parser(
        "build-launch-bundle",
        help="Consume a validated handoff packet and build the checked-in debate launch bundle.",
    )
    launch_parser.add_argument("--packet-json", required=True, help="Path to a handoff packet JSON file.")
    launch_parser.add_argument("--debate-id", help="Optional stable debate id.")
    launch_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted debate runtime artifacts.",
    )

    roundtable_parser = subparsers.add_parser(
        "validate-roundtable-record",
        help="Validate a debate roundtable record against a checked-in launch bundle.",
    )
    roundtable_parser.add_argument("--roundtable-json", required=True)
    roundtable_parser.add_argument("--launch-bundle-json", required=True)

    template_parser = subparsers.add_parser(
        "build-review-template",
        help="Build a reviewer-facing template from a debate launch bundle.",
    )
    template_parser.add_argument("--launch-bundle-json", required=True)
    template_parser.add_argument("--output-json", help="Optional explicit output path.")

    review_packet_parser = subparsers.add_parser(
        "build-review-packet",
        help="Build a reviewer packet from a validated roundtable record and launch bundle.",
    )
    review_packet_parser.add_argument("--roundtable-json", required=True)
    review_packet_parser.add_argument("--launch-bundle-json", required=True)
    review_packet_parser.add_argument("--output-json", help="Optional explicit output path.")
    review_packet_parser.add_argument(
        "--source-launch-bundle-label",
        help="Optional stable label to write into source_launch_bundle instead of the full path.",
    )

    review_parser = subparsers.add_parser(
        "validate-review-packet",
        help="Validate a reviewer packet against the checked-in reviewer protocol contract.",
    )
    review_parser.add_argument("--review-packet-json", required=True)

    review_result_parser = subparsers.add_parser(
        "validate-review-result",
        help="Validate a reviewer result against a checked-in reviewer packet.",
    )
    review_result_parser.add_argument("--review-result-json", required=True)
    review_result_parser.add_argument("--review-packet-json", required=True)

    followup_parser = subparsers.add_parser(
        "validate-followup-record",
        help="Validate a debate followup record against a rejected reviewer result.",
    )
    followup_parser.add_argument("--followup-json", required=True)
    followup_parser.add_argument("--review-result-json", required=True)
    followup_parser.add_argument("--review-packet-json", required=True)

    rereview_parser = subparsers.add_parser(
        "build-rereview-packet",
        help="Build a re-review packet from a rejected reviewer result plus a followup record.",
    )
    rereview_parser.add_argument("--followup-json", required=True)
    rereview_parser.add_argument("--review-result-json", required=True)
    rereview_parser.add_argument("--review-packet-json", required=True)
    rereview_parser.add_argument("--output-json", help="Optional explicit output path.")

    canonical_parser = subparsers.add_parser(
        "validate-canonical",
        help="Replay the checked-in canonical handoff into a debate launch bundle and reviewer packet validation.",
    )
    canonical_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted debate runtime artifacts.",
    )

    canonical_execution_parser = subparsers.add_parser(
        "validate-canonical-execution",
        help="Replay the checked-in canonical debate execution chain through roundtable and reviewer artifacts.",
    )
    canonical_execution_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted debate runtime artifacts.",
    )

    canonical_followup_parser = subparsers.add_parser(
        "validate-canonical-followup",
        help="Replay the checked-in canonical reject-followup-rereview debate chain.",
    )
    canonical_followup_parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted debate runtime artifacts.",
    )

    return parser


def command_build_launch_bundle(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    payload = load_json(Path(args.packet_json))
    packet = unwrap_packet(payload)
    packet_acceptance = validate_packet_payload(payload)
    registry = packet_validator.load_registry()
    debate_id = args.debate_id or derive_debate_id(packet["source_room_id"])
    launch_bundle = build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=debate_id,
        source_packet_path=str(Path(args.packet_json).expanduser().resolve()),
    )

    debate_dir = get_debate_dir(state_root, debate_id)
    ensure_directory(debate_dir / "launch")
    launch_path = debate_dir / "launch" / "launch-bundle.json"
    write_json(launch_path, launch_bundle)

    return {
        "ok": True,
        "action": "build-launch-bundle",
        "debate_id": debate_id,
        "launch_bundle_path": str(launch_path),
        "selected_agents": launch_bundle["candidate_pool"]["final_agents"],
        "speaker_order": launch_bundle["speaker_order"],
        "balance_after_reselection": launch_bundle["candidate_pool"]["balance_after_reselection"],
    }


def command_validate_roundtable_record(args: argparse.Namespace) -> dict[str, Any]:
    launch_bundle = load_json(Path(args.launch_bundle_json))
    validate_launch_bundle(launch_bundle)
    roundtable_record = load_json(Path(args.roundtable_json))
    validation = validate_roundtable_record(roundtable_record, launch_bundle)
    return {
        "ok": True,
        "action": "validate-roundtable-record",
        "validation": validation,
    }


def command_build_review_template(args: argparse.Namespace) -> dict[str, Any]:
    launch_bundle_path = Path(args.launch_bundle_json).expanduser().resolve()
    launch_bundle = load_json(launch_bundle_path)
    validate_launch_bundle(launch_bundle)
    template = build_review_template(launch_bundle, source_launch_bundle=str(launch_bundle_path))

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
    else:
        output_path = launch_bundle_path.parent.parent / "review" / "review-template.json"
    ensure_directory(output_path.parent)
    write_json(output_path, template)

    return {
        "ok": True,
        "action": "build-review-template",
        "review_template_path": str(output_path),
        "participant_count": len(template["participants"]),
        "quick_mode": template["quick_mode"],
    }


def command_build_review_packet(args: argparse.Namespace) -> dict[str, Any]:
    launch_bundle_path = Path(args.launch_bundle_json).expanduser().resolve()
    launch_bundle = load_json(launch_bundle_path)
    validate_launch_bundle(launch_bundle)

    roundtable_path = Path(args.roundtable_json).expanduser().resolve()
    roundtable_record = load_json(roundtable_path)
    roundtable_validation = validate_roundtable_record(roundtable_record, launch_bundle)

    source_label = args.source_launch_bundle_label or str(launch_bundle_path)
    review_packet = build_review_packet(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        source_launch_bundle=source_label,
    )
    review_packet_validation = validate_review_packet(review_packet)

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
    else:
        output_path = launch_bundle_path.parent.parent / "review" / "review-packet.json"
    ensure_directory(output_path.parent)
    write_json(output_path, review_packet)

    return {
        "ok": True,
        "action": "build-review-packet",
        "review_packet_path": str(output_path),
        "roundtable_validation": roundtable_validation,
        "review_packet_validation": review_packet_validation,
    }


def command_validate_review_packet(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_json(Path(args.review_packet_json))
    result = validate_review_packet(payload)
    return {"ok": True, "action": "validate-review-packet", "validation": result}


def command_validate_review_result(args: argparse.Namespace) -> dict[str, Any]:
    review_packet = load_json(Path(args.review_packet_json))
    validate_review_packet(review_packet)
    review_result = load_json(Path(args.review_result_json))
    validation = validate_review_result(review_result, review_packet)
    return {"ok": True, "action": "validate-review-result", "validation": validation}


def command_validate_followup_record(args: argparse.Namespace) -> dict[str, Any]:
    review_packet = load_json(Path(args.review_packet_json))
    validate_review_packet(review_packet)

    review_result = load_json(Path(args.review_result_json))
    review_result_validation = validate_review_result(review_result, review_packet)
    require(review_result["allow_final_decision"] is False, "followup record only applies to rejected reviewer results.")

    followup_record = load_json(Path(args.followup_json))
    followup_validation = validate_followup_record(followup_record, review_result, review_packet)
    return {
        "ok": True,
        "action": "validate-followup-record",
        "review_result_validation": review_result_validation,
        "validation": followup_validation,
    }


def command_build_rereview_packet(args: argparse.Namespace) -> dict[str, Any]:
    review_packet_path = Path(args.review_packet_json).expanduser().resolve()
    review_packet = load_json(review_packet_path)
    validate_review_packet(review_packet)

    review_result = load_json(Path(args.review_result_json))
    review_result_validation = validate_review_result(review_result, review_packet)
    require(review_result["allow_final_decision"] is False, "re-review packet only applies to rejected reviewer results.")

    followup_record = load_json(Path(args.followup_json))
    followup_validation = validate_followup_record(followup_record, review_result, review_packet)
    rereview_packet = build_rereview_packet(
        review_packet=review_packet,
        review_result=review_result,
        followup_record=followup_record,
    )
    rereview_packet_validation = validate_review_packet(rereview_packet)

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
    else:
        output_path = review_packet_path.parent.parent / "followup" / "rereview-packet.json"
    ensure_directory(output_path.parent)
    write_json(output_path, rereview_packet)

    return {
        "ok": True,
        "action": "build-rereview-packet",
        "rereview_packet_path": str(output_path),
        "review_result_validation": review_result_validation,
        "followup_validation": followup_validation,
        "rereview_packet_validation": rereview_packet_validation,
    }


def command_validate_canonical(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    debate_id = "debate-canonical-bridge"
    room_id = "room-canonical-debate"

    fixture_payload = materialize_placeholders(load_json(ROOM_UPGRADE_FIXTURE), {"__ROOM_ID__": room_id})
    packet = unwrap_packet(fixture_payload)
    packet_acceptance = validate_packet_payload(fixture_payload)
    registry = packet_validator.load_registry()
    launch_bundle = build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=debate_id,
        source_packet_path=str(ROOM_UPGRADE_FIXTURE),
    )

    review_packet = materialize_placeholders(load_json(CANONICAL_REVIEW_PACKET), {"__ROOM_ID__": room_id})
    review_validation = validate_review_packet(review_packet)

    debate_dir = get_debate_dir(state_root, debate_id)
    ensure_directory(debate_dir / "launch")
    ensure_directory(debate_dir / "review")
    write_json(debate_dir / "launch" / "launch-bundle.json", launch_bundle)
    write_json(debate_dir / "review" / "canonical-review-packet.json", review_packet)
    write_json(debate_dir / "review" / "review-packet.validation.json", review_validation)

    report = {
        "ok": True,
        "action": "validate-canonical",
        "debate_id": debate_id,
        "source_room_id": room_id,
        "artifacts": {
            "debate_dir": str(debate_dir),
            "launch_bundle": str(debate_dir / "launch" / "launch-bundle.json"),
            "review_packet": str(debate_dir / "review" / "canonical-review-packet.json"),
            "review_validation": str(debate_dir / "review" / "review-packet.validation.json"),
        },
        "launch_summary": {
            "selected_agents": launch_bundle["candidate_pool"]["final_agents"],
            "speaker_order": launch_bundle["speaker_order"],
            "actual_overlap": launch_bundle["candidate_pool"]["actual_overlap"],
            "minimum_overlap_target": launch_bundle["candidate_pool"]["minimum_overlap_target"],
            "balance_after_reselection": launch_bundle["candidate_pool"]["balance_after_reselection"],
        },
        "review_validation": review_validation,
        "pass_criteria": {
            "launch_bundle_persisted": bool((debate_dir / "launch" / "launch-bundle.json").exists()),
            "minimum_overlap_respected": (
                launch_bundle["candidate_pool"]["actual_overlap"]
                >= launch_bundle["candidate_pool"]["minimum_overlap_target"]
            ),
            "selection_balanced": launch_bundle["candidate_pool"]["balance_after_reselection"]["passes_debate_balance"],
            "review_packet_accepted": review_validation["accepted"],
        },
    }
    write_json(debate_dir / "validation-report.json", report)
    return report


def command_validate_canonical_execution(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    debate_id = "debate-canonical-execution"
    room_id = "room-canonical-debate"

    fixture_payload = materialize_placeholders(load_json(ROOM_UPGRADE_FIXTURE), {"__ROOM_ID__": room_id})
    packet = unwrap_packet(fixture_payload)
    packet_acceptance = validate_packet_payload(fixture_payload)
    registry = packet_validator.load_registry()
    launch_bundle = build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=debate_id,
        source_packet_path=str(ROOM_UPGRADE_FIXTURE),
    )

    roundtable_record = materialize_placeholders(
        load_json(CANONICAL_ROUNDTABLE_RECORD),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    roundtable_validation = validate_roundtable_record(roundtable_record, launch_bundle)

    review_packet = build_review_packet(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        source_launch_bundle="canonical",
    )
    review_packet_validation = validate_review_packet(review_packet)
    expected_review_packet = materialize_placeholders(load_json(CANONICAL_REVIEW_PACKET), {"__ROOM_ID__": room_id})
    require(review_packet == expected_review_packet, "canonical built review packet no longer matches fixture.")

    review_result = materialize_placeholders(
        load_json(CANONICAL_REVIEW_RESULT),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    review_result_validation = validate_review_result(review_result, review_packet)

    debate_dir = get_debate_dir(state_root, debate_id)
    ensure_directory(debate_dir / "launch")
    ensure_directory(debate_dir / "roundtable")
    ensure_directory(debate_dir / "review")
    write_json(debate_dir / "launch" / "launch-bundle.json", launch_bundle)
    write_json(debate_dir / "roundtable" / "roundtable-record.json", roundtable_record)
    write_json(debate_dir / "roundtable" / "roundtable.validation.json", roundtable_validation)
    write_json(debate_dir / "review" / "review-packet.json", review_packet)
    write_json(debate_dir / "review" / "review-packet.validation.json", review_packet_validation)
    write_json(debate_dir / "review" / "review-result.json", review_result)
    write_json(debate_dir / "review" / "review-result.validation.json", review_result_validation)

    report = {
        "ok": True,
        "action": "validate-canonical-execution",
        "debate_id": debate_id,
        "source_room_id": room_id,
        "artifacts": {
            "debate_dir": str(debate_dir),
            "launch_bundle": str(debate_dir / "launch" / "launch-bundle.json"),
            "roundtable_record": str(debate_dir / "roundtable" / "roundtable-record.json"),
            "roundtable_validation": str(debate_dir / "roundtable" / "roundtable.validation.json"),
            "review_packet": str(debate_dir / "review" / "review-packet.json"),
            "review_packet_validation": str(debate_dir / "review" / "review-packet.validation.json"),
            "review_result": str(debate_dir / "review" / "review-result.json"),
            "review_result_validation": str(debate_dir / "review" / "review-result.validation.json"),
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
        "review_result_validation": review_result_validation,
        "pass_criteria": {
            "launch_bundle_persisted": bool((debate_dir / "launch" / "launch-bundle.json").exists()),
            "roundtable_record_accepted": roundtable_validation["accepted"],
            "review_packet_matches_fixture": review_packet == expected_review_packet,
            "review_result_accepted": review_result_validation["accepted"],
            "allow_final_decision": review_result["allow_final_decision"],
        },
    }
    write_json(debate_dir / "validation-report.json", report)
    return report


def command_validate_canonical_followup(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    debate_id = "debate-canonical-followup"
    room_id = "room-canonical-debate"

    fixture_payload = materialize_placeholders(load_json(ROOM_UPGRADE_FIXTURE), {"__ROOM_ID__": room_id})
    packet = unwrap_packet(fixture_payload)
    packet_acceptance = validate_packet_payload(fixture_payload)
    registry = packet_validator.load_registry()
    launch_bundle = build_launch_bundle(
        packet=packet,
        packet_acceptance=packet_acceptance,
        registry=registry,
        debate_id=debate_id,
        source_packet_path=str(ROOM_UPGRADE_FIXTURE),
    )

    roundtable_record = materialize_placeholders(
        load_json(CANONICAL_ROUNDTABLE_RECORD),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    roundtable_validation = validate_roundtable_record(roundtable_record, launch_bundle)

    review_packet = build_review_packet(
        launch_bundle=launch_bundle,
        roundtable_record=roundtable_record,
        source_launch_bundle="canonical",
    )
    review_packet_validation = validate_review_packet(review_packet)
    expected_review_packet = materialize_placeholders(load_json(CANONICAL_REVIEW_PACKET), {"__ROOM_ID__": room_id})
    require(review_packet == expected_review_packet, "canonical followup review packet no longer matches fixture.")

    reject_review_result = materialize_placeholders(
        load_json(CANONICAL_FOLLOWUP_REVIEW_RESULT_REJECT),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    reject_review_result_validation = validate_review_result(reject_review_result, review_packet)
    require(
        reject_review_result["allow_final_decision"] is False,
        "canonical followup rejection fixture must reject final decision.",
    )

    followup_record = materialize_placeholders(
        load_json(CANONICAL_FOLLOWUP_RECORD),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    followup_validation = validate_followup_record(followup_record, reject_review_result, review_packet)

    rereview_packet = build_rereview_packet(
        review_packet=review_packet,
        review_result=reject_review_result,
        followup_record=followup_record,
    )
    rereview_packet_validation = validate_review_packet(rereview_packet)
    expected_rereview_packet = materialize_placeholders(
        load_json(CANONICAL_FOLLOWUP_REREVIEW_PACKET),
        {"__ROOM_ID__": room_id},
    )
    require(rereview_packet == expected_rereview_packet, "canonical rereview packet no longer matches fixture.")

    final_review_result = materialize_placeholders(
        load_json(CANONICAL_FOLLOWUP_REVIEW_RESULT_ALLOW),
        {"__ROOM_ID__": room_id, "__DEBATE_ID__": debate_id},
    )
    final_review_result_validation = validate_review_result(final_review_result, rereview_packet)
    require(
        final_review_result["allow_final_decision"] is True,
        "canonical followup final review fixture must allow final decision.",
    )

    debate_dir = get_debate_dir(state_root, debate_id)
    ensure_directory(debate_dir / "launch")
    ensure_directory(debate_dir / "roundtable")
    ensure_directory(debate_dir / "review")
    ensure_directory(debate_dir / "followup")
    write_json(debate_dir / "launch" / "launch-bundle.json", launch_bundle)
    write_json(debate_dir / "roundtable" / "roundtable-record.json", roundtable_record)
    write_json(debate_dir / "roundtable" / "roundtable.validation.json", roundtable_validation)
    write_json(debate_dir / "review" / "review-packet.json", review_packet)
    write_json(debate_dir / "review" / "review-packet.validation.json", review_packet_validation)
    write_json(debate_dir / "review" / "review-result.reject.json", reject_review_result)
    write_json(debate_dir / "review" / "review-result.reject.validation.json", reject_review_result_validation)
    write_json(debate_dir / "followup" / "followup-record.json", followup_record)
    write_json(debate_dir / "followup" / "followup.validation.json", followup_validation)
    write_json(debate_dir / "followup" / "rereview-packet.json", rereview_packet)
    write_json(debate_dir / "followup" / "rereview-packet.validation.json", rereview_packet_validation)
    write_json(debate_dir / "followup" / "review-result.allow.json", final_review_result)
    write_json(debate_dir / "followup" / "review-result.allow.validation.json", final_review_result_validation)

    report = {
        "ok": True,
        "action": "validate-canonical-followup",
        "debate_id": debate_id,
        "source_room_id": room_id,
        "artifacts": {
            "debate_dir": str(debate_dir),
            "launch_bundle": str(debate_dir / "launch" / "launch-bundle.json"),
            "roundtable_record": str(debate_dir / "roundtable" / "roundtable-record.json"),
            "review_packet": str(debate_dir / "review" / "review-packet.json"),
            "reject_review_result": str(debate_dir / "review" / "review-result.reject.json"),
            "followup_record": str(debate_dir / "followup" / "followup-record.json"),
            "rereview_packet": str(debate_dir / "followup" / "rereview-packet.json"),
            "final_review_result": str(debate_dir / "followup" / "review-result.allow.json"),
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
        "reject_review_result_validation": reject_review_result_validation,
        "followup_validation": followup_validation,
        "rereview_packet_validation": rereview_packet_validation,
        "final_review_result_validation": final_review_result_validation,
        "pass_criteria": {
            "initial_review_packet_matches_fixture": review_packet == expected_review_packet,
            "initial_reject_accepted": reject_review_result_validation["accepted"],
            "followup_record_accepted": followup_validation["accepted"],
            "rereview_packet_matches_fixture": rereview_packet == expected_rereview_packet,
            "final_review_result_accepted": final_review_result_validation["accepted"],
            "allow_final_decision_after_followup": final_review_result["allow_final_decision"],
        },
    }
    write_json(debate_dir / "validation-report.json", report)
    return report


def build_launch_bundle(
    *,
    packet: dict[str, Any],
    packet_acceptance: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    debate_id: str,
    source_packet_path: str,
) -> dict[str, Any]:
    primary_type = packet["field_03_type"]["primary"]
    secondary_type = packet["field_03_type"].get("secondary")
    suggested_agents = packet["field_11_suggested_agents"]
    defaults_primary = packet_validator.DEFAULT_AGENT_COMBINATIONS[primary_type]
    defaults_secondary = (
        packet_validator.DEFAULT_AGENT_COMBINATIONS[secondary_type] if secondary_type is not None else []
    )
    candidate_pool = build_candidate_pool(
        suggested_agents=suggested_agents,
        defaults_primary=defaults_primary,
        defaults_secondary=defaults_secondary,
        registry=registry,
    )
    scores = score_candidates(
        packet=packet,
        candidate_pool=candidate_pool,
        defaults_primary=defaults_primary,
        defaults_secondary=defaults_secondary,
        registry=registry,
    )
    final_agents, final_balance = choose_final_agents(
        candidate_pool=candidate_pool,
        suggested_agents=suggested_agents,
        scores=scores,
        registry=registry,
    )
    speaker_order = build_speaker_order(final_agents, seed_text=f"{packet['source_room_id']}:{debate_id}")

    participants = build_participants(
        final_agents=final_agents,
        packet=packet,
        defaults_primary=defaults_primary,
        defaults_secondary=defaults_secondary,
        registry=registry,
    )

    removed = [agent_id for agent_id in suggested_agents if agent_id not in final_agents]
    added = [agent_id for agent_id in final_agents if agent_id not in suggested_agents]
    minimum_overlap_target = min(2, len(suggested_agents))
    actual_overlap = sum(1 for agent_id in final_agents if agent_id in suggested_agents)
    notes: list[str] = []
    if removed:
        notes.append("reselection_removed_some_room_suggested_agents")
    if added:
        notes.append("reselection_added_debate_side_agents")
    if not final_balance["passes_debate_balance"]:
        notes.append("final_selection_still_unbalanced")
    if actual_overlap < minimum_overlap_target:
        notes.append("minimum_overlap_target_not_met")

    return {
        "schema_version": "v0.1",
        "mode": "debate_launch",
        "source_kind": "room_handoff",
        "debate_id": debate_id,
        "source_room_id": packet["source_room_id"],
        "source_packet_path": source_packet_path,
        "topic": packet["field_01_original_topic"],
        "room_title": packet["field_02_room_title"],
        "primary_type": primary_type,
        "secondary_type": secondary_type,
        "packet_acceptance": packet_acceptance,
        "packet_materials": {
            "sub_problems": packet["field_04_sub_problems"],
            "consensus_points": packet["field_05_consensus_points"],
            "tension_points": packet["field_06_tension_points"],
            "open_questions": packet["field_07_open_questions"],
            "candidate_solutions": packet["field_08_candidate_solutions"],
            "factual_claims": packet["field_09_factual_claims"],
            "uncertainty_points": packet["field_10_uncertainty_points"],
            "upgrade_reason": packet["field_13_upgrade_reason"],
        },
        "candidate_pool": {
            "starting_agents": suggested_agents,
            "defaults_primary": defaults_primary,
            "defaults_secondary": defaults_secondary,
            "candidate_pool": candidate_pool,
            "final_agents": final_agents,
            "removed_from_suggested": removed,
            "added_beyond_suggested": added,
            "minimum_overlap_target": minimum_overlap_target,
            "actual_overlap": actual_overlap,
            "balance_after_reselection": final_balance,
            "notes": notes,
        },
        "participants": participants,
        "moderator": {
            "agent_id": "debate-dispatcher",
            "role": "主持人",
            "responsibility": "组织 debate 8 步流程、汇总冲突与共识、提交审查包。",
        },
        "reviewer": {
            "agent_id": "debate-reviewer",
            "role": "审查 Agent",
            "review_required": True,
            "review_only_visible_outputs": True,
            "followup_cap": 1,
        },
        "speaker_order": speaker_order,
        "prompt_inputs": {
            "roundtable": {
                "topic": packet["field_01_original_topic"],
                "primary_type": primary_type,
                "secondary_type": secondary_type,
                "quick_mode": False,
                "packet_is_authoritative": True,
                "selected_agents": final_agents,
                "speaker_order": speaker_order,
                "starting_materials": {
                    "consensus_points": packet["field_05_consensus_points"],
                    "tension_points": packet["field_06_tension_points"],
                    "open_questions": packet["field_07_open_questions"],
                    "candidate_solutions": packet["field_08_candidate_solutions"],
                    "uncertainty_points": packet["field_10_uncertainty_points"],
                },
            },
            "reviewer": {
                "quick_mode": False,
                "review_required": True,
                "conversation_log_reviewable": False,
                "review_only_visible_outputs": True,
                "followup_cap": 1,
            },
            "followup": {
                "trigger": "reviewer_reject_only",
                "max_followup_rounds": 1,
            },
        },
    }


def build_review_template(launch_bundle: dict[str, Any], *, source_launch_bundle: str) -> dict[str, Any]:
    participants = [
        {
            "agent_id": item["agent_id"],
            "short_name": item["short_name"],
            "responsibility": item["responsibility"],
        }
        for item in launch_bundle["participants"]
    ]
    return {
        "schema_version": "v0.1",
        "source_kind": launch_bundle["source_kind"],
        "source_room_id": launch_bundle["source_room_id"],
        "source_launch_bundle": source_launch_bundle,
        "topic_restatement": "",
        "primary_type": launch_bundle["primary_type"],
        "secondary_type": launch_bundle.get("secondary_type"),
        "quick_mode": False,
        "participants": participants,
        "agent_outputs": [
            {
                "agent_id": item["agent_id"],
                "role_duty": item["responsibility"],
                "core_conclusion": "",
                "evidence": [],
                "biggest_problem": "",
                "opposed_misjudgment": "",
                "concrete_recommendation": "",
                "confidence": "",
                "uncertainties": [],
            }
            for item in participants
        ],
        "moderator_summary": {
            "topic_restatement": "",
            "participants_and_roles": participants,
            "consensus_points": [],
            "core_conflicts": [],
            "hidden_assumptions": [],
            "preliminary_recommendation": "",
            "review_focus": [],
        },
        "evidence_buckets": {
            "facts": [],
            "inferences": [],
            "uncertainties": [],
            "recommendations": [],
        },
        "review_boundaries": {
            "conversation_log_reviewable": False,
            "review_only_visible_outputs": True,
            "followup_cap": 1,
        },
    }


def build_review_packet(
    *,
    launch_bundle: dict[str, Any],
    roundtable_record: dict[str, Any],
    source_launch_bundle: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v0.1",
        "source_kind": launch_bundle["source_kind"],
        "source_room_id": launch_bundle["source_room_id"],
        "source_launch_bundle": source_launch_bundle,
        "topic_restatement": roundtable_record["topic_restatement"],
        "primary_type": roundtable_record["primary_type"],
        "secondary_type": roundtable_record.get("secondary_type"),
        "quick_mode": roundtable_record["quick_mode"],
        "participants": copy.deepcopy(roundtable_record["participants"]),
        "agent_outputs": copy.deepcopy(roundtable_record["agent_outputs"]),
        "moderator_summary": copy.deepcopy(roundtable_record["moderator_summary"]),
        "evidence_buckets": copy.deepcopy(roundtable_record["evidence_buckets"]),
        "review_boundaries": {
            "conversation_log_reviewable": False,
            "review_only_visible_outputs": launch_bundle["reviewer"]["review_only_visible_outputs"],
            "followup_cap": launch_bundle["reviewer"]["followup_cap"],
        },
    }


def validate_roundtable_record(payload: dict[str, Any], launch_bundle: dict[str, Any]) -> dict[str, Any]:
    registry = packet_validator.load_registry()
    validate_launch_bundle(launch_bundle)

    require(payload.get("schema_version") == "v0.1", "roundtable record schema_version must be v0.1.")
    require(payload.get("mode") == "debate_roundtable_record", "roundtable record mode must be debate_roundtable_record.")
    require(payload.get("source_kind") == launch_bundle["source_kind"], "roundtable record source_kind must match launch bundle.")
    require(payload.get("debate_id") == launch_bundle["debate_id"], "roundtable record debate_id must match launch bundle.")
    require(
        payload.get("source_room_id") == launch_bundle["source_room_id"],
        "roundtable record source_room_id must match launch bundle.",
    )
    require(
        isinstance(payload.get("topic_restatement"), str) and bool(payload["topic_restatement"].strip()),
        "roundtable record topic_restatement must be non-empty.",
    )
    require(
        payload.get("primary_type") == launch_bundle["primary_type"],
        "roundtable record primary_type must match launch bundle.",
    )
    require(
        payload.get("secondary_type") == launch_bundle.get("secondary_type"),
        "roundtable record secondary_type must match launch bundle.",
    )
    require(isinstance(payload.get("quick_mode"), bool), "roundtable record quick_mode must be a boolean.")

    participants = payload.get("participants")
    require(isinstance(participants, list) and 3 <= len(participants) <= 5, "roundtable record must contain 3-5 participants.")
    participant_ids: list[str] = []
    launch_participants = {item["agent_id"] for item in launch_bundle["participants"]}
    for item in participants:
        require(isinstance(item, dict), "roundtable record participants must be objects.")
        agent_id = item.get("agent_id")
        require(agent_id in registry, f"roundtable participant is not registered: {agent_id}")
        require(agent_id not in participant_ids, f"duplicate roundtable participant: {agent_id}")
        participant_ids.append(agent_id)
        require(
            isinstance(item.get("short_name"), str) and bool(item["short_name"].strip()),
            f"roundtable participant short_name must be non-empty for {agent_id}.",
        )
        require(
            isinstance(item.get("responsibility"), str) and bool(item["responsibility"].strip()),
            f"roundtable participant responsibility must be non-empty for {agent_id}.",
        )
    require(set(participant_ids) == launch_participants, "roundtable participants must match launch bundle participants.")

    speaker_order = payload.get("speaker_order")
    require(isinstance(speaker_order, list) and len(speaker_order) == len(participant_ids), "roundtable speaker_order must align with participants.")
    require(len(set(speaker_order)) == len(speaker_order), "roundtable speaker_order must not repeat participants.")
    require(set(speaker_order) == set(participant_ids), "roundtable speaker_order must cover the same participants.")

    review_status = payload.get("review_status")
    require(isinstance(review_status, dict), "roundtable review_status must be an object.")
    require(
        review_status.get("review_required") is (not payload["quick_mode"]),
        "roundtable review_required must reflect quick_mode.",
    )
    require(isinstance(review_status.get("followup_allowed"), bool), "roundtable followup_allowed must be a boolean.")
    require(review_status.get("max_followup_rounds") == 1, "roundtable max_followup_rounds must be 1.")
    if payload["quick_mode"]:
        require(review_status.get("followup_allowed") is False, "quick mode roundtable must not allow reviewer followup.")
    else:
        require(review_status.get("followup_allowed") is True, "full mode roundtable must allow one reviewer followup.")

    derived_review_packet = build_review_packet(
        launch_bundle=launch_bundle,
        roundtable_record=payload,
        source_launch_bundle="validation",
    )
    review_validation = validate_review_packet(derived_review_packet)

    return {
        "accepted": True,
        "checked_against": str(Path(__file__).resolve()),
        "reason": "roundtable record is structurally compatible with the checked-in launch bundle and reviewer packet contract.",
        "participant_count": len(participant_ids),
        "review_validation": review_validation,
    }


def validate_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    registry = packet_validator.load_registry()
    require(payload.get("schema_version") == "v0.1", "review packet schema_version must be v0.1.")
    require(payload.get("source_kind") in {"room_handoff", "direct_debate"}, "review packet source_kind is invalid.")
    require(
        isinstance(payload.get("topic_restatement"), str) and bool(payload["topic_restatement"].strip()),
        "review packet topic_restatement must be non-empty.",
    )
    require(payload.get("primary_type") in packet_validator.VALID_TASK_TYPES, "review packet primary_type is invalid.")
    secondary_type = payload.get("secondary_type")
    require(
        secondary_type is None or secondary_type in packet_validator.VALID_TASK_TYPES,
        "review packet secondary_type is invalid.",
    )
    require(isinstance(payload.get("quick_mode"), bool), "review packet quick_mode must be a boolean.")

    participants = payload.get("participants")
    require(isinstance(participants, list) and 3 <= len(participants) <= 5, "review packet must contain 3-5 participants.")
    participant_ids: list[str] = []
    for item in participants:
        require(isinstance(item, dict), "review packet participants must be objects.")
        agent_id = item.get("agent_id")
        require(agent_id in registry, f"review packet participant is not registered: {agent_id}")
        require(agent_id not in participant_ids, f"duplicate review packet participant: {agent_id}")
        participant_ids.append(agent_id)
        require(isinstance(item.get("short_name"), str) and bool(item["short_name"].strip()), "participant short_name must be non-empty.")
        require(
            isinstance(item.get("responsibility"), str) and bool(item["responsibility"].strip()),
            f"participant responsibility must be non-empty for {agent_id}.",
        )

    if payload["quick_mode"]:
        return {
            "accepted": True,
            "checked_against": str(Path(__file__).resolve()),
            "review_applicable": False,
            "reason": "quick mode review packet is structurally valid and correctly marked as reviewer-skipped.",
            "participant_count": len(participant_ids),
        }

    outputs = payload.get("agent_outputs")
    require(isinstance(outputs, list) and len(outputs) == len(participant_ids), "agent_outputs must align with participants.")
    seen_outputs: set[str] = set()
    for item in outputs:
        require(isinstance(item, dict), "agent_outputs items must be objects.")
        agent_id = item.get("agent_id")
        require(agent_id in participant_ids, f"agent_outputs contains unknown participant: {agent_id}")
        require(agent_id not in seen_outputs, f"duplicate agent output: {agent_id}")
        seen_outputs.add(agent_id)
        require(isinstance(item.get("role_duty"), str) and bool(item["role_duty"].strip()), f"role_duty missing for {agent_id}.")
        require(
            isinstance(item.get("core_conclusion"), str) and bool(item["core_conclusion"].strip()),
            f"core_conclusion missing for {agent_id}.",
        )
        evidence = item.get("evidence")
        require(isinstance(evidence, list) and len(evidence) >= 1, f"evidence list missing for {agent_id}.")
        require(all(isinstance(entry, str) and bool(entry.strip()) for entry in evidence), f"evidence entries invalid for {agent_id}.")
        require(
            isinstance(item.get("biggest_problem"), str) and bool(item["biggest_problem"].strip()),
            f"biggest_problem missing for {agent_id}.",
        )
        require(
            isinstance(item.get("opposed_misjudgment"), str) and bool(item["opposed_misjudgment"].strip()),
            f"opposed_misjudgment missing for {agent_id}.",
        )
        require(
            isinstance(item.get("concrete_recommendation"), str) and bool(item["concrete_recommendation"].strip()),
            f"concrete_recommendation missing for {agent_id}.",
        )
        require(item.get("confidence") in VALID_CONFIDENCE, f"confidence is invalid for {agent_id}.")
        uncertainties = item.get("uncertainties")
        require(isinstance(uncertainties, list), f"uncertainties must be a list for {agent_id}.")
        require(
            all(isinstance(entry, str) and bool(entry.strip()) for entry in uncertainties),
            f"uncertainties entries invalid for {agent_id}.",
        )

    moderator_summary = payload.get("moderator_summary")
    require(isinstance(moderator_summary, dict), "moderator_summary must be an object.")
    require(
        isinstance(moderator_summary.get("topic_restatement"), str)
        and bool(moderator_summary["topic_restatement"].strip()),
        "moderator_summary.topic_restatement must be non-empty.",
    )
    participant_roles = moderator_summary.get("participants_and_roles")
    require(isinstance(participant_roles, list) and len(participant_roles) == len(participant_ids), "participants_and_roles must align with participants.")
    summary_ids = []
    for item in participant_roles:
        require(isinstance(item, dict), "participants_and_roles entries must be objects.")
        require(item.get("agent_id") in participant_ids, "participants_and_roles contains unknown participant.")
        summary_ids.append(item["agent_id"])
        require(isinstance(item.get("responsibility"), str) and bool(item["responsibility"].strip()), "participants_and_roles responsibility must be non-empty.")
    require(set(summary_ids) == set(participant_ids), "participants_and_roles must cover the same participant set.")
    validate_non_empty_string_list(moderator_summary.get("consensus_points"), "moderator_summary.consensus_points")
    require(isinstance(moderator_summary.get("core_conflicts"), list), "moderator_summary.core_conflicts must be a list.")
    require(isinstance(moderator_summary.get("hidden_assumptions"), list), "moderator_summary.hidden_assumptions must be a list.")
    require(
        isinstance(moderator_summary.get("preliminary_recommendation"), str)
        and bool(moderator_summary["preliminary_recommendation"].strip()),
        "moderator_summary.preliminary_recommendation must be non-empty.",
    )
    validate_non_empty_string_list(moderator_summary.get("review_focus"), "moderator_summary.review_focus")

    evidence_buckets = payload.get("evidence_buckets")
    require(isinstance(evidence_buckets, dict), "evidence_buckets must be an object.")
    validate_non_empty_string_list(evidence_buckets.get("facts"), "evidence_buckets.facts")
    validate_non_empty_string_list(evidence_buckets.get("inferences"), "evidence_buckets.inferences")
    require(isinstance(evidence_buckets.get("uncertainties"), list), "evidence_buckets.uncertainties must be a list.")
    validate_non_empty_string_list(evidence_buckets.get("recommendations"), "evidence_buckets.recommendations")

    review_boundaries = payload.get("review_boundaries")
    require(isinstance(review_boundaries, dict), "review_boundaries must be an object.")
    require(review_boundaries.get("conversation_log_reviewable") is False, "conversation_log_reviewable must be false.")
    require(review_boundaries.get("review_only_visible_outputs") is True, "review_only_visible_outputs must be true.")
    require(review_boundaries.get("followup_cap") == 1, "followup_cap must be 1 for full mode.")

    return {
        "accepted": True,
        "checked_against": str(Path(__file__).resolve()),
        "review_applicable": True,
        "reason": "review packet satisfies the checked-in reviewer protocol contract for full-mode /debate review.",
        "participant_count": len(participant_ids),
    }


def validate_review_result(payload: dict[str, Any], review_packet: dict[str, Any]) -> dict[str, Any]:
    participant_ids = [item["agent_id"] for item in review_packet["participants"]]
    participant_set = set(participant_ids)
    allowed_followup_targets = participant_set | {"moderator"}

    require(payload.get("schema_version") == "v0.1", "review result schema_version must be v0.1.")
    require(payload.get("mode") == "debate_review_result", "review result mode must be debate_review_result.")
    require(payload.get("source_kind") == review_packet["source_kind"], "review result source_kind must match review packet.")
    require(
        payload.get("source_room_id") == review_packet["source_room_id"],
        "review result source_room_id must match review packet.",
    )
    require(
        isinstance(payload.get("topic_restatement"), str) and bool(payload["topic_restatement"].strip()),
        "review result topic_restatement must be non-empty.",
    )
    require(
        isinstance(payload.get("quick_mode"), bool) and payload["quick_mode"] == review_packet["quick_mode"],
        "review result quick_mode must match review packet.",
    )
    require(isinstance(payload.get("review_applicable"), bool), "review result review_applicable must be a boolean.")
    require(
        isinstance(payload.get("overall_score"), int) and 1 <= payload["overall_score"] <= 10,
        "review result overall_score must be an integer between 1 and 10.",
    )

    best_agent = payload.get("best_agent")
    require(isinstance(best_agent, str) and bool(best_agent.strip()), "review result best_agent must be non-empty.")
    require(best_agent in participant_set, "review result best_agent must be one of the debate participants.")

    weak_agents = payload.get("weak_agents")
    require(isinstance(weak_agents, list), "review result weak_agents must be a list.")
    require(len(set(weak_agents)) == len(weak_agents), "review result weak_agents must not contain duplicates.")
    require(all(isinstance(agent_id, str) and agent_id in participant_set for agent_id in weak_agents), "review result weak_agents must contain only participant ids.")

    validate_string_list_allow_empty(payload.get("evidence_gaps"), "review result evidence_gaps")
    validate_string_list_allow_empty(payload.get("logic_gaps"), "review result logic_gaps")
    validate_string_list_allow_empty(payload.get("overlooked_issues"), "review result overlooked_issues")
    validate_string_list_allow_empty(payload.get("severe_red_flags"), "review result severe_red_flags")

    require(isinstance(payload.get("allow_final_decision"), bool), "review result allow_final_decision must be a boolean.")

    required_followups = payload.get("required_followups")
    require(isinstance(required_followups, list), "review result required_followups must be a list.")
    seen_followups: set[str] = set()
    for item in required_followups:
        require(isinstance(item, dict), "required_followups entries must be objects.")
        agent_id = item.get("agent_id")
        require(
            agent_id in allowed_followup_targets,
            "required_followups.agent_id must be a debate participant or moderator.",
        )
        require(agent_id not in seen_followups, "required_followups must not repeat the same participant.")
        seen_followups.add(agent_id)
        require(
            isinstance(item.get("needs"), str) and bool(item["needs"].strip()),
            f"required_followups.needs must be non-empty for {agent_id}.",
        )

    require(
        isinstance(payload.get("rationale"), str) and bool(payload["rationale"].strip()),
        "review result rationale must be non-empty.",
    )

    if review_packet["quick_mode"]:
        require(payload["review_applicable"] is False, "quick mode review result must be marked not applicable.")
    else:
        require(payload["review_applicable"] is True, "full mode review result must be marked applicable.")

    if payload["allow_final_decision"]:
        require(payload["overall_score"] >= 7, "review result cannot allow final decision with score below 7.")
        require(len(payload["severe_red_flags"]) == 0, "review result cannot allow final decision with severe red flags.")
        require(len(required_followups) == 0, "review result cannot allow final decision while still requiring followups.")
    else:
        require(
            len(required_followups) >= 1 or payload["overall_score"] < 7 or len(payload["severe_red_flags"]) >= 1,
            "review result rejection must include followups, a low score, or severe red flags.",
        )

    return {
        "accepted": True,
        "checked_against": str(Path(__file__).resolve()),
        "review_applicable": payload["review_applicable"],
        "reason": "review result satisfies the checked-in reviewer decision contract.",
        "allow_final_decision": payload["allow_final_decision"],
    }


def validate_followup_record(
    payload: dict[str, Any],
    review_result: dict[str, Any],
    review_packet: dict[str, Any],
) -> dict[str, Any]:
    require(review_packet["quick_mode"] is False, "followup records are only valid for full mode review packets.")
    require(review_result["allow_final_decision"] is False, "followup records require a rejected reviewer result.")

    participant_map = {item["agent_id"]: item for item in review_packet["participants"]}
    required_map = {
        item["agent_id"]: item["needs"]
        for item in review_result["required_followups"]
    }
    require(len(required_map) >= 1, "followup records require at least one reviewer-requested followup target.")
    participant_targets = {agent_id for agent_id in required_map if agent_id != "moderator"}
    moderator_required = "moderator" in required_map

    require(payload.get("schema_version") == "v0.1", "followup record schema_version must be v0.1.")
    require(payload.get("mode") == "debate_followup_record", "followup record mode must be debate_followup_record.")
    require(payload.get("source_kind") == review_packet["source_kind"], "followup record source_kind must match review packet.")
    require(payload.get("debate_id") == review_result["debate_id"], "followup record debate_id must match rejected review result.")
    require(
        payload.get("source_room_id") == review_packet["source_room_id"],
        "followup record source_room_id must match review packet.",
    )
    require(
        isinstance(payload.get("topic_restatement"), str)
        and payload["topic_restatement"] == review_packet["topic_restatement"],
        "followup record topic_restatement must match review packet.",
    )
    require(
        isinstance(payload.get("quick_mode"), bool) and payload["quick_mode"] is False,
        "followup record quick_mode must be false.",
    )
    require(payload.get("followup_round") == 1, "followup record followup_round must be exactly 1.")

    validate_non_empty_string_list(payload.get("rejection_summary"), "followup record rejection_summary")

    required_followups = payload.get("required_followups")
    require(isinstance(required_followups, list), "followup record required_followups must be a list.")
    require(len(required_followups) == len(required_map), "followup record required_followups must mirror the reviewer result.")
    seen_required: set[str] = set()
    for item in required_followups:
        require(isinstance(item, dict), "followup record required_followups entries must be objects.")
        agent_id = item.get("agent_id")
        require(agent_id in required_map, f"followup record includes unexpected followup target: {agent_id}")
        require(agent_id not in seen_required, "followup record required_followups must not repeat targets.")
        seen_required.add(agent_id)
        require(
            item.get("needs") == required_map[agent_id],
            f"followup record required_followups.needs must match reviewer result for {agent_id}.",
        )
    require(seen_required == set(required_map), "followup record must cover every reviewer-requested followup target.")

    agent_followups = payload.get("agent_followups")
    require(isinstance(agent_followups, list), "followup record agent_followups must be a list.")
    seen_agent_followups: set[str] = set()
    for item in agent_followups:
        require(isinstance(item, dict), "followup record agent_followups entries must be objects.")
        agent_id = item.get("agent_id")
        require(agent_id in participant_targets, f"followup record contains unexpected participant followup: {agent_id}")
        require(agent_id not in seen_agent_followups, "followup record agent_followups must not repeat participants.")
        seen_agent_followups.add(agent_id)
        require(
            item.get("role_duty") == participant_map[agent_id]["responsibility"],
            f"followup record role_duty must match participant responsibility for {agent_id}.",
        )
        require(
            item.get("needs") == required_map[agent_id],
            f"followup record needs must match reviewer followup request for {agent_id}.",
        )
        validate_non_empty_string_list(item.get("supplemental_points"), f"followup record supplemental_points[{agent_id}]")
        require(
            isinstance(item.get("updated_recommendation"), str) and bool(item["updated_recommendation"].strip()),
            f"followup record updated_recommendation must be non-empty for {agent_id}.",
        )
        validate_string_list_allow_empty(
            item.get("remaining_uncertainties"),
            f"followup record remaining_uncertainties[{agent_id}]",
        )
    require(
        seen_agent_followups == participant_targets,
        "followup record agent_followups must cover exactly the participant targets requested by the reviewer.",
    )

    moderator_followup = payload.get("moderator_followup")
    if moderator_required:
        require(isinstance(moderator_followup, dict), "followup record moderator_followup is required when reviewer targets moderator.")
        require(
            moderator_followup.get("needs") == required_map["moderator"],
            "followup record moderator_followup.needs must match reviewer followup request for moderator.",
        )
        validate_non_empty_string_list(
            moderator_followup.get("added_or_corrected_consensus"),
            "followup record moderator_followup.added_or_corrected_consensus",
        )
        validate_non_empty_string_list(
            moderator_followup.get("added_or_corrected_conflicts"),
            "followup record moderator_followup.added_or_corrected_conflicts",
        )
        validate_non_empty_string_list(
            moderator_followup.get("facts"),
            "followup record moderator_followup.facts",
        )
        validate_non_empty_string_list(
            moderator_followup.get("inferences"),
            "followup record moderator_followup.inferences",
        )
        require(
            isinstance(moderator_followup.get("updated_preliminary_recommendation"), str)
            and bool(moderator_followup["updated_preliminary_recommendation"].strip()),
            "followup record moderator_followup.updated_preliminary_recommendation must be non-empty.",
        )
        validate_non_empty_string_list(
            moderator_followup.get("updated_stop_conditions"),
            "followup record moderator_followup.updated_stop_conditions",
        )
        validate_string_list_allow_empty(
            moderator_followup.get("remaining_uncertainties"),
            "followup record moderator_followup.remaining_uncertainties",
        )
    else:
        require(
            moderator_followup is None,
            "followup record must not include moderator_followup when moderator was not requested.",
        )

    rereview_status = payload.get("rereview_status")
    require(isinstance(rereview_status, dict), "followup record rereview_status must be an object.")
    require(rereview_status.get("rereview_required") is True, "followup record rereview_required must be true.")
    require(rereview_status.get("max_followup_rounds") == 1, "followup record max_followup_rounds must be 1.")
    require(rereview_status.get("return_to_reviewer") is True, "followup record return_to_reviewer must be true.")

    return {
        "accepted": True,
        "checked_against": str(Path(__file__).resolve()),
        "reason": "followup record satisfies the checked-in reject-followup-rereview contract.",
        "participant_followup_count": len(participant_targets),
        "moderator_followup_required": moderator_required,
    }


def build_rereview_packet(
    *,
    review_packet: dict[str, Any],
    review_result: dict[str, Any],
    followup_record: dict[str, Any],
) -> dict[str, Any]:
    rereview_packet = copy.deepcopy(review_packet)
    participant_followups = {
        item["agent_id"]: item
        for item in followup_record["agent_followups"]
    }

    rereview_packet["followup_context"] = {
        "followup_round": followup_record["followup_round"],
        "rejection_summary": copy.deepcopy(followup_record["rejection_summary"]),
        "prior_review_result": {
            "overall_score": review_result["overall_score"],
            "best_agent": review_result["best_agent"],
            "weak_agents": copy.deepcopy(review_result["weak_agents"]),
            "evidence_gaps": copy.deepcopy(review_result["evidence_gaps"]),
            "logic_gaps": copy.deepcopy(review_result["logic_gaps"]),
            "overlooked_issues": copy.deepcopy(review_result["overlooked_issues"]),
            "severe_red_flags": copy.deepcopy(review_result["severe_red_flags"]),
            "allow_final_decision": review_result["allow_final_decision"],
            "required_followups": copy.deepcopy(review_result["required_followups"]),
            "rationale": review_result["rationale"],
        },
        "return_to_reviewer": followup_record["rereview_status"]["return_to_reviewer"],
    }

    for output in rereview_packet["agent_outputs"]:
        agent_id = output["agent_id"]
        if agent_id not in participant_followups:
            continue
        followup = participant_followups[agent_id]
        output["followup_update"] = {
            "needs": followup["needs"],
            "supplemental_points": copy.deepcopy(followup["supplemental_points"]),
            "updated_recommendation": followup["updated_recommendation"],
            "remaining_uncertainties": copy.deepcopy(followup["remaining_uncertainties"]),
        }
        rereview_packet["evidence_buckets"]["recommendations"].append(followup["updated_recommendation"])
        rereview_packet["evidence_buckets"]["uncertainties"].extend(copy.deepcopy(followup["remaining_uncertainties"]))

    moderator_followup = followup_record.get("moderator_followup")
    if moderator_followup is None:
        moderator_followup = synthesize_moderator_followup(
            review_packet=review_packet,
            review_result=review_result,
            followup_record=followup_record,
        )
    if moderator_followup is not None:
        rereview_packet["moderator_summary"]["consensus_points"].extend(
            copy.deepcopy(moderator_followup["added_or_corrected_consensus"])
        )
        rereview_packet["moderator_summary"]["core_conflicts"].extend(
            copy.deepcopy(moderator_followup["added_or_corrected_conflicts"])
        )
        rereview_packet["moderator_summary"]["preliminary_recommendation"] = moderator_followup[
            "updated_preliminary_recommendation"
        ]
        rereview_packet["moderator_summary"]["stop_conditions"] = copy.deepcopy(
            moderator_followup["updated_stop_conditions"]
        )
        rereview_packet["moderator_summary"]["followup_update"] = {
            "needs": moderator_followup["needs"],
            "facts": copy.deepcopy(moderator_followup["facts"]),
            "inferences": copy.deepcopy(moderator_followup["inferences"]),
            "updated_preliminary_recommendation": moderator_followup["updated_preliminary_recommendation"],
            "updated_stop_conditions": copy.deepcopy(moderator_followup["updated_stop_conditions"]),
            "remaining_uncertainties": copy.deepcopy(moderator_followup["remaining_uncertainties"]),
        }
        if moderator_followup.get("synthesized_from_agent_followups") is True:
            rereview_packet["moderator_summary"]["followup_update"]["synthesized_from_agent_followups"] = True
        rereview_packet["evidence_buckets"]["facts"].extend(copy.deepcopy(moderator_followup["facts"]))
        rereview_packet["evidence_buckets"]["inferences"].extend(copy.deepcopy(moderator_followup["inferences"]))
        rereview_packet["evidence_buckets"]["uncertainties"].extend(
            copy.deepcopy(moderator_followup["remaining_uncertainties"])
        )
        rereview_packet["evidence_buckets"]["recommendations"].append(
            moderator_followup["updated_preliminary_recommendation"]
        )
        rereview_packet["evidence_buckets"]["recommendations"].extend(
            copy.deepcopy(moderator_followup["updated_stop_conditions"])
        )

    rereview_packet["review_boundaries"]["followup_round"] = followup_record["followup_round"]
    rereview_packet["review_boundaries"]["rereview_required"] = True
    return rereview_packet


def synthesize_moderator_followup(
    *,
    review_packet: dict[str, Any],
    review_result: dict[str, Any],
    followup_record: dict[str, Any],
) -> dict[str, Any] | None:
    agent_followups = followup_record.get("agent_followups")
    if not isinstance(agent_followups, list) or not agent_followups:
        return None

    participant_map = {
        item["agent_id"]: item
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    integrated_recommendations: list[str] = []
    integrated_inferences: list[str] = []
    remaining_uncertainties: list[str] = []
    entry_candidates: list[str] = []
    workflow_constraints: list[str] = []
    gate_candidates: list[str] = []
    for item in agent_followups:
        if not isinstance(item, dict):
            continue
        agent_id = item.get("agent_id")
        participant = participant_map.get(agent_id, {})
        label = participant.get("short_name") or agent_id
        updated_recommendation = item.get("updated_recommendation")
        if isinstance(updated_recommendation, str) and updated_recommendation.strip():
            cleaned = updated_recommendation.strip()
            integrated_recommendations.append(f"{label}: {cleaned}")
            classify_followup_text(
                cleaned,
                entry_candidates=entry_candidates,
                workflow_constraints=workflow_constraints,
                gate_candidates=gate_candidates,
            )
        supplemental_points = item.get("supplemental_points")
        if isinstance(supplemental_points, list):
            for point in supplemental_points:
                if isinstance(point, str) and point.strip():
                    cleaned = point.strip()
                    integrated_inferences.append(f"{label}: {cleaned}")
                    classify_followup_text(
                        cleaned,
                        entry_candidates=entry_candidates,
                        workflow_constraints=workflow_constraints,
                        gate_candidates=gate_candidates,
                    )
        uncertainties = item.get("remaining_uncertainties")
        if isinstance(uncertainties, list):
            for point in uncertainties:
                if isinstance(point, str) and point.strip():
                    remaining_uncertainties.append(point.strip())

    if not integrated_recommendations:
        return None

    synthesized_stop_conditions = collect_stop_conditions_from_followups(agent_followups)
    reviewer_feedback = dedupe_non_empty_strings(
        review_result.get("evidence_gaps", [])
        + review_result.get("logic_gaps", [])
        + review_result.get("overlooked_issues", [])
        + review_result.get("severe_red_flags", [])
    )
    should_block = should_emit_blocked_followup(
        entry_candidates=entry_candidates,
        gate_candidates=gate_candidates,
        reviewer_feedback=reviewer_feedback,
    )

    if should_block:
        blocking_prerequisites = build_blocking_prerequisites(
            review_result=review_result,
            entry_candidates=entry_candidates,
            workflow_constraints=workflow_constraints,
            gate_candidates=gate_candidates,
        )
        integrated_preliminary_recommendation = build_blocked_preliminary_recommendation(
            entry_candidates=entry_candidates,
            blocking_prerequisites=blocking_prerequisites,
        )
        synthesized_stop_conditions = build_blocking_stop_conditions(
            blocking_prerequisites=blocking_prerequisites,
            derived_stop_conditions=synthesized_stop_conditions,
        )
        added_or_corrected_consensus = build_blocking_consensus(
            entry_candidates=entry_candidates,
            blocking_prerequisites=blocking_prerequisites,
        )
        added_or_corrected_conflicts = reviewer_feedback[:3]
        integrated_inferences.extend(blocking_prerequisites)
    else:
        integrated_preliminary_recommendation = build_structured_preliminary_recommendation(
            entry_candidates=entry_candidates,
            workflow_constraints=workflow_constraints,
            gate_candidates=gate_candidates,
            remaining_uncertainties=remaining_uncertainties,
        )
        added_or_corrected_consensus = build_structured_consensus(
            entry_candidates=entry_candidates,
            workflow_constraints=workflow_constraints,
            gate_candidates=gate_candidates,
        )
        added_or_corrected_conflicts = []

    return {
        "needs": (
            "主持人需把 reviewer 点名补充的结果整合成单一可复审建议。"
            if not should_block
            else "主持人需把补充结果收束成单一阻塞结论，明确当前为什么还不能放行。"
        ),
        "added_or_corrected_consensus": added_or_corrected_consensus,
        "added_or_corrected_conflicts": added_or_corrected_conflicts,
        "facts": [],
        "inferences": copy.deepcopy(integrated_inferences),
        "updated_preliminary_recommendation": integrated_preliminary_recommendation,
        "updated_stop_conditions": synthesized_stop_conditions,
        "remaining_uncertainties": dedupe_non_empty_strings(remaining_uncertainties + review_result.get("logic_gaps", [])),
        "synthesized_from_agent_followups": True,
    }


def classify_followup_text(
    text: str,
    *,
    entry_candidates: list[str],
    workflow_constraints: list[str],
    gate_candidates: list[str],
) -> None:
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "首发入口",
            "第一刀",
            "单押",
            "固定为",
            "ddl 前",
            "考试周",
            "文本场景",
            "课程短文",
            "作业文字说明",
            "单题单步",
            "垂直场景",
            "候选场景",
        )
    ):
        entry_candidates.append(text)
    if any(
        marker in lowered
        for marker in (
            "流程",
            "步骤",
            "上传",
            "回填",
            "审核",
            "闭环",
            "闸门",
            "界面",
            "生成",
            "提交帮助度",
        )
    ):
        workflow_constraints.append(text)
    if any(
        marker in lowered
        for marker in (
            "完成率",
            "复用率",
            "回访",
            "阈值",
            "停止",
            "判定",
            "不允许",
            "低于",
            "高于",
            "一票否决",
            "样本",
            "放行",
            "主指标",
            "迁移",
            "复述",
        )
    ):
        gate_candidates.append(text)


def should_emit_blocked_followup(
    *,
    entry_candidates: list[str],
    gate_candidates: list[str],
    reviewer_feedback: list[str],
) -> bool:
    if not has_locked_entry_candidate(entry_candidates) or not gate_candidates:
        return True

    block_markers = (
        "没有可见候选场景清单",
        "切口未锁定",
        "仍停留在筛选标准层",
        "未形成足够清晰的成功/失败门槛",
        "没有新增可核实事实",
        "仍主要建立在推断",
        "应输出阻塞结论",
        "不应启动实验",
        "结论先行",
        "虚假共识",
    )
    for item in reviewer_feedback:
        if any(marker in item for marker in block_markers):
            return True
    return False


def has_locked_entry_candidate(entry_candidates: list[str]) -> bool:
    lock_markers = ("锁定", "固定为", "只选", "定为", "单押", "不再并列", "首发入口固定", "第一刀场景定为")
    for item in entry_candidates:
        if any(marker in item for marker in lock_markers):
            return True
    return False


def build_blocking_prerequisites(
    *,
    review_result: dict[str, Any],
    entry_candidates: list[str],
    workflow_constraints: list[str],
    gate_candidates: list[str],
) -> list[str]:
    prerequisites: list[str] = []
    feedback = dedupe_non_empty_strings(
        review_result.get("evidence_gaps", [])
        + review_result.get("logic_gaps", [])
        + review_result.get("overlooked_issues", [])
        + review_result.get("severe_red_flags", [])
    )

    if entry_candidates:
        prerequisites.append("当前讨论里出现过的首刀/入口都只能保留为候选假设，不得在没有额外证据前写成已收束结论。")

    if any("没有可见候选场景清单" in item or "切口" in item for item in feedback):
        prerequisites.append("在至少拿出一个通过筛选标准的具体候选切口前，不允许启动首轮实验。")
    if any("没有新增可核实事实" in item or "仍主要建立在推断" in item for item in feedback):
        prerequisites.append("在没有新增外部事实时，所有关于场景频率、复用强度和需求动机的判断都只能降格为待验证假设。")
    if any("门槛" in item or "阈值" in item or "判定" in item for item in feedback) or not gate_candidates:
        prerequisites.append("在把成功/失败门槛、停止条件和样本归类规则写成单表前，不允许放行。")
    if any("人工" in item or "时延" in item for item in workflow_constraints + gate_candidates + feedback):
        prerequisites.append("在人工风险闸门的先后顺序、时延上限和超标后的处理规则明确前，不允许把人工兜底写成已成立路径。")

    if not prerequisites:
        prerequisites.append("在主持人无法把补充内容压成单一路径前，不允许把本轮讨论写成可启动实验。")
    return dedupe_non_empty_strings(prerequisites)


def build_blocked_preliminary_recommendation(
    *,
    entry_candidates: list[str],
    blocking_prerequisites: list[str],
) -> str:
    parts = [
        "补充后主持人统一结论：本轮的最终决议不是启动受限首版实验，而是维持阻塞结论。",
    ]
    if entry_candidates:
        parts.append(f"当前只允许把“{entry_candidates[0]}”保留为候选假设，而不是已收束切口。")
    parts.append("在以下前置条件满足前，只允许保留筛选标准、风险边界和判停规则，不允许扩入口，也不允许对外承诺学习有效。")
    if blocking_prerequisites:
        parts.append("前置条件包括：" + "；".join(blocking_prerequisites))
    return " ".join(parts)


def build_blocking_stop_conditions(
    *,
    blocking_prerequisites: list[str],
    derived_stop_conditions: list[str],
) -> list[str]:
    stop_conditions = [
        "只要上述任一前置条件仍未满足，就维持阻塞结论，不允许启动首版实验。",
        "如果后续材料仍只能提供筛选标准而没有单一可执行切口，就直接结束本轮 debate，不再解释成可放行方案。",
    ]
    stop_conditions.extend(blocking_prerequisites)
    stop_conditions.extend(derived_stop_conditions)
    return dedupe_non_empty_strings(stop_conditions)


def build_blocking_consensus(
    *,
    entry_candidates: list[str],
    blocking_prerequisites: list[str],
) -> list[str]:
    items = ["本轮最终结论改为阻塞，不批准直接启动首版实验。"]
    if entry_candidates:
        items.append(f"当前只能把“{entry_candidates[0]}”保留为候选假设。")
    items.extend(blocking_prerequisites[:3])
    return dedupe_non_empty_strings(items)


def build_structured_preliminary_recommendation(
    *,
    entry_candidates: list[str],
    workflow_constraints: list[str],
    gate_candidates: list[str],
    remaining_uncertainties: list[str],
) -> str:
    parts = [
        "补充后主持人统一建议：当前只允许执行一个受限首版实验，不允许并行扩展其他入口，也不允许把方案放大成更重的产品化投入。",
    ]
    if entry_candidates:
        parts.append(f"唯一允许继续验证的首刀切口是：{entry_candidates[0]}")
    if workflow_constraints:
        parts.append("执行链路只保留：" + "；".join(dedupe_non_empty_strings(workflow_constraints)[:3]))
    if gate_candidates:
        parts.append("放行与停表只看：" + "；".join(dedupe_non_empty_strings(gate_candidates)[:4]))
    if remaining_uncertainties:
        parts.append("凡仍缺事实支撑的频率、需求强度和长期价值判断，一律降格为待验证假设，不写成已证成事实。")
    parts.append("只要触发任一停止条件，就直接判定该方向暂不成立，不得继续放大。")
    return " ".join(parts)


def build_structured_consensus(
    *,
    entry_candidates: list[str],
    workflow_constraints: list[str],
    gate_candidates: list[str],
) -> list[str]:
    items: list[str] = []
    if entry_candidates:
        items.append(f"唯一允许继续验证的首刀切口是：{entry_candidates[0]}")
    if workflow_constraints:
        items.append("执行链路必须收敛为单一路径，不再并列多种入口或多套人工兜底方式。")
    if gate_candidates:
        items.append("放行与停表标准必须先于扩张决定写死，不能靠事后解释补救。")
    return dedupe_non_empty_strings(items)


def dedupe_non_empty_strings(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def collect_stop_conditions_from_followups(agent_followups: list[Any]) -> list[str]:
    derived: list[str] = []
    trigger_words = ("停止", "暂停", "失败", "不允许", "高风险", "偏向代做", "不进入", "拦截")
    for item in agent_followups:
        if not isinstance(item, dict):
            continue
        for field in ("updated_recommendation",):
            value = item.get(field)
            if isinstance(value, str) and value.strip() and any(word in value for word in trigger_words):
                derived.append(value.strip())
        supplemental_points = item.get("supplemental_points")
        if not isinstance(supplemental_points, list):
            continue
        for point in supplemental_points:
            if isinstance(point, str) and point.strip() and any(word in point for word in trigger_words):
                derived.append(point.strip())

    if not derived:
        for item in agent_followups:
            if not isinstance(item, dict):
                continue
            recommendation = item.get("updated_recommendation")
            if isinstance(recommendation, str) and recommendation.strip():
                derived.append(f"若无法满足以下补充要求，则不允许继续放大：{recommendation.strip()}")

    return dedupe_non_empty_strings(derived)


def validate_launch_bundle(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == "v0.1", "launch bundle schema_version must be v0.1.")
    require(payload.get("mode") == "debate_launch", "launch bundle mode must be debate_launch.")
    require(payload.get("source_kind") == "room_handoff", "launch bundle source_kind must be room_handoff.")
    require(isinstance(payload.get("participants"), list) and 3 <= len(payload["participants"]) <= 5, "launch bundle participants must contain 3-5 agents.")


def validate_packet_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return packet_validator.validate_handoff_packet(payload)
    except Exception as exc:
        raise DebateRuntimeError(f"handoff packet failed debate preflight: {exc}") from exc


def unwrap_packet(payload: dict[str, Any]) -> dict[str, Any]:
    packet = payload.get("handoff_packet") if "handoff_packet" in payload else payload
    require(isinstance(packet, dict), "handoff packet payload must be an object.")
    return packet


def build_candidate_pool(
    *,
    suggested_agents: list[str],
    defaults_primary: list[str],
    defaults_secondary: list[str],
    registry: dict[str, dict[str, Any]],
) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for agent_id in suggested_agents + defaults_primary + defaults_secondary:
        if agent_id in seen:
            continue
        if registry[agent_id]["default_excluded"] and agent_id not in suggested_agents:
            continue
        seen.add(agent_id)
        ordered.append(agent_id)
    return ordered


def score_candidates(
    *,
    packet: dict[str, Any],
    candidate_pool: list[str],
    defaults_primary: list[str],
    defaults_secondary: list[str],
    registry: dict[str, dict[str, Any]],
) -> dict[str, int]:
    suggested_agents = packet["field_11_suggested_agents"]
    suggested_ranks = {agent_id: index for index, agent_id in enumerate(suggested_agents)}
    discussed_agents = collect_discussed_agents(packet)
    scores: dict[str, int] = {}
    for agent_id in candidate_pool:
        entry = registry[agent_id]
        score = 0
        if agent_id in suggested_ranks:
            score += 100 - suggested_ranks[agent_id] * 5
        if agent_id in defaults_primary:
            score += 30
        if agent_id in defaults_secondary:
            score += 12
        if agent_id in discussed_agents:
            score += 10
        if agent_id in packet["field_12_suggested_agent_roles"]:
            score += 6
        if entry["structural_role"] == "defensive":
            score += 6
        if entry["expression"] == "grounded":
            score += 5
        if entry["strength"] == "moderate":
            score += 2
        if entry["expression"] == "dramatic":
            score -= 8
        if entry["default_excluded"]:
            score -= 20
        scores[agent_id] = score
    return scores


def choose_final_agents(
    *,
    candidate_pool: list[str],
    suggested_agents: list[str],
    scores: dict[str, int],
    registry: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    suggested_set = set(suggested_agents)
    minimum_overlap_target = min(2, len(suggested_agents))
    target_count = max(3, min(5, len(suggested_agents)))
    max_count = min(5, len(candidate_pool))

    best_combo: tuple[str, ...] | None = None
    best_rank: tuple[Any, ...] | None = None
    for count in range(target_count, max_count + 1):
        for combo in itertools.combinations(candidate_pool, count):
            combo_set = set(combo)
            overlap = len(combo_set & suggested_set)
            balance = packet_validator.summarize_balance(list(combo), registry)
            rank = (
                1 if balance["passes_debate_balance"] else 0,
                1 if overlap >= minimum_overlap_target else 0,
                overlap,
                -abs(count - target_count),
                sum(scores[agent_id] for agent_id in combo),
                balance["defensive_count"],
                balance["grounded_count"],
                -balance["dominant_ratio"],
            )
            if best_rank is None or rank > best_rank:
                best_rank = rank
                best_combo = combo

    require(best_combo is not None, "failed to select a debate roster from the candidate pool.")
    ordered = sorted(
        best_combo,
        key=lambda agent_id: (-scores[agent_id], candidate_pool.index(agent_id)),
    )
    return ordered, packet_validator.summarize_balance(ordered, registry)


def build_speaker_order(agent_ids: list[str], *, seed_text: str) -> list[str]:
    ordered = sorted(
        agent_ids,
        key=lambda agent_id: stable_int(f"{seed_text}:{agent_id}"),
    )
    return ordered


def build_participants(
    *,
    final_agents: list[str],
    packet: dict[str, Any],
    defaults_primary: list[str],
    defaults_secondary: list[str],
    registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    participants: list[dict[str, Any]] = []
    for agent_id in final_agents:
        entry = registry[agent_id]
        responsibility = packet["field_12_suggested_agent_roles"].get(agent_id) or fallback_role(
            agent_id=agent_id,
            entry=entry,
            primary_type=packet["field_03_type"]["primary"],
        )
        why_selected = build_selection_reason(
            agent_id=agent_id,
            in_suggested=agent_id in packet["field_11_suggested_agents"],
            in_primary=agent_id in defaults_primary,
            in_secondary=agent_id in defaults_secondary,
        )
        participants.append(
            {
                "agent_id": agent_id,
                "short_name": entry["short_name"],
                "local_skill": f"{agent_id}-skill",
                "responsibility": responsibility,
                "why_selected": why_selected,
                "should_not_do": build_guardrail(entry),
            }
        )
    return participants


def fallback_role(*, agent_id: str, entry: dict[str, Any], primary_type: str) -> str:
    focus_tags = entry.get("sub_problem_tags", "").split(",")
    focus_bits = [tag.strip() for tag in focus_tags if tag.strip()][:2]
    focus_label = " / ".join(focus_bits) if focus_bits else "关键判断"
    return (
        f"围绕{TASK_LABELS[primary_type]}，重点从 {focus_label} 角度补齐正式审议中的"
        f"{entry['structural_role']} 视角缺口。"
    )


def build_selection_reason(*, agent_id: str, in_suggested: bool, in_primary: bool, in_secondary: bool) -> str:
    reasons: list[str] = []
    if in_suggested:
        reasons.append("保留 room 升级上下文")
    if in_primary:
        reasons.append("符合主分类默认组合")
    if in_secondary:
        reasons.append("补副分类缺口")
    if not reasons:
        reasons.append("用于完成 debate 结构平衡")
    return "，".join(reasons) + f" ({agent_id})。"


def build_guardrail(entry: dict[str, Any]) -> str:
    if entry["expression"] == "dramatic":
        return "不要用戏剧化叙事替代依据，必须把强判断压回可检验假设。"
    if entry["structural_role"] == "offensive":
        return "不要把方向判断扩成压倒性结论，必须回应约束与下行。"
    if entry["structural_role"] == "defensive":
        return "不要只是否定，必须把风险翻译成门槛、动作或停止条件。"
    return "不要重复别人的判断，优先补机制、解释或连接层缺口。"


def collect_discussed_agents(packet: dict[str, Any]) -> set[str]:
    discussed: set[str] = set()
    for solution in packet["field_08_candidate_solutions"]:
        for agent_id in solution["proposed_by"]:
            discussed.add(agent_id)
    for claim in packet["field_09_factual_claims"]:
        for agent_id in claim["cited_by"]:
            discussed.add(agent_id)
    return discussed


def derive_debate_id(source_room_id: str) -> str:
    suffix = stable_hex(source_room_id)[:8]
    return f"debate-{suffix}"


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def materialize_placeholders(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: materialize_placeholders(subvalue, replacements) for key, subvalue in value.items()}
    if isinstance(value, list):
        return [materialize_placeholders(item, replacements) for item in value]
    if isinstance(value, str):
        result = value
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    return copy.deepcopy(value)


def get_debate_dir(state_root: Path, debate_id: str) -> Path:
    return state_root / debate_id


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DebateRuntimeError(f"JSON file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DebateRuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_non_empty_string_list(value: Any, field_name: str) -> None:
    require(isinstance(value, list) and len(value) >= 1, f"{field_name} must be a non-empty list.")
    require(all(isinstance(item, str) and bool(item.strip()) for item in value), f"{field_name} entries must be non-empty strings.")


def validate_string_list_allow_empty(value: Any, field_name: str) -> None:
    require(isinstance(value, list), f"{field_name} must be a list.")
    require(all(isinstance(item, str) and bool(item.strip()) for item in value), f"{field_name} entries must be non-empty strings.")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DebateRuntimeError(message)


if __name__ == "__main__":
    sys.exit(main())
