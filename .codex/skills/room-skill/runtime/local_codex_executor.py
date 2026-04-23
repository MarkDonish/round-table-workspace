#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chat_completions_executor import parse_json_from_text


REPO_ROOT = Path(__file__).resolve().parent.parents[3]
CODEX_HOME = Path.home() / ".codex"
DEFAULT_SANDBOX = "read-only"
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_TIMEOUT_RETRIES = 1
DEFAULT_RETRY_TIMEOUT_MULTIPLIER = 1.5
DEFAULT_REASONING_EFFORT = "medium"
LOCAL_CODEX_PRESETS = {
    "gpt54_family": {
        "model": "gpt-5.4",
        "fallback_models": ["gpt-5.4-mini"],
        "profile": None,
        "reasoning_effort": "low",
        "sandbox": DEFAULT_SANDBOX,
        "timeout_seconds": 240,
        "timeout_retries": 1,
        "retry_timeout_multiplier": DEFAULT_RETRY_TIMEOUT_MULTIPLIER,
        "persist_session": False,
        "step_policies": {
            "room_full_selection": {
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
            "room_turn_selection": {
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
            "room_chat": {
                "timeout_seconds": 300,
                "timeout_retries": 1,
            },
            "room_summary": {
                "model": "gpt-5.4-mini",
                "fallback_models": ["gpt-5.4"],
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
            "room_upgrade": {
                "model": "gpt-5.4-mini",
                "fallback_models": ["gpt-5.4"],
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
            "debate_roundtable": {
                "timeout_seconds": 300,
                "timeout_retries": 1,
            },
            "debate_reviewer_initial": {
                "model": "gpt-5.4-mini",
                "fallback_models": ["gpt-5.4"],
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
            "debate_followup": {
                "timeout_seconds": 300,
                "timeout_retries": 1,
            },
            "debate_reviewer_rereview": {
                "model": "gpt-5.4-mini",
                "fallback_models": ["gpt-5.4"],
                "timeout_seconds": 180,
                "timeout_retries": 0,
            },
        },
    }
}
SMOKE_RESPONSE = {"ok": True, "mode": "local_codex_exec"}
HOST_PREFLIGHT_PROBE_PREFIX = ".round-table-host-preflight-"
TRACE_MANIFEST_SUFFIX = ".child-trace.json"
STEP_POLICY_OVERRIDE_FIELDS = (
    "model",
    "fallback_models",
    "profile",
    "reasoning_effort",
    "sandbox",
    "timeout_seconds",
    "timeout_retries",
    "retry_timeout_multiplier",
)


class LocalCodexExecutorError(Exception):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    resolved = resolve_execution_settings(
        preset_name=args.preset,
        model=args.model,
        fallback_models=parse_model_list(args.fallback_models) if args.fallback_models is not None else None,
        profile=args.profile,
        reasoning_effort=args.reasoning_effort,
        sandbox=args.sandbox,
        timeout_seconds=args.timeout_seconds,
        timeout_retries=args.timeout_retries,
        retry_timeout_multiplier=args.retry_timeout_multiplier,
        persist_session=args.persist_session,
    )

    try:
        if args.check_host_preflight:
            result = check_local_host_preflight(
                repo_root=REPO_ROOT,
                model=resolved["model"],
                fallback_models=resolved["fallback_models"],
                profile=resolved["profile"],
                reasoning_effort=resolved["reasoning_effort"],
                sandbox=resolved["sandbox"],
                timeout_seconds=resolved["timeout_seconds"],
                timeout_retries=resolved["timeout_retries"],
                retry_timeout_multiplier=resolved["retry_timeout_multiplier"],
                ephemeral=resolved["ephemeral"],
                preset_name=resolved["preset"],
            )
        elif args.check_local_exec:
            result = check_local_exec(
                repo_root=REPO_ROOT,
                model=resolved["model"],
                fallback_models=resolved["fallback_models"],
                profile=resolved["profile"],
                reasoning_effort=resolved["reasoning_effort"],
                sandbox=resolved["sandbox"],
                timeout_seconds=resolved["timeout_seconds"],
                timeout_retries=resolved["timeout_retries"],
                retry_timeout_multiplier=resolved["retry_timeout_multiplier"],
                ephemeral=resolved["ephemeral"],
                preset_name=resolved["preset"],
            )
        else:
            if not args.prompt_file or not args.input_json:
                raise LocalCodexExecutorError(
                    "--prompt-file and --input-json are required unless --check-local-exec or --check-host-preflight is used."
                )
            prompt_path = Path(args.prompt_file).expanduser().resolve()
            input_path = Path(args.input_json).expanduser().resolve()
            result = call_local_codex(
                prompt_path=prompt_path,
                prompt_text=prompt_path.read_text(encoding="utf-8"),
                prompt_input=json.loads(input_path.read_text(encoding="utf-8")),
                repo_root=REPO_ROOT,
                model=resolved["model"],
                fallback_models=resolved["fallback_models"],
                profile=resolved["profile"],
                reasoning_effort=resolved["reasoning_effort"],
                sandbox=resolved["sandbox"],
                timeout_seconds=resolved["timeout_seconds"],
                timeout_retries=resolved["timeout_retries"],
                retry_timeout_multiplier=resolved["retry_timeout_multiplier"],
                ephemeral=resolved["ephemeral"],
            )
    except (LocalCodexExecutorError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    output_json = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
    else:
        sys.stdout.write(output_json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run checked-in round-table prompts through local Codex child-agent tasks."
    )
    check_group = parser.add_mutually_exclusive_group()
    check_group.add_argument("--check-local-exec", action="store_true", help="Run a minimal local child-agent smoke test.")
    check_group.add_argument(
        "--check-host-preflight",
        action="store_true",
        help="Run local host storage checks plus the nested child-agent smoke test.",
    )
    parser.add_argument("--prompt-file", help="Prompt markdown file to execute.")
    parser.add_argument("--input-json", help="Structured JSON input file for the prompt.")
    parser.add_argument("--output-json", help="Optional path for the parsed JSON output.")
    parser.add_argument(
        "--preset",
        choices=sorted(LOCAL_CODEX_PRESETS),
        help="Optional checked-in local child-task preset.",
    )
    parser.add_argument("--model", help="Optional explicit model for the local child task.")
    parser.add_argument(
        "--fallback-models",
        help="Optional comma-separated fallback models to try when the primary model fails or is rate-limited.",
    )
    parser.add_argument("--profile", help="Optional Codex profile for the local child task.")
    parser.add_argument(
        "--reasoning-effort",
        default=None,
        help=(
            "Reasoning effort override for the local child task. Defaults to the selected preset, "
            "or `medium` when no preset is supplied."
        ),
    )
    parser.add_argument(
        "--sandbox",
        default=None,
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode for the local child task.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="Timeout for one local child task.",
    )
    parser.add_argument(
        "--timeout-retries",
        type=int,
        default=None,
        help="How many times to retry a timed-out or transiently disconnected local child task.",
    )
    parser.add_argument(
        "--retry-timeout-multiplier",
        type=float,
        default=None,
        help="Multiplier applied to the timeout on each retry after a timeout.",
    )
    parser.add_argument(
        "--persist-session",
        action="store_true",
        help="Keep child sessions on disk instead of using --ephemeral.",
    )
    return parser


def check_local_exec(
    *,
    repo_root: Path,
    model: str | None,
    fallback_models: list[str] | None,
    profile: str | None,
    reasoning_effort: str | None,
    sandbox: str,
    timeout_seconds: int,
    timeout_retries: int,
    retry_timeout_multiplier: float,
    ephemeral: bool,
    preset_name: str | None = None,
) -> dict[str, Any]:
    response = run_local_codex_prompt(
        repo_root=repo_root,
        task_prompt='Return exactly this JSON object and nothing else: {"ok": true, "mode": "local_codex_exec"}',
        model=model,
        fallback_models=fallback_models,
        profile=profile,
        reasoning_effort=reasoning_effort,
        sandbox=sandbox,
        timeout_seconds=timeout_seconds,
        timeout_retries=timeout_retries,
        retry_timeout_multiplier=retry_timeout_multiplier,
        ephemeral=ephemeral,
        trace_base=None,
        execution_metadata=None,
    )
    payload = parse_json_from_text(response)
    if payload != SMOKE_RESPONSE:
        raise LocalCodexExecutorError(
            f"Unexpected local Codex smoke response: expected {json.dumps(SMOKE_RESPONSE, ensure_ascii=False)}, got {json.dumps(payload, ensure_ascii=False)}"
        )
    return {
        "ready": True,
        "mode": "local_codex_exec",
        "repo_root": str(repo_root),
        "preset": preset_name,
        "sandbox": sandbox,
        "model": model,
        "fallback_models": fallback_models or [],
        "profile": profile,
        "reasoning_effort": reasoning_effort,
        "timeout_seconds": timeout_seconds,
        "timeout_retries": timeout_retries,
        "retry_timeout_multiplier": retry_timeout_multiplier,
        "ephemeral": ephemeral,
    }


def check_local_host_preflight(
    *,
    repo_root: Path,
    model: str | None,
    fallback_models: list[str] | None,
    profile: str | None,
    reasoning_effort: str | None,
    sandbox: str,
    timeout_seconds: int,
    timeout_retries: int,
    retry_timeout_multiplier: float,
    ephemeral: bool,
    preset_name: str | None = None,
) -> dict[str, Any]:
    codex_path = shutil.which("codex")
    if not codex_path:
        raise LocalCodexExecutorError("Could not find `codex` on PATH.")

    storage = inspect_local_codex_storage()
    required_ready = all(bool(item.get("ready")) for item in storage["required_targets"])
    smoke: dict[str, Any]
    if required_ready:
        smoke = check_local_exec(
            repo_root=repo_root,
            model=model,
            fallback_models=fallback_models,
            profile=profile,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
            timeout_seconds=timeout_seconds,
            timeout_retries=timeout_retries,
            retry_timeout_multiplier=retry_timeout_multiplier,
            ephemeral=ephemeral,
            preset_name=preset_name,
        )
    else:
        smoke = {
            "ready": False,
            "mode": "local_codex_exec",
            "skipped": True,
            "reason": "Skipped because required local Codex host storage checks failed.",
        }

    warnings = build_storage_warnings(storage=storage)
    return {
        "ready": required_ready and bool(smoke.get("ready")),
        "mode": "local_codex_host_preflight",
        "repo_root": str(repo_root),
        "codex_binary": codex_path,
        "codex_home": str(CODEX_HOME),
        "preset": preset_name,
        "model": model,
        "fallback_models": fallback_models or [],
        "profile": profile,
        "reasoning_effort": reasoning_effort,
        "sandbox": sandbox,
        "timeout_seconds": timeout_seconds,
        "timeout_retries": timeout_retries,
        "retry_timeout_multiplier": retry_timeout_multiplier,
        "ephemeral": ephemeral,
        "storage": storage,
        "smoke": smoke,
        "warnings": warnings,
    }


def inspect_local_codex_storage() -> dict[str, Any]:
    required_targets = [
        inspect_directory_target(CODEX_HOME, label="codex_home", required=True),
        inspect_directory_target(CODEX_HOME / "sessions", label="sessions_dir", required=True),
    ]
    recommended_targets = [
        inspect_file_target(CODEX_HOME / "session_index.jsonl", label="session_index", required=False),
        inspect_directory_target(CODEX_HOME / "sqlite", label="sqlite_dir", required=False),
    ]
    state_databases = inspect_glob_targets(CODEX_HOME, "state_*.sqlite", label_prefix="state_db")
    log_databases = inspect_glob_targets(CODEX_HOME, "logs_*.sqlite", label_prefix="log_db")
    sqlite_databases = inspect_glob_targets(CODEX_HOME / "sqlite", "*.db", label_prefix="sqlite_db")
    return {
        "required_targets": required_targets,
        "recommended_targets": recommended_targets,
        "state_databases": state_databases,
        "log_databases": log_databases,
        "sqlite_databases": sqlite_databases,
    }


def inspect_directory_target(path: Path, *, label: str, required: bool) -> dict[str, Any]:
    info = {
        "label": label,
        "path": str(path),
        "target_type": "directory",
        "required": required,
        "exists": path.exists(),
    }
    if path.exists():
        info["is_directory"] = path.is_dir()
        if not path.is_dir():
            info["ready"] = False
            info["status"] = "not_a_directory"
            return info
        info["status"] = "present"
        info["readable"] = os.access(path, os.R_OK | os.X_OK)
        info["writable"] = os.access(path, os.W_OK | os.X_OK)
        probe = probe_directory_write(path)
        info.update(probe)
        info["ready"] = bool(probe["ready"])
        return info

    parent = path.parent
    info["status"] = "missing"
    info["parent"] = str(parent)
    probe = probe_directory_write(parent)
    info["parent_probe"] = probe
    info["ready"] = bool(probe["ready"])
    if info["ready"]:
        info["status"] = "missing_but_parent_writable"
    else:
        info["status"] = "missing_and_parent_not_writable"
    return info


def inspect_file_target(path: Path, *, label: str, required: bool) -> dict[str, Any]:
    info = {
        "label": label,
        "path": str(path),
        "target_type": "file",
        "required": required,
        "exists": path.exists(),
    }
    if path.exists():
        info["is_file"] = path.is_file()
        if not path.is_file():
            info["ready"] = False
            info["status"] = "not_a_file"
            return info
        info["status"] = "present"
        info["readable"] = os.access(path, os.R_OK)
        info["writable"] = os.access(path, os.W_OK)
        info["ready"] = bool(info["writable"])
        return info

    parent = path.parent
    info["status"] = "missing"
    info["parent"] = str(parent)
    probe = probe_directory_write(parent)
    info["parent_probe"] = probe
    info["ready"] = bool(probe["ready"])
    if info["ready"]:
        info["status"] = "missing_but_parent_writable"
    else:
        info["status"] = "missing_and_parent_not_writable"
    return info


def inspect_glob_targets(base_dir: Path, pattern: str, *, label_prefix: str) -> list[dict[str, Any]]:
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for index, path in enumerate(sorted(base_dir.glob(pattern)), start=1):
        if not path.is_file():
            continue
        entries.append(
            {
                "label": f"{label_prefix}_{index}",
                "path": str(path),
                "target_type": "file",
                "required": False,
                "exists": True,
                "status": "present",
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK),
                "ready": bool(os.access(path, os.W_OK)),
            }
        )
    return entries


def probe_directory_write(path: Path) -> dict[str, Any]:
    info = {
        "probe_dir": str(path),
        "ready": False,
    }
    if not path.exists():
        info["status"] = "missing"
        return info
    if not path.is_dir():
        info["status"] = "not_a_directory"
        return info

    probe_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path,
            prefix=HOST_PREFLIGHT_PROBE_PREFIX,
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write("ok\n")
            probe_path = Path(handle.name)
    except OSError as exc:
        info["status"] = "write_probe_failed"
        info["error"] = str(exc)
        return info
    finally:
        if probe_path is not None and probe_path.exists():
            probe_path.unlink(missing_ok=True)

    info["status"] = "write_probe_ok"
    info["ready"] = True
    return info


def build_storage_warnings(*, storage: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for item in storage["recommended_targets"]:
        if not item.get("ready"):
            warnings.append(f"Recommended local Codex target not ready: {item['label']} -> {item['status']}")
    for category, label in (
        ("state_databases", "state database"),
        ("log_databases", "log database"),
        ("sqlite_databases", "sqlite database"),
    ):
        entries = storage[category]
        if not entries:
            warnings.append(f"No existing local Codex {label} files were discovered; child tasks may still work if Codex creates them on demand.")
            continue
        for item in entries:
            if not item.get("ready"):
                warnings.append(f"Existing local Codex {label} is not writable: {item['path']}")
    return warnings


def call_local_codex(
    *,
    prompt_path: Path,
    prompt_text: str,
    prompt_input: dict[str, Any],
    repo_root: Path,
    model: str | None,
    fallback_models: list[str] | None,
    profile: str | None,
    reasoning_effort: str | None,
    sandbox: str,
    timeout_seconds: int,
    timeout_retries: int,
    retry_timeout_multiplier: float,
    ephemeral: bool,
    trace_base: Path | None = None,
    execution_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = run_local_codex_prompt(
        repo_root=repo_root,
        task_prompt=build_task_prompt(prompt_path=prompt_path, prompt_text=prompt_text, prompt_input=prompt_input),
        model=model,
        fallback_models=fallback_models,
        profile=profile,
        reasoning_effort=reasoning_effort,
        sandbox=sandbox,
        timeout_seconds=timeout_seconds,
        timeout_retries=timeout_retries,
        retry_timeout_multiplier=retry_timeout_multiplier,
        ephemeral=ephemeral,
        trace_base=trace_base,
        execution_metadata=execution_metadata,
    )
    repaired_response = repair_runtime_json_text(response)
    if repaired_response is None:
        raise LocalCodexExecutorError(
            "Could not repair local Codex JSON response." + build_trace_hint(trace_base),
            details=build_local_codex_error_details(
                failure_category="invalid_json_output",
                trace_base=trace_base,
                response_excerpt=build_text_excerpt(response),
            ),
        )
    try:
        payload = parse_json_from_text(repaired_response)
    except (json.JSONDecodeError, ValueError) as exc:
        raise LocalCodexExecutorError(
            "local codex exec returned a non-parseable JSON object." + build_trace_hint(trace_base),
            details=build_local_codex_error_details(
                failure_category="invalid_json_output",
                trace_base=trace_base,
                response_excerpt=build_text_excerpt(repaired_response),
            ),
        ) from exc
    return normalize_prompt_output(prompt_path=prompt_path, prompt_input=prompt_input, payload=payload)


def build_task_prompt(*, prompt_path: Path, prompt_text: str, prompt_input: dict[str, Any]) -> str:
    try:
        relative_prompt_path = prompt_path.relative_to(REPO_ROOT)
    except ValueError:
        relative_prompt_path = prompt_path
    artifact_contract = build_artifact_contract(prompt_path=prompt_path, prompt_input=prompt_input)
    return (
        "You are a local Codex child agent executing one checked-in round-table prompt.\n"
        "The full checked-in prompt contract is pasted below verbatim. Treat it as the primary and self-contained task contract.\n"
        "Do not open the prompt's source reference files just because they are listed as source refs.\n"
        "Do not inspect any repository file unless this wrapper explicitly says you may. For this task, you should assume the pasted prompt and JSON input are sufficient.\n"
        "Do not browse the web.\n"
        "Return exactly one JSON object and nothing else. No markdown fences. No commentary.\n\n"
        f"Prompt path: {relative_prompt_path}\n\n"
        "Full prompt contract:\n"
        "```markdown\n"
        f"{prompt_text.strip()}\n"
        "```\n\n"
        "Structured input:\n"
        "```json\n"
        f"{json.dumps(prompt_input, ensure_ascii=False, indent=2)}\n"
        "```"
        f"{artifact_contract}"
    )


def build_artifact_contract(*, prompt_path: Path, prompt_input: dict[str, Any]) -> str:
    if prompt_path.name == "debate-reviewer.md":
        return build_debate_reviewer_artifact_contract(prompt_input=prompt_input)
    if prompt_path.name == "debate-followup.md":
        return build_debate_followup_artifact_contract(prompt_input=prompt_input)
    if prompt_path.name != "debate-roundtable.md":
        return ""

    participants = prompt_input.get("participants")
    speaker_order = prompt_input.get("speaker_order")
    prompt_inputs = prompt_input.get("prompt_inputs")
    if not (isinstance(participants, list) and isinstance(speaker_order, list)):
        return ""
    quick_mode = bool(prompt_inputs.get("quick_mode")) if isinstance(prompt_inputs, dict) else False

    participant_lines = []
    for item in participants:
        if not isinstance(item, dict):
            continue
        participant_lines.append(
            f'- agent_id="{item.get("agent_id")}", short_name="{item.get("short_name")}", responsibility="{item.get("responsibility")}"'
        )

    return (
        "\n\nRuntime artifact contract:\n"
        "Do not return step1-step8 meeting notes.\n"
        "Return exactly one final runtime artifact JSON object compatible with `debate_roundtable_record`.\n"
        "Required top-level fields and values:\n"
        '- `schema_version`: `"v0.1"`\n'
        '- `mode`: `"debate_roundtable_record"`\n'
        '- `source_kind`: `"room_handoff"`\n'
        f'- `debate_id`: `{prompt_input.get("debate_id")}`\n'
        f'- `source_room_id`: `{prompt_input.get("source_room_id")}`\n'
        f'- `primary_type`: `{prompt_input.get("primary_type")}`\n'
        f'- `secondary_type`: `{prompt_input.get("secondary_type")}`\n'
        f'- `quick_mode`: `{str(quick_mode).lower()}`\n'
        "- `participants`: must match exactly this set of participants:\n"
        f'{chr(10).join(participant_lines)}\n'
        f'- `speaker_order`: must equal `{json.dumps(speaker_order, ensure_ascii=False)}`\n'
        "- `agent_outputs`: exactly one object per speaker with keys "
        "`agent_id`, `role_duty`, `core_conclusion`, `evidence`, `biggest_problem`, "
        "`opposed_misjudgment`, `concrete_recommendation`, `confidence`, `uncertainties`\n"
        "- `moderator_summary`: keys "
        "`topic_restatement`, `participants_and_roles`, `consensus_points`, `core_conflicts`, "
        "`hidden_assumptions`, `preliminary_recommendation`, `review_focus`\n"
        "- `evidence_buckets`: keys `facts`, `inferences`, `uncertainties`, `recommendations`\n"
        "- `review_boundaries`: exactly "
        '{"conversation_log_reviewable": false, "review_only_visible_outputs": true, "followup_cap": 1}\n'
        "- `review_status`: exactly "
        f'{{"review_required": {str(not quick_mode).lower()}, "followup_allowed": {str(not quick_mode).lower()}, "max_followup_rounds": 1}}\n'
        "Before responding, internally verify that the JSON parses and that all required top-level fields are present.\n"
    )


def build_debate_reviewer_artifact_contract(*, prompt_input: dict[str, Any]) -> str:
    review_packet = prompt_input.get("review_packet")
    if not isinstance(review_packet, dict):
        return ""
    participant_ids = [
        item.get("agent_id")
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    ]
    scenario = prompt_input.get("scenario")
    followup_round = prompt_input.get("followup_round", 0)
    scenario_rule = ""
    if scenario == "reject_followup" and followup_round == 0:
        scenario_rule = "- Because this is the initial `reject_followup` validation round, `allow_final_decision` must be `false` and `required_followups` must be non-empty.\n"
    elif scenario == "reject_followup" and followup_round == 1:
        scenario_rule = (
            "- This is the rereview round after the only allowed followup. The result must be terminal.\n"
            "- Approve only if the followup resolves the requested gaps.\n"
            "- If the gaps are still unresolved, `allow_final_decision` must be `false` and `required_followups` must be an empty list because no further followup rounds are allowed.\n"
        )
    return (
        "\n\nRuntime artifact contract:\n"
        "Do not return the human-oriented 8-item review memo.\n"
        "Return exactly one final runtime artifact JSON object compatible with `debate_review_result`.\n"
        "Required top-level fields and values:\n"
        '- `schema_version`: `"v0.1"`\n'
        '- `mode`: `"debate_review_result"`\n'
        f'- `source_kind`: `{review_packet.get("source_kind")}`\n'
        f'- `source_room_id`: `{review_packet.get("source_room_id")}`\n'
        f'- `topic_restatement`: `{review_packet.get("topic_restatement")}`\n'
        f'- `quick_mode`: `{str(bool(review_packet.get("quick_mode"))).lower()}`\n'
        "- `review_applicable`: boolean\n"
        "- `overall_score`: integer 1-10\n"
        f'- `best_agent`: one of `{json.dumps(participant_ids, ensure_ascii=False)}`\n'
        f'- `weak_agents`: zero or more ids from `{json.dumps(participant_ids, ensure_ascii=False)}`\n'
        "- `evidence_gaps`, `logic_gaps`, `overlooked_issues`, `severe_red_flags`: string lists\n"
        "- `allow_final_decision`: boolean\n"
        "- `required_followups`: list of `{agent_id, needs}` objects; when allow=true this must be empty\n"
        "- `rationale`: non-empty string\n"
        f"{scenario_rule}"
        "Before responding, internally verify that the JSON parses and that agent references use canonical ids, not display names.\n"
    )


def build_debate_followup_artifact_contract(*, prompt_input: dict[str, Any]) -> str:
    review_result = prompt_input.get("review_result")
    if not isinstance(review_result, dict):
        return ""
    required_followups = review_result.get("required_followups")
    return (
        "\n\nRuntime artifact contract:\n"
        "Do not return the human-oriented followup memo.\n"
        "Return exactly one final runtime artifact JSON object compatible with `debate_followup_record`.\n"
        "Required top-level fields and values:\n"
        '- `schema_version`: `"v0.1"`\n'
        '- `mode`: `"debate_followup_record"`\n'
        f'- `source_kind`: `{prompt_input.get("review_packet", {}).get("source_kind")}`\n'
        f'- `debate_id`: `{prompt_input.get("debate_id")}`\n'
        f'- `source_room_id`: `{prompt_input.get("source_room_id")}`\n'
        f'- `topic_restatement`: `{prompt_input.get("review_packet", {}).get("topic_restatement")}`\n'
        "- `quick_mode`: false\n"
        "- `followup_round`: 1\n"
        f'- `required_followups`: must mirror reviewer targets exactly: `{json.dumps(required_followups, ensure_ascii=False)}`\n'
        "- `agent_followups`: one object per requested debate participant with keys `agent_id`, `role_duty`, `needs`, `supplemental_points`, `updated_recommendation`, `remaining_uncertainties`\n"
        "- `moderator_followup`: include when moderator was requested; keys `needs`, `added_or_corrected_consensus`, `added_or_corrected_conflicts`, `facts`, `inferences`, `updated_preliminary_recommendation`, `updated_stop_conditions`, `remaining_uncertainties`\n"
        '- `rereview_status`: exactly `{"rereview_required": true, "max_followup_rounds": 1, "return_to_reviewer": true}`\n'
        "Before responding, internally verify that the JSON parses and that followup targets use canonical ids, not display names.\n"
    )


def run_local_codex_prompt(
    *,
    repo_root: Path,
    task_prompt: str,
    model: str | None,
    fallback_models: list[str] | None,
    profile: str | None,
    reasoning_effort: str | None,
    sandbox: str,
    timeout_seconds: int,
    timeout_retries: int,
    retry_timeout_multiplier: float,
    ephemeral: bool,
    trace_base: Path | None,
    execution_metadata: dict[str, Any] | None,
) -> str:
    codex_path = shutil.which("codex")
    if not codex_path:
        raise LocalCodexExecutorError("Could not find `codex` on PATH.")
    model_candidates = build_model_candidates(model=model, fallback_models=fallback_models)
    prompt_started_monotonic = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="round-table-local-codex-") as temp_dir:
        trace_paths = build_trace_paths(trace_base=trace_base, temp_dir=Path(temp_dir))
        output_path = trace_paths["last_message"] or (Path(temp_dir) / "last-message.txt")
        stdout_path = trace_paths["stdout_jsonl"]
        stderr_path = trace_paths["stderr"]
        prompt_path = trace_paths["task_prompt"]
        command_path = trace_paths["command"]
        trace_manifest_path = trace_paths["trace_manifest"]
        trace_manifest = {
            "schema_version": "v0.1",
            "mode": "local_codex_child_trace",
            "repo_root": str(repo_root),
            "trace_base": str(trace_base) if trace_base is not None else None,
            "codex_binary": codex_path,
            "artifacts": serialize_trace_paths(trace_paths),
            "execution": {
                "model": model,
                "fallback_models": fallback_models or [],
                "model_candidates": model_candidates,
                "profile": profile,
                "reasoning_effort": reasoning_effort,
                "sandbox": sandbox,
                "timeout_seconds": timeout_seconds,
                "timeout_retries": timeout_retries,
                "retry_timeout_multiplier": retry_timeout_multiplier,
                "ephemeral": ephemeral,
            },
            "task_strategy": execution_metadata or {},
            "attempts": [],
            "final_status": "started",
            "started_at": utc_now_iso(),
        }

        if prompt_path is not None:
            prompt_path.write_text(task_prompt, encoding="utf-8")
        write_trace_manifest(trace_manifest_path, trace_manifest)
        attempts: list[dict[str, Any]] = []
        last_timeout_error: LocalCodexExecutorError | None = None
        last_failure_message: str | None = None
        last_failure_details: dict[str, Any] | None = None
        for model_index, candidate_model in enumerate(model_candidates):
            cmd = [
                codex_path,
                "exec",
                "--color",
                "never",
                "--json",
                "--skip-git-repo-check",
                "--sandbox",
                sandbox,
                "--ignore-rules",
                "--output-last-message",
                str(output_path),
            ]
            if ephemeral:
                cmd.append("--ephemeral")
            if candidate_model:
                cmd.extend(["--model", candidate_model])
            if profile:
                cmd.extend(["--profile", profile])
            if reasoning_effort:
                cmd.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])

            for attempt_index in range(timeout_retries + 1):
                attempt_timeout = int(round(timeout_seconds * (retry_timeout_multiplier ** attempt_index)))
                attempt_timeout = max(attempt_timeout, timeout_seconds)
                attempt_started_monotonic = time.monotonic()
                attempts.append(
                    {
                        "model_candidate_index": model_index + 1,
                        "model": candidate_model,
                        "attempt": attempt_index + 1,
                        "timeout_seconds": attempt_timeout,
                    }
                )
                trace_attempt = {
                    "model_candidate_index": model_index + 1,
                    "model": candidate_model,
                    "attempt": attempt_index + 1,
                    "timeout_seconds": attempt_timeout,
                    "status": "started",
                    "started_at": utc_now_iso(),
                }
                trace_manifest["attempts"].append(trace_attempt)
                if command_path is not None:
                    command_path.write_text(
                        json.dumps(
                            {
                                "cmd": cmd,
                                "cwd": str(repo_root),
                                "timeout_seconds": timeout_seconds,
                                "timeout_retries": timeout_retries,
                                "retry_timeout_multiplier": retry_timeout_multiplier,
                                "fallback_models": fallback_models or [],
                                "reasoning_effort": reasoning_effort,
                                "attempts": attempts,
                                "ephemeral": ephemeral,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                write_trace_manifest(trace_manifest_path, trace_manifest)
                try:
                    completed = subprocess.run(
                        cmd,
                        input=task_prompt,
                        text=True,
                        capture_output=True,
                        cwd=temp_dir,
                        timeout=attempt_timeout,
                        check=False,
                    )
                except subprocess.TimeoutExpired as exc:
                    write_trace_text(stdout_path, exc.stdout)
                    write_trace_text(stderr_path, exc.stderr)
                    timeout_message = f"local codex exec timed out after {attempt_timeout}s on attempt {attempt_index + 1}"
                    timeout_details = build_local_codex_error_details(
                        failure_category="timeout",
                        trace_base=trace_base,
                        model=candidate_model,
                        attempt=attempt_index + 1,
                        timeout_seconds=attempt_timeout,
                        retryable=attempt_index < timeout_retries,
                    )
                    trace_attempt.update(
                        {
                            "status": "timed_out",
                            "failure_category": timeout_details["failure_category"],
                            "error": timeout_message,
                            "retryable": timeout_details.get("retryable", False),
                            "finished_at": utc_now_iso(),
                            "duration_seconds": round(time.monotonic() - attempt_started_monotonic, 3),
                        }
                    )
                    trace_manifest["final_status"] = "retrying_after_timeout" if attempt_index < timeout_retries else "failed"
                    trace_manifest["last_failure"] = timeout_details
                    if attempt_index >= timeout_retries:
                        set_trace_manifest_finished(
                            trace_manifest,
                            final_status="failed",
                            started_monotonic=prompt_started_monotonic,
                        )
                    write_trace_manifest(trace_manifest_path, trace_manifest)
                    if attempt_index >= timeout_retries:
                        last_timeout_error = LocalCodexExecutorError(
                            timeout_message + build_trace_hint(trace_base),
                            details=timeout_details,
                        )
                        break
                    continue

                write_trace_text(stdout_path, completed.stdout)
                write_trace_text(stderr_path, completed.stderr)
                if completed.returncode == 0:
                    response_text, response_source = read_child_response_text(output_path=output_path, stdout_jsonl=completed.stdout)
                    trace_attempt.update(
                        {
                            "status": "completed",
                            "returncode": completed.returncode,
                            "response_source": response_source,
                            "finished_at": utc_now_iso(),
                            "duration_seconds": round(time.monotonic() - attempt_started_monotonic, 3),
                        }
                    )
                    if response_text is None:
                        missing_message = "local codex exec completed but did not yield a recoverable last message."
                        missing_details = build_local_codex_error_details(
                            failure_category="missing_child_message",
                            trace_base=trace_base,
                            model=candidate_model,
                            attempt=attempt_index + 1,
                            response_source=response_source,
                        )
                        trace_attempt.update(
                            {
                                "status": "failed",
                                "failure_category": missing_details["failure_category"],
                                "error": missing_message,
                                "finished_at": utc_now_iso(),
                                "duration_seconds": round(time.monotonic() - attempt_started_monotonic, 3),
                            }
                        )
                        trace_manifest["last_failure"] = missing_details
                        set_trace_manifest_finished(
                            trace_manifest,
                            final_status="failed",
                            started_monotonic=prompt_started_monotonic,
                        )
                        write_trace_manifest(trace_manifest_path, trace_manifest)
                        raise LocalCodexExecutorError(
                            missing_message + build_trace_hint(trace_base),
                            details=missing_details,
                        )
                    existing_output = output_path.read_text(encoding="utf-8") if output_path.exists() else None
                    if existing_output != response_text:
                        output_path.write_text(response_text, encoding="utf-8")
                    trace_manifest["final_model"] = candidate_model
                    trace_manifest["response_source"] = response_source
                    set_trace_manifest_finished(
                        trace_manifest,
                        final_status="child_task_succeeded",
                        started_monotonic=prompt_started_monotonic,
                    )
                    write_trace_manifest(trace_manifest_path, trace_manifest)
                    return response_text

                failure_info = classify_command_failure(stdout=completed.stdout, stderr=completed.stderr, returncode=completed.returncode)
                last_failure_message = (
                    "local codex exec failed: "
                    + failure_info["summary"]
                    + build_trace_hint(trace_base)
                )
                last_failure_details = build_local_codex_error_details(
                    failure_category=failure_info["failure_category"],
                    trace_base=trace_base,
                    model=candidate_model,
                    attempt=attempt_index + 1,
                    returncode=completed.returncode,
                    retryable=failure_info["retryable"],
                    try_next_model=failure_info["try_next_model"],
                    summary=failure_info["summary"],
                )
                trace_attempt.update(
                    {
                        "status": "failed",
                        "returncode": completed.returncode,
                        "failure_category": failure_info["failure_category"],
                        "summary": failure_info["summary"],
                        "retryable": failure_info["retryable"],
                        "try_next_model": failure_info["try_next_model"],
                        "finished_at": utc_now_iso(),
                        "duration_seconds": round(time.monotonic() - attempt_started_monotonic, 3),
                    }
                )
                trace_manifest["last_failure"] = last_failure_details
                if should_retry_transient_failure(stdout=completed.stdout, stderr=completed.stderr) and attempt_index < timeout_retries:
                    trace_attempt["retry_decision"] = "retry_same_model"
                    trace_manifest["final_status"] = "retrying_after_failure"
                    write_trace_manifest(trace_manifest_path, trace_manifest)
                    continue
                if should_try_next_model(stdout=completed.stdout, stderr=completed.stderr) and model_index + 1 < len(model_candidates):
                    trace_attempt["retry_decision"] = "switch_model"
                    trace_manifest["final_status"] = "switching_model"
                    write_trace_manifest(trace_manifest_path, trace_manifest)
                    break
                set_trace_manifest_finished(
                    trace_manifest,
                    final_status="failed",
                    started_monotonic=prompt_started_monotonic,
                )
                write_trace_manifest(trace_manifest_path, trace_manifest)
                raise LocalCodexExecutorError(last_failure_message, details=last_failure_details)

            if last_timeout_error is not None and model_index + 1 < len(model_candidates):
                last_timeout_error = None
                continue
            if last_timeout_error is not None:
                raise last_timeout_error
        if last_failure_message:
            raise LocalCodexExecutorError(last_failure_message, details=last_failure_details)
        generic_details = build_local_codex_error_details(
            failure_category="command_failed",
            trace_base=trace_base,
        )
        trace_manifest["last_failure"] = generic_details
        set_trace_manifest_finished(
            trace_manifest,
            final_status="failed",
            started_monotonic=prompt_started_monotonic,
        )
        write_trace_manifest(trace_manifest_path, trace_manifest)
        raise LocalCodexExecutorError(
            "local codex exec failed without a usable attempt result." + build_trace_hint(trace_base),
            details=generic_details,
        )


def summarize_command_failure(stdout: str, stderr: str, returncode: int) -> str:
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip())
    condensed = " ".join(combined.split())
    if len(condensed) > 400:
        condensed = condensed[:400] + "..."
    return f"exit={returncode}; output={condensed or '信息缺失'}"


def read_child_response_text(*, output_path: Path, stdout_jsonl: str) -> tuple[str | None, str | None]:
    raw_last_message = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    repaired_raw = repair_runtime_json_text(raw_last_message)
    if repaired_raw is not None:
        source = "output_last_message" if repaired_raw == raw_last_message else "output_last_message_repaired"
        return repaired_raw, source

    recovered_from_stdout = extract_last_agent_message_from_stdout_jsonl(stdout_jsonl)
    repaired_stdout = repair_runtime_json_text(recovered_from_stdout)
    if repaired_stdout is not None:
        source = "stdout_agent_message" if repaired_stdout == recovered_from_stdout else "stdout_agent_message_repaired"
        return repaired_stdout, source

    if raw_last_message and recovered_from_stdout and len(recovered_from_stdout) > len(raw_last_message):
        return recovered_from_stdout, "stdout_agent_message_raw_fallback"
    if raw_last_message:
        return raw_last_message, "output_last_message_raw_fallback"
    if recovered_from_stdout:
        return recovered_from_stdout, "stdout_agent_message_raw_only"
    return None, None


def is_valid_runtime_json_text(text: str | None) -> bool:
    return repair_runtime_json_text(text) is not None


def repair_runtime_json_text(text: str | None) -> str | None:
    if not text:
        return None
    normalized = repair_missing_string_quotes_before_delimiters(text)
    normalized_tail = repair_truncated_json_tail(repair_top_level_json_closers(normalized))
    normalized_eof = repair_unterminated_json_eof(normalized_tail)
    candidates = [
        text,
        normalized,
        normalized_tail,
        normalized_eof,
    ]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parse_json_from_text(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        return candidate
    return None


def extract_last_agent_message_from_stdout_jsonl(stdout_jsonl: str) -> str | None:
    last_message: str | None = None
    for line in stdout_jsonl.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        if item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            last_message = text
    return last_message


def parse_model_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_execution_settings(
    *,
    preset_name: str | None,
    model: str | None,
    fallback_models: list[str] | None,
    profile: str | None,
    reasoning_effort: str | None,
    sandbox: str | None,
    timeout_seconds: int | None,
    timeout_retries: int | None,
    retry_timeout_multiplier: float | None,
    persist_session: bool,
) -> dict[str, Any]:
    resolved = {
        "preset": preset_name,
        "model": None,
        "fallback_models": [],
        "profile": None,
        "reasoning_effort": DEFAULT_REASONING_EFFORT,
        "sandbox": DEFAULT_SANDBOX,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "timeout_retries": DEFAULT_TIMEOUT_RETRIES,
        "retry_timeout_multiplier": DEFAULT_RETRY_TIMEOUT_MULTIPLIER,
        "ephemeral": not persist_session,
    }
    if preset_name:
        preset = LOCAL_CODEX_PRESETS.get(preset_name)
        if preset is None:
            raise ValueError(f"Unknown local Codex preset: {preset_name}")
        resolved.update(
            {
                "model": preset["model"],
                "fallback_models": list(preset["fallback_models"]),
                "profile": preset["profile"],
                "reasoning_effort": preset["reasoning_effort"],
                "sandbox": preset["sandbox"],
                "timeout_seconds": preset["timeout_seconds"],
                "timeout_retries": preset["timeout_retries"],
                "retry_timeout_multiplier": preset["retry_timeout_multiplier"],
                "ephemeral": not preset.get("persist_session", False),
            }
        )
    if model is not None:
        resolved["model"] = model
    if fallback_models is not None:
        resolved["fallback_models"] = list(fallback_models)
    if profile is not None:
        resolved["profile"] = profile
    if reasoning_effort is not None:
        resolved["reasoning_effort"] = reasoning_effort
    if sandbox is not None:
        resolved["sandbox"] = sandbox
    if timeout_seconds is not None:
        resolved["timeout_seconds"] = timeout_seconds
    if timeout_retries is not None:
        resolved["timeout_retries"] = timeout_retries
    if retry_timeout_multiplier is not None:
        resolved["retry_timeout_multiplier"] = retry_timeout_multiplier
    if persist_session:
        resolved["ephemeral"] = False
    return resolved


def resolve_task_execution_settings(
    *,
    base_settings: dict[str, Any],
    preset_name: str | None,
    prompt_path: Path,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    resolved = {
        "preset": base_settings.get("preset"),
        "model": base_settings.get("model"),
        "fallback_models": list(base_settings.get("fallback_models") or []),
        "profile": base_settings.get("profile"),
        "reasoning_effort": base_settings.get("reasoning_effort"),
        "sandbox": base_settings.get("sandbox"),
        "timeout_seconds": base_settings.get("timeout_seconds"),
        "timeout_retries": base_settings.get("timeout_retries"),
        "retry_timeout_multiplier": base_settings.get("retry_timeout_multiplier"),
        "ephemeral": base_settings.get("ephemeral"),
    }
    policy_key = derive_step_policy_key(prompt_path=prompt_path, prompt_input=prompt_input)
    policy = get_step_policy(preset_name=preset_name, policy_key=policy_key)
    for field in STEP_POLICY_OVERRIDE_FIELDS:
        if field not in policy:
            continue
        value = policy[field]
        if field == "fallback_models":
            resolved[field] = list(value)
        else:
            resolved[field] = value
    resolved["task_policy_key"] = policy_key
    resolved["task_policy_applied"] = bool(policy)
    return resolved


def derive_step_policy_key(*, prompt_path: Path, prompt_input: dict[str, Any]) -> str | None:
    prompt_name = prompt_path.name
    mode = prompt_input.get("mode")
    if prompt_name == "room-selection.md":
        if mode == "room_full":
            return "room_full_selection"
        if mode == "room_turn":
            return "room_turn_selection"
    if prompt_name == "room-chat.md":
        return "room_chat"
    if prompt_name == "room-summary.md":
        return "room_summary"
    if prompt_name == "room-upgrade.md":
        return "room_upgrade"
    if prompt_name == "debate-roundtable.md":
        return "debate_roundtable"
    if prompt_name == "debate-followup.md":
        return "debate_followup"
    if prompt_name == "debate-reviewer.md":
        followup_round = parse_int(prompt_input.get("followup_round"), default=0)
        return "debate_reviewer_rereview" if followup_round > 0 else "debate_reviewer_initial"
    return None


def get_step_policy(*, preset_name: str | None, policy_key: str | None) -> dict[str, Any]:
    if not preset_name or not policy_key:
        return {}
    preset = LOCAL_CODEX_PRESETS.get(preset_name) or {}
    step_policies = preset.get("step_policies")
    if not isinstance(step_policies, dict):
        return {}
    policy = step_policies.get(policy_key)
    if not isinstance(policy, dict):
        return {}
    resolved: dict[str, Any] = {}
    for field in STEP_POLICY_OVERRIDE_FIELDS:
        if field not in policy:
            continue
        value = policy[field]
        resolved[field] = list(value) if field == "fallback_models" else value
    return resolved


def build_model_candidates(*, model: str | None, fallback_models: list[str] | None) -> list[str | None]:
    candidates: list[str | None] = [model]
    for item in fallback_models or []:
        if item == model:
            continue
        candidates.append(item)
    return candidates


def build_trace_paths(*, trace_base: Path | None, temp_dir: Path) -> dict[str, Path | None]:
    if trace_base is not None:
        trace_base.parent.mkdir(parents=True, exist_ok=True)
        return {
            "last_message": Path(f"{trace_base}.child-last-message.txt"),
            "stdout_jsonl": Path(f"{trace_base}.child-stdout.jsonl"),
            "stderr": Path(f"{trace_base}.child-stderr.txt"),
            "task_prompt": Path(f"{trace_base}.child-task-prompt.md"),
            "command": Path(f"{trace_base}.child-command.json"),
            "trace_manifest": Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"),
        }
    return {
        "last_message": temp_dir / "last-message.txt",
        "stdout_jsonl": None,
        "stderr": None,
        "task_prompt": None,
        "command": None,
        "trace_manifest": None,
    }


def serialize_trace_paths(paths: dict[str, Path | None]) -> dict[str, str]:
    return {key: str(path) for key, path in paths.items() if path is not None}


def write_trace_manifest(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    payload["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def set_trace_manifest_finished(
    payload: dict[str, Any],
    *,
    final_status: str,
    started_monotonic: float,
) -> None:
    payload["final_status"] = final_status
    payload["finished_at"] = utc_now_iso()
    payload["wall_time_seconds"] = round(max(time.monotonic() - started_monotonic, 0.0), 3)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_local_codex_error_details(
    *,
    failure_category: str,
    trace_base: Path | None,
    model: str | None = None,
    attempt: int | None = None,
    timeout_seconds: int | None = None,
    returncode: int | None = None,
    retryable: bool | None = None,
    try_next_model: bool | None = None,
    response_source: str | None = None,
    summary: str | None = None,
    response_excerpt: str | None = None,
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "failure_category": failure_category,
    }
    if trace_base is not None:
        details["trace_base"] = str(trace_base)
        details["trace_manifest"] = str(Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"))
    if model is not None:
        details["model"] = model
    if attempt is not None:
        details["attempt"] = attempt
    if timeout_seconds is not None:
        details["timeout_seconds"] = timeout_seconds
    if returncode is not None:
        details["returncode"] = returncode
    if retryable is not None:
        details["retryable"] = retryable
    if try_next_model is not None:
        details["try_next_model"] = try_next_model
    if response_source is not None:
        details["response_source"] = response_source
    if summary is not None:
        details["summary"] = summary
    if response_excerpt is not None:
        details["response_excerpt"] = response_excerpt
    return details


def serialize_local_codex_error(exc: Exception, *, trace_base: Path | None = None) -> dict[str, Any]:
    payload = {
        "error": str(exc),
        "error_type": type(exc).__name__,
    }
    if trace_base is not None:
        payload["trace_base"] = str(trace_base)
        payload["trace_manifest"] = str(Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"))
    if isinstance(exc, LocalCodexExecutorError) and exc.details:
        payload["failure_category"] = exc.details.get("failure_category")
        payload["local_codex"] = exc.details
        payload["trace_base"] = exc.details.get("trace_base", payload.get("trace_base"))
        payload["trace_manifest"] = exc.details.get("trace_manifest", payload.get("trace_manifest"))
    return payload


def classify_command_failure(*, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    summary = summarize_command_failure(stdout, stderr, returncode)
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip()).lower()
    retryable = should_retry_transient_failure(stdout=stdout, stderr=stderr)
    try_next_model = should_try_next_model(stdout=stdout, stderr=stderr)
    if retryable:
        failure_category = "transient_transport_failure"
    elif any(token in combined for token in ("permission denied", "operation not permitted", "sandbox", "write access", "not writable")):
        failure_category = "host_permission_or_sandbox_denied"
    elif any(token in combined for token in ("unknown model", "model not found", "invalid model", "unrecognized model")):
        failure_category = "invalid_model"
    elif try_next_model:
        failure_category = "rate_limit_or_model_overloaded"
    else:
        failure_category = "command_failed"
    return {
        "failure_category": failure_category,
        "summary": summary,
        "retryable": retryable,
        "try_next_model": try_next_model,
    }


def build_text_excerpt(text: str | None, *, limit: int = 280) -> str | None:
    if not text:
        return None
    condensed = " ".join(text.split())
    if len(condensed) <= limit:
        return condensed
    return condensed[:limit] + "..."


def parse_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def should_try_next_model(*, stdout: str, stderr: str) -> bool:
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip()).lower()
    retry_signals = [
        "usage limit",
        "switch to another model",
        "rate limit",
        "quota",
        "model overloaded",
        "try again later",
    ]
    return any(signal in combined for signal in retry_signals)


def should_retry_transient_failure(*, stdout: str, stderr: str) -> bool:
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip()).lower()
    retry_signals = [
        "stream disconnected before completion",
        "stream disconnected - retrying sampling request",
        "failed to lookup address information",
        "dns error",
        "could not resolve host",
        "failed to connect to websocket",
        "error sending request for url",
        "transport channel closed",
    ]
    return any(signal in combined for signal in retry_signals)


def normalize_prompt_output(*, prompt_path: Path, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    mode = prompt_input.get("mode")
    if mode == "debate_roundtable":
        return normalize_debate_roundtable_output(prompt_input=prompt_input, payload=payload)
    if mode == "debate_review":
        return normalize_debate_review_output(prompt_input=prompt_input, payload=payload)
    if mode == "debate_followup":
        return normalize_debate_followup_output(prompt_input=prompt_input, payload=payload)
    if prompt_path.name == "room-selection.md":
        return normalize_room_selection_output(prompt_input=prompt_input, payload=payload)
    if prompt_path.name == "room-upgrade.md":
        return normalize_room_upgrade_output(payload=payload)
    return payload


def normalize_room_selection_output(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    mode = prompt_input.get("mode")

    roster = normalized.get("roster")
    if isinstance(roster, list):
        normalized_roster = normalize_agent_reference_list(roster)
        if normalized_roster:
            normalized["roster"] = normalized_roster

    if mode == "room_turn":
        speakers = normalized.get("speakers")
        if isinstance(speakers, list):
            normalized_speakers = normalize_agent_reference_list(speakers)
            if normalized_speakers:
                normalized["speakers"] = normalized_speakers

    return normalized


def normalize_room_upgrade_output(*, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload

    handoff_packet = payload.get("handoff_packet")
    if not isinstance(handoff_packet, dict):
        return payload

    uncertainty_points = handoff_packet.get("field_10_uncertainty_points")
    if not (isinstance(uncertainty_points, list) and uncertainty_points and all(isinstance(item, dict) for item in uncertainty_points)):
        return payload

    normalized_points: list[str] = []
    for item in uncertainty_points:
        text = item.get("uncertainty_text") or item.get("text")
        if not text:
            continue
        speaker = item.get("agent_id") or item.get("agent")
        normalized_points.append(f"{speaker}: {text}" if speaker else str(text))

    normalized_handoff = dict(handoff_packet)
    normalized_handoff["field_10_uncertainty_points"] = normalized_points
    normalized_payload = dict(payload)
    normalized_payload["handoff_packet"] = normalized_handoff
    return normalized_payload


def normalize_debate_roundtable_output(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    if payload.get("schema_version") == "v0.1" and payload.get("mode") == "debate_roundtable_record":
        return enrich_debate_roundtable_record(prompt_input=prompt_input, payload=payload)

    steps = payload.get("steps")
    container = steps if isinstance(steps, dict) else payload
    final_resolution = container.get("step8_final_resolution") or container.get("step8_final_decision") or payload.get("final_resolution")
    step8 = container.get("step8")
    if not isinstance(final_resolution, dict) and isinstance(step8, dict):
        final_resolution = step8.get("final_resolution") or step8.get("final_decision") or step8.get("最终决议")

    step5 = container.get("step5") or container.get("step5_speeches") or container.get("step5_speaking_order")
    if isinstance(step5, dict):
        step5 = step5.get("speeches")
    step6 = container.get("step6") or container.get("step6_moderator_summary") or container.get("step6_host_summary")
    evidence = (
        payload.get("fact_inference_distinction")
        or payload.get("fact_inference_split")
        or payload.get("facts_inferences_uncertainties")
        or payload.get("distinction")
    )
    if not isinstance(evidence, dict) and isinstance(final_resolution, dict):
        evidence = final_resolution.get("事实_推断_不确定_建议")
        if not isinstance(evidence, dict):
            evidence = final_resolution.get("事实_推断_不确定项_建议")
        if not isinstance(evidence, dict):
            evidence = final_resolution.get("facts")
        if not isinstance(evidence, dict) and any(
            key in final_resolution for key in ("facts", "inferences", "uncertainties", "uncertainty", "suggestions", "建议")
        ):
            evidence = final_resolution
    if not isinstance(evidence, dict):
        if isinstance(step8, dict):
            nested_final = step8.get("final_resolution")
            if isinstance(nested_final, dict):
                evidence = nested_final.get("事实_推断_不确定_建议")
                if not isinstance(evidence, dict):
                    evidence = nested_final.get("事实_推断_不确定项_建议")
                if not isinstance(evidence, dict):
                    evidence = nested_final.get("facts")
            nested_final_cn = step8.get("最终决议")
            if not isinstance(evidence, dict) and isinstance(nested_final_cn, dict):
                evidence = nested_final_cn.get("事实_推断_不确定_建议")
                if not isinstance(evidence, dict):
                    evidence = nested_final_cn.get("事实_推断_不确定项_建议")
                if not isinstance(evidence, dict):
                    evidence = nested_final_cn.get("facts")
            nested_final_en = step8.get("final_decision")
            if not isinstance(evidence, dict) and isinstance(nested_final_en, dict):
                evidence = nested_final_en.get("facts")
                if not isinstance(evidence, dict) and any(
                    key in nested_final_en for key in ("facts", "inferences", "uncertainties", "uncertainty", "suggestions", "建议")
                ):
                    evidence = nested_final_en
    participants = prompt_input.get("participants")
    speaker_order = prompt_input.get("speaker_order")
    if not (
        isinstance(step5, list)
        and isinstance(step6, dict)
        and isinstance(evidence, dict)
        and isinstance(participants, list)
        and isinstance(speaker_order, list)
    ):
        return payload

    participant_map = {
        item.get("agent_id"): item
        for item in participants
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    if any(agent_id not in participant_map for agent_id in speaker_order):
        return payload

    agent_outputs: list[dict[str, Any]] = []
    for index, agent_id in enumerate(speaker_order):
        participant = participant_map[agent_id]
        item = step5[index] if index < len(step5) and isinstance(step5[index], dict) else {}
        agent_outputs.append(
            {
                "agent_id": agent_id,
                "role_duty": participant["responsibility"],
                "core_conclusion": first_non_empty_string(
                    item.get("核心结论"),
                    item.get("结论"),
                    item.get("key_conclusion"),
                    item.get("core_conclusion"),
                ),
                "evidence": ensure_string_list(item.get("判断依据") or item.get("依据") or item.get("evidence")),
                "biggest_problem": first_non_empty_string(
                    item.get("当前方案最大的一个问题"),
                    item.get("最大问题"),
                    item.get("main_issue"),
                    item.get("biggest_problem"),
                ),
                "opposed_misjudgment": first_non_empty_string(
                    item.get("我反对的一个常见误判"),
                    item.get("我反对的常见误判"),
                    item.get("常见误判"),
                    item.get("common_misjudgment"),
                    item.get("common_misjudgment_opposed"),
                    item.get("opposed_misjudgment"),
                ),
                "concrete_recommendation": stringify_recommendation(
                    item.get("我的具体建议"),
                    item.get("具体建议"),
                    item.get("建议"),
                    item.get("actionable_suggestion"),
                    item.get("specific_suggestion"),
                    item.get("concrete_recommendation"),
                ),
                "confidence": normalize_confidence_value(item.get("置信度") or item.get("confidence")),
                "uncertainties": ensure_string_list(item.get("不确定项") or item.get("uncertainties") or item.get("uncertainty")),
            }
        )

    prompt_inputs = prompt_input.get("prompt_inputs")
    quick_mode = bool(prompt_inputs.get("quick_mode")) if isinstance(prompt_inputs, dict) else False

    return {
        "schema_version": "v0.1",
        "mode": "debate_roundtable_record",
        "source_kind": "room_handoff",
        "debate_id": prompt_input.get("debate_id"),
        "source_room_id": prompt_input.get("source_room_id"),
        "topic_restatement": first_non_empty_string(
            step6.get("议题重述"),
            final_resolution.get("单一最终建议") if isinstance(final_resolution, dict) else None,
            payload.get("topic_restatement"),
            prompt_input.get("topic"),
        ),
        "primary_type": prompt_input.get("primary_type"),
        "secondary_type": prompt_input.get("secondary_type"),
        "quick_mode": quick_mode,
        "participants": [
            {
                "agent_id": item["agent_id"],
                "short_name": item["short_name"],
                "responsibility": item["responsibility"],
            }
            for item in participants
            if isinstance(item, dict)
        ],
        "speaker_order": list(speaker_order),
        "agent_outputs": agent_outputs,
        "moderator_summary": {
            "topic_restatement": first_non_empty_string(
                step6.get("议题重述"),
                step6.get("topic_restate"),
                step6.get("restated_issue"),
                prompt_input.get("topic"),
            ),
            "participants_and_roles": [
                {
                    "agent_id": item["agent_id"],
                    "responsibility": item["responsibility"],
                }
                for item in participants
                if isinstance(item, dict)
            ],
            "consensus_points": ensure_string_list(step6.get("共识点") or step6.get("consensus")),
            "core_conflicts": ensure_string_list(step6.get("核心分歧") or step6.get("core_divergence")),
            "hidden_assumptions": ensure_string_list(step6.get("隐含假设") or step6.get("implicit_assumptions")),
            "preliminary_recommendation": first_non_empty_string(
                step6.get("初步建议"),
                step6.get("建议"),
                step6.get("provisional_recommendation"),
                step6.get("preliminary_recommendation"),
                step6.get("preliminary_suggestion"),
            ),
            "review_focus": ensure_string_list(
                step6.get("需要审查Agent重点检查的地方")
                or step6.get("review_focus_points")
                or step6.get("review_points_for_reviewer")
                or step6.get("reviewer_check_focus")
                or step6.get("review_focus_for_reviewer")
            ),
        },
        "evidence_buckets": {
            "facts": ensure_string_list(evidence.get("事实") or evidence.get("facts") or evidence.get("列出的事实")),
            "inferences": ensure_string_list(evidence.get("推断") or evidence.get("inferences")),
            "uncertainties": ensure_string_list(evidence.get("不确定项") or evidence.get("uncertainties") or evidence.get("uncertainty")),
            "recommendations": ensure_string_list(
                evidence.get("建议") or evidence.get("recommendations") or evidence.get("suggestions")
            ),
        },
        "review_boundaries": {
            "conversation_log_reviewable": False,
            "review_only_visible_outputs": True,
            "followup_cap": 1,
        },
        "review_status": {
            "review_required": not quick_mode,
            "followup_allowed": not quick_mode,
            "max_followup_rounds": 1,
        },
    }


def normalize_debate_review_output(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    review_packet = prompt_input.get("review_packet")
    if not isinstance(review_packet, dict) or not isinstance(payload, dict):
        return payload
    if payload.get("schema_version") == "v0.1" and payload.get("mode") == "debate_review_result":
        return enrich_debate_review_result(prompt_input=prompt_input, payload=payload)

    participant_ids = [
        item.get("agent_id")
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    ]
    allow_final_decision = normalize_allow_decision(payload.get("是否允许进入最终决议"))
    normalized = {
        "schema_version": "v0.1",
        "mode": "debate_review_result",
        "source_kind": review_packet.get("source_kind"),
        "debate_id": prompt_input.get("debate_id"),
        "source_room_id": review_packet.get("source_room_id"),
        "topic_restatement": review_packet.get("topic_restatement"),
        "quick_mode": bool(review_packet.get("quick_mode")),
        "review_applicable": not bool(review_packet.get("quick_mode")),
        "overall_score": normalize_score(payload.get("本轮讨论总体评分")),
        "best_agent": resolve_agent_reference(payload.get("履职最好的 Agent"), participant_ids, review_packet),
        "weak_agents": normalize_agent_list(payload.get("偷懒或空泛的 Agent"), participant_ids, review_packet),
        "evidence_gaps": ensure_string_list_allow_empty(payload.get("缺证据的论点")),
        "logic_gaps": ensure_string_list_allow_empty(payload.get("逻辑跳跃点")),
        "overlooked_issues": ensure_string_list_allow_empty(payload.get("被忽略的关键问题")),
        "severe_red_flags": [],
        "allow_final_decision": allow_final_decision,
        "required_followups": [] if allow_final_decision else parse_required_followups(payload.get("如果不允许，需要补充什么"), participant_ids, review_packet),
        "rationale": first_non_empty_string(
            payload.get("审核依据"),
            "reviewer accepted the visible roundtable outputs for final decision." if allow_final_decision else "reviewer requires targeted followups before final decision.",
        ),
    }
    return enforce_review_scenario(prompt_input=prompt_input, review_packet=review_packet, payload=normalized)


def normalize_debate_followup_output(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    review_packet = prompt_input.get("review_packet")
    review_result = prompt_input.get("review_result")
    roundtable_record = prompt_input.get("roundtable_record")
    if not all(isinstance(item, dict) for item in (review_packet, review_result, roundtable_record)) or not isinstance(payload, dict):
        return payload
    if payload.get("schema_version") == "v0.1" and payload.get("mode") == "debate_followup_record":
        return enrich_debate_followup_record(prompt_input=prompt_input, payload=payload)

    participant_ids = [
        item.get("agent_id")
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    ]
    required_followups = review_result.get("required_followups") if isinstance(review_result.get("required_followups"), list) else []
    required_map = {
        item.get("agent_id"): item.get("needs")
        for item in required_followups
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }

    directed = payload.get("定向补充发言")
    agent_followups: list[dict[str, Any]] = []
    if isinstance(directed, dict):
        for raw_agent, notes in directed.items():
            agent_id = resolve_agent_reference(raw_agent, participant_ids, review_packet)
            if agent_id not in participant_ids or agent_id not in required_map:
                continue
            participant = next(
                (item for item in review_packet.get("participants", []) if isinstance(item, dict) and item.get("agent_id") == agent_id),
                {},
            )
            agent_followups.append(
                {
                    "agent_id": agent_id,
                    "role_duty": participant.get("responsibility"),
                    "needs": required_map[agent_id],
                    "supplemental_points": ensure_string_list(notes),
                    "updated_recommendation": stringify_recommendation(notes),
                    "remaining_uncertainties": [],
                }
            )

    moderator_needs = required_map.get("moderator")
    moderator_section = payload.get("主持人补充汇总")
    moderator_followup = None
    if moderator_needs and isinstance(moderator_section, dict):
        evidence_buckets = roundtable_record.get("evidence_buckets") if isinstance(roundtable_record, dict) else {}
        moderator_followup = {
            "needs": moderator_needs,
            "added_or_corrected_consensus": ensure_string_list(moderator_section.get("新增或修正的共识")),
            "added_or_corrected_conflicts": ensure_string_list(moderator_section.get("新增或修正的冲突")),
            "facts": ensure_string_list(evidence_buckets.get("facts") if isinstance(evidence_buckets, dict) else None),
            "inferences": ensure_string_list(evidence_buckets.get("inferences") if isinstance(evidence_buckets, dict) else None),
            "updated_preliminary_recommendation": stringify_recommendation(moderator_section.get("更新后的初步建议")),
            "updated_stop_conditions": ensure_string_list(moderator_section.get("更新后的停止条件 / 复盘点")),
            "remaining_uncertainties": ensure_string_list_allow_empty(
                payload.get("返审提示", {}).get("仍有哪些不确定项") if isinstance(payload.get("返审提示"), dict) else None
            ),
        }

    return {
        "schema_version": "v0.1",
        "mode": "debate_followup_record",
        "source_kind": review_packet.get("source_kind"),
        "debate_id": review_result.get("debate_id"),
        "source_room_id": review_packet.get("source_room_id"),
        "topic_restatement": review_packet.get("topic_restatement"),
        "quick_mode": False,
        "followup_round": 1,
        "rejection_summary": ensure_string_list(payload.get("本轮未通过原因")),
        "required_followups": [
            {"agent_id": item["agent_id"], "needs": item["needs"]}
            for item in required_followups
            if isinstance(item, dict)
        ],
        "agent_followups": agent_followups,
        "moderator_followup": moderator_followup,
        "rereview_status": {
            "rereview_required": True,
            "max_followup_rounds": 1,
            "return_to_reviewer": True,
        },
    }


def enforce_review_scenario(*, prompt_input: dict[str, Any], review_packet: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not (prompt_input.get("scenario") == "reject_followup" and prompt_input.get("followup_round") == 0):
        return payload

    participant_ids = [
        item.get("agent_id")
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    ]
    enriched = dict(payload)
    enriched["allow_final_decision"] = False
    enriched["overall_score"] = min(normalize_score(payload.get("overall_score")), 6)
    required_followups = payload.get("required_followups") if isinstance(payload.get("required_followups"), list) else []
    if not required_followups:
        required_followups = infer_required_followups_from_review(payload=payload, participant_ids=participant_ids)
    enriched["required_followups"] = required_followups
    if isinstance(enriched.get("rationale"), str) and enriched["rationale"].strip():
        enriched["rationale"] = enriched["rationale"].strip() + " Initial reject_followup validation round requires at least one targeted followup before final decision."
    else:
        enriched["rationale"] = "Initial reject_followup validation round requires targeted followups before final decision."
    return enriched


def enrich_debate_roundtable_record(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    participants = prompt_input.get("participants")
    speaker_order = prompt_input.get("speaker_order")
    prompt_inputs = prompt_input.get("prompt_inputs")
    quick_mode = bool(prompt_inputs.get("quick_mode")) if isinstance(prompt_inputs, dict) else False
    participant_map = {
        item.get("agent_id"): item
        for item in participants
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    } if isinstance(participants, list) else {}

    enriched = dict(payload)
    enriched["source_kind"] = payload.get("source_kind") or "room_handoff"
    enriched["debate_id"] = payload.get("debate_id") or prompt_input.get("debate_id")
    enriched["source_room_id"] = payload.get("source_room_id") or prompt_input.get("source_room_id")
    enriched["primary_type"] = payload.get("primary_type") or prompt_input.get("primary_type")
    enriched["secondary_type"] = payload.get("secondary_type", prompt_input.get("secondary_type"))
    enriched["quick_mode"] = bool(payload.get("quick_mode", quick_mode))
    enriched["topic_restatement"] = first_non_empty_string(
        payload.get("topic_restatement"),
        payload.get("moderator_summary", {}).get("topic_restatement") if isinstance(payload.get("moderator_summary"), dict) else None,
        prompt_input.get("topic"),
    )

    if isinstance(participants, list):
        enriched["participants"] = [
            {
                "agent_id": item["agent_id"],
                "short_name": item["short_name"],
                "responsibility": item["responsibility"],
            }
            for item in participants
            if isinstance(item, dict)
        ]
    if isinstance(speaker_order, list):
        enriched["speaker_order"] = list(speaker_order)

    moderator_summary = payload.get("moderator_summary")
    normalized_summary = dict(moderator_summary) if isinstance(moderator_summary, dict) else {}
    if isinstance(participants, list):
        normalized_summary["participants_and_roles"] = [
            {
                "agent_id": item["agent_id"],
                "responsibility": item["responsibility"],
            }
            for item in participants
            if isinstance(item, dict)
        ]
    normalized_summary["topic_restatement"] = first_non_empty_string(
        normalized_summary.get("topic_restatement"),
        payload.get("topic_restatement"),
        prompt_input.get("topic"),
    )
    normalized_summary["consensus_points"] = ensure_string_list(normalized_summary.get("consensus_points"))
    normalized_summary["core_conflicts"] = ensure_string_list(normalized_summary.get("core_conflicts"))
    normalized_summary["hidden_assumptions"] = ensure_string_list(normalized_summary.get("hidden_assumptions"))
    normalized_summary["review_focus"] = ensure_string_list(normalized_summary.get("review_focus"))
    enriched["moderator_summary"] = normalized_summary

    agent_outputs = payload.get("agent_outputs")
    if isinstance(agent_outputs, list):
        normalized_outputs = []
        for item in agent_outputs:
            if not isinstance(item, dict):
                continue
            agent_id = item.get("agent_id")
            participant = participant_map.get(agent_id, {})
            normalized_outputs.append(
                {
                    "agent_id": agent_id,
                    "role_duty": first_non_empty_string(item.get("role_duty"), participant.get("responsibility")),
                    "core_conclusion": first_non_empty_string(item.get("core_conclusion")),
                    "evidence": ensure_string_list(item.get("evidence")),
                    "biggest_problem": first_non_empty_string(item.get("biggest_problem")),
                    "opposed_misjudgment": first_non_empty_string(item.get("opposed_misjudgment")),
                    "concrete_recommendation": stringify_recommendation(item.get("concrete_recommendation")),
                    "confidence": normalize_confidence_value(item.get("confidence")),
                    "uncertainties": ensure_string_list(item.get("uncertainties")),
                }
            )
        enriched["agent_outputs"] = normalized_outputs

    evidence_buckets = payload.get("evidence_buckets")
    normalized_evidence = dict(evidence_buckets) if isinstance(evidence_buckets, dict) else {}
    normalized_evidence["facts"] = ensure_string_list(normalized_evidence.get("facts"))
    normalized_evidence["inferences"] = ensure_string_list(normalized_evidence.get("inferences"))
    normalized_evidence["uncertainties"] = ensure_string_list(normalized_evidence.get("uncertainties"))
    normalized_evidence["recommendations"] = ensure_string_list(normalized_evidence.get("recommendations"))
    enriched["evidence_buckets"] = normalized_evidence

    enriched["review_boundaries"] = {
        "conversation_log_reviewable": False,
        "review_only_visible_outputs": True,
        "followup_cap": 1,
    }
    enriched["review_status"] = {
        "review_required": not quick_mode,
        "followup_allowed": not quick_mode,
        "max_followup_rounds": 1,
    }
    return enriched


def enrich_debate_review_result(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    review_packet = prompt_input.get("review_packet")
    if not isinstance(review_packet, dict):
        return payload
    participant_ids = [
        item.get("agent_id")
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    ]
    enriched = dict(payload)
    enriched["source_kind"] = payload.get("source_kind") or review_packet.get("source_kind")
    enriched["debate_id"] = payload.get("debate_id") or prompt_input.get("debate_id")
    enriched["source_room_id"] = payload.get("source_room_id") or review_packet.get("source_room_id")
    enriched["topic_restatement"] = review_packet.get("topic_restatement")
    enriched["quick_mode"] = bool(payload.get("quick_mode", review_packet.get("quick_mode")))
    enriched["review_applicable"] = bool(payload.get("review_applicable", not bool(review_packet.get("quick_mode"))))
    enriched["overall_score"] = normalize_score(payload.get("overall_score"))
    enriched["best_agent"] = resolve_agent_reference(payload.get("best_agent"), participant_ids, review_packet)
    enriched["weak_agents"] = normalize_agent_list(payload.get("weak_agents"), participant_ids, review_packet)
    enriched["evidence_gaps"] = ensure_string_list_allow_empty(payload.get("evidence_gaps"))
    enriched["logic_gaps"] = ensure_string_list_allow_empty(payload.get("logic_gaps"))
    enriched["overlooked_issues"] = ensure_string_list_allow_empty(payload.get("overlooked_issues"))
    enriched["severe_red_flags"] = ensure_string_list_allow_empty(payload.get("severe_red_flags"))
    enriched["allow_final_decision"] = bool(payload.get("allow_final_decision"))
    enriched["required_followups"] = payload.get("required_followups") if isinstance(payload.get("required_followups"), list) else []
    enriched["rationale"] = first_non_empty_string(payload.get("rationale"))
    return enforce_review_scenario(prompt_input=prompt_input, review_packet=review_packet, payload=enriched)


def enrich_debate_followup_record(*, prompt_input: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    review_packet = prompt_input.get("review_packet")
    review_result = prompt_input.get("review_result")
    if not isinstance(review_packet, dict) or not isinstance(review_result, dict):
        return payload

    required_followups = review_result.get("required_followups") if isinstance(review_result.get("required_followups"), list) else []
    required_map = {
        item.get("agent_id"): item.get("needs")
        for item in required_followups
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    participant_map = {
        item.get("agent_id"): item
        for item in review_packet.get("participants", [])
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    participant_targets = [agent_id for agent_id in required_map if agent_id != "moderator"]

    enriched = dict(payload)
    enriched["source_kind"] = payload.get("source_kind") or review_packet.get("source_kind")
    enriched["debate_id"] = payload.get("debate_id") or review_result.get("debate_id") or prompt_input.get("debate_id")
    enriched["source_room_id"] = payload.get("source_room_id") or review_packet.get("source_room_id")
    enriched["topic_restatement"] = review_packet.get("topic_restatement")
    enriched["quick_mode"] = False
    enriched["followup_round"] = 1

    rejection_summary = ensure_string_list_allow_empty(payload.get("rejection_summary"))
    if not rejection_summary:
        rejection_summary = (
            ensure_string_list_allow_empty(review_result.get("evidence_gaps"))
            + ensure_string_list_allow_empty(review_result.get("logic_gaps"))
            + ensure_string_list_allow_empty(review_result.get("overlooked_issues"))
        )
    enriched["rejection_summary"] = rejection_summary or ["信息缺失"]

    if required_followups:
        enriched["required_followups"] = [
            {"agent_id": item["agent_id"], "needs": item["needs"]}
            for item in required_followups
            if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
        ]

    raw_agent_followups = payload.get("agent_followups")
    if isinstance(raw_agent_followups, list):
        normalized_agent_followups = []
        seen_targets: set[str] = set()
        for item in raw_agent_followups:
            if not isinstance(item, dict):
                continue
            agent_id = item.get("agent_id")
            if agent_id not in participant_targets or agent_id in seen_targets:
                continue
            seen_targets.add(agent_id)
            participant = participant_map.get(agent_id, {})
            normalized_agent_followups.append(
                {
                    "agent_id": agent_id,
                    "role_duty": participant.get("responsibility"),
                    "needs": required_map.get(agent_id),
                    "supplemental_points": ensure_string_list(item.get("supplemental_points")),
                    "updated_recommendation": stringify_recommendation(item.get("updated_recommendation")),
                    "remaining_uncertainties": ensure_string_list_allow_empty(item.get("remaining_uncertainties")),
                }
            )
        enriched["agent_followups"] = normalized_agent_followups

    moderator_required = "moderator" in required_map
    moderator_followup = payload.get("moderator_followup")
    if moderator_required:
        normalized_moderator = dict(moderator_followup) if isinstance(moderator_followup, dict) else {}
        normalized_moderator["needs"] = first_non_empty_string(normalized_moderator.get("needs"), required_map.get("moderator"))
        normalized_moderator["added_or_corrected_consensus"] = ensure_string_list(normalized_moderator.get("added_or_corrected_consensus"))
        normalized_moderator["added_or_corrected_conflicts"] = ensure_string_list(normalized_moderator.get("added_or_corrected_conflicts"))
        normalized_moderator["facts"] = ensure_string_list(normalized_moderator.get("facts"))
        normalized_moderator["inferences"] = ensure_string_list(normalized_moderator.get("inferences"))
        normalized_moderator["updated_preliminary_recommendation"] = stringify_recommendation(
            normalized_moderator.get("updated_preliminary_recommendation")
        )
        normalized_moderator["updated_stop_conditions"] = ensure_string_list(normalized_moderator.get("updated_stop_conditions"))
        normalized_moderator["remaining_uncertainties"] = ensure_string_list_allow_empty(
            normalized_moderator.get("remaining_uncertainties")
        )
        enriched["moderator_followup"] = normalized_moderator
    else:
        enriched["moderator_followup"] = None

    enriched["rereview_status"] = {
        "rereview_required": True,
        "max_followup_rounds": 1,
        "return_to_reviewer": True,
    }
    return enriched


def first_non_empty_string(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "信息缺失"


def normalize_agent_reference_list(items: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str) and item.strip():
            normalized.append({"agent": item.strip()})
            continue
        if not isinstance(item, dict):
            continue
        agent_id = item.get("agent") or item.get("agent_id")
        if isinstance(agent_id, str) and agent_id.strip():
            normalized.append({"agent": agent_id.strip()})
    return normalized


def ensure_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [item for item in (coerce_visible_string(entry) for entry in value) if item]
        return items or ["信息缺失"]
    single_value = coerce_visible_string(value)
    if single_value:
        return [single_value]
    return ["信息缺失"]


def ensure_string_list_allow_empty(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (coerce_visible_string(entry) for entry in value) if item]
    single_value = coerce_visible_string(value)
    if single_value:
        return [single_value]
    return []


def coerce_visible_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if not isinstance(value, dict):
        return None
    for key in (
        "text",
        "needs",
        "uncertainty_text",
        "recommendation",
        "updated_recommendation",
        "summary",
        "label",
        "title",
    ):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def normalize_confidence_value(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"高", "high"}:
            return "high"
        if normalized in {"中", "medium", "med"}:
            return "medium"
        if normalized in {"中高", "medium-high", "mid-high"}:
            return "medium"
        if normalized in {"低", "low"}:
            return "low"
    return "medium"


def stringify_recommendation(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            if items:
                return " ".join(items)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "信息缺失"


def normalize_allow_decision(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"允许", "allow", "allowed", "pass", "passed", "yes", "true"}:
            return True
    return False


def normalize_score(value: Any) -> int:
    if isinstance(value, int):
        return max(1, min(10, value))
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return max(1, min(10, int(digits)))
    return 7


def resolve_agent_reference(value: Any, participant_ids: list[str], review_packet: dict[str, Any]) -> str:
    aliases: dict[str, str] = {}
    for item in review_packet.get("participants", []):
        if not isinstance(item, dict):
            continue
        agent_id = item.get("agent_id")
        short_name = item.get("short_name")
        if isinstance(agent_id, str):
            aliases[agent_id.lower()] = agent_id
        if isinstance(short_name, str):
            aliases[short_name.lower()] = agent_id
    if isinstance(value, str):
        resolved = aliases.get(value.strip().lower())
        if resolved:
            return resolved
    return participant_ids[0] if participant_ids else "信息缺失"


def normalize_agent_list(value: Any, participant_ids: list[str], review_packet: dict[str, Any]) -> list[str]:
    if not isinstance(value, list):
        return []
    resolved: list[str] = []
    for item in value:
        agent_id = resolve_agent_reference(item, participant_ids, review_packet)
        if agent_id in participant_ids and agent_id not in resolved:
            resolved.append(agent_id)
    return resolved


def parse_required_followups(value: Any, participant_ids: list[str], review_packet: dict[str, Any]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    followups: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            agent_id = resolve_agent_reference(item.get("agent_id") or item.get("agent"), participant_ids, review_packet)
            needs = first_non_empty_string(item.get("needs"), item.get("text"))
        elif isinstance(item, str):
            left, _, right = item.partition("->")
            if not right:
                left, _, right = item.partition("：")
            agent_id = resolve_agent_reference(left or item, participant_ids, review_packet)
            needs = first_non_empty_string(right or item)
        else:
            continue
        if agent_id in participant_ids:
            followups.append({"agent_id": agent_id, "needs": needs})
    return followups


def infer_required_followups_from_review(*, payload: dict[str, Any], participant_ids: list[str]) -> list[dict[str, str]]:
    followups: list[dict[str, str]] = []

    def add(agent_id: str, needs: str) -> None:
        if agent_id in participant_ids and all(item["agent_id"] != agent_id for item in followups):
            followups.append({"agent_id": agent_id, "needs": needs})

    weak_agents = payload.get("weak_agents")
    if isinstance(weak_agents, list):
        for agent_id in weak_agents:
            if isinstance(agent_id, str):
                add(agent_id, "补齐 reviewer 指出的证据/逻辑缺口，并把建议改成可执行门槛。")

    corpus = " ".join(
        ensure_string_list_allow_empty(payload.get("evidence_gaps"))
        + ensure_string_list_allow_empty(payload.get("logic_gaps"))
        + ensure_string_list_allow_empty(payload.get("overlooked_issues"))
    )
    if any(token in corpus for token in ("kill", "阈值", "口径", "样本", "成本")):
        add("munger", "补齐 kill rule 的指标来源、统计口径与停止条件。")
    if any(token in corpus for token in ("错误", "信任", "风险", "停摆")):
        add("taleb", "给出关键错误定义、信任损伤量化和立即停摆动作。")
    if any(token in corpus for token in ("模型", "吞吐", "延迟", "人工复核", "降级", "闭环")):
        add("karpathy", "补充模型/规则闭环在延迟、吞吐、错误率和降级策略上的可执行性评估。")
    if any(token in corpus for token in ("场景", "高频", "切口", "体验")):
        add("steve-jobs", "补充单点场景选择依据，并说明为什么该入口足够高频且可复用。")

    if not followups and participant_ids:
        add(participant_ids[0], "补齐 reviewer 指出的关键缺口。")
    return followups


def write_trace_text(path: Path | None, payload: str | bytes | None) -> None:
    if path is None:
        return
    text: str
    if payload is None:
        text = ""
    elif isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = payload
    path.write_text(text, encoding="utf-8")


def build_trace_hint(trace_base: Path | None) -> str:
    if trace_base is None:
        return ""
    return f"; trace_base={trace_base}"


def repair_top_level_json_closers(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text

    entries: list[tuple[int, int, str | None]] = []
    depth = 0
    in_string = False
    escape = False
    object_end = -1
    i = start
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            string_start = i
            in_string = True
            escape = False
            i += 1
            if depth == 1:
                j = i
                local_escape = False
                while j < len(text):
                    inner = text[j]
                    if local_escape:
                        local_escape = False
                    elif inner == "\\":
                        local_escape = True
                    elif inner == '"':
                        break
                    j += 1
                colon = skip_whitespace(text, j + 1)
                if colon < len(text) and text[colon] == ":":
                    value_start = skip_whitespace(text, colon + 1)
                    opener = text[value_start] if value_start < len(text) and text[value_start] in "[{" else None
                    entries.append((string_start, value_start, opener))
                    i = j + 1
                    in_string = False
                    continue
            continue

        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                object_end = i
                break
        i += 1

    if object_end == -1 or not entries:
        return text

    repaired = list(text)
    for index, (_, value_start, opener) in enumerate(entries):
        if opener is None or opener not in "[{":
            continue
        next_key_start = entries[index + 1][0] if index + 1 < len(entries) else object_end
        closer_index = find_segment_closer(text, value_start=value_start, next_key_start=next_key_start, object_end=object_end)
        if closer_index is None:
            continue
        closer = repaired[closer_index]
        if opener == "[" and closer == "}":
            repaired[closer_index] = "]"
        elif opener == "{" and closer == "]":
            repaired[closer_index] = "}"
    return "".join(repaired)


def repair_truncated_json_tail(text: str) -> str:
    stripped_end = len(text.rstrip())
    core = text[:stripped_end]
    suffix = text[stripped_end:]
    if not core:
        return text

    trail_index = len(core)
    while trail_index > 0 and core[trail_index - 1] in "}]":
        trail_index -= 1
    if trail_index == len(core):
        return text

    prefix = core[:trail_index]
    trailing_braces = core[trail_index:]
    in_string = False
    escape = False
    for ch in prefix:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True

    if not in_string:
        return text
    return prefix + '"' + trailing_braces + suffix


def repair_missing_string_quotes_before_delimiters(text: str) -> str:
    if not text:
        return text

    repaired: list[str] = []
    in_string = False
    escape = False
    delimiter_patterns = (',"', ',{', ',]', ',}', '},{"', '}]', '},]')
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            elif any(text.startswith(pattern, i) for pattern in delimiter_patterns):
                repaired.append('"')
                in_string = False
                continue
        elif ch == '"':
            in_string = True

        repaired.append(ch)
        i += 1
    return "".join(repaired)


def repair_unterminated_json_eof(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text

    prefix = text[:start]
    core = text[start:]
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in core:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch in "{[":
            stack.append(ch)
            continue
        if ch == "}" and stack and stack[-1] == "{":
            stack.pop()
            continue
        if ch == "]" and stack and stack[-1] == "[":
            stack.pop()
            continue

    suffix = ""
    if in_string:
        suffix += '"'
    while stack:
        opener = stack.pop()
        suffix += "}" if opener == "{" else "]"
    if not suffix:
        return text
    return prefix + core + suffix


def skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def find_segment_closer(text: str, *, value_start: int, next_key_start: int, object_end: int) -> int | None:
    end = next_key_start if next_key_start > value_start else object_end
    cursor = end - 1
    while cursor > value_start and text[cursor].isspace():
        cursor -= 1
    if cursor > value_start and text[cursor] == ",":
        cursor -= 1
    while cursor > value_start and text[cursor].isspace():
        cursor -= 1
    if cursor <= value_start:
        return None
    return cursor


if __name__ == "__main__":
    sys.exit(main())
