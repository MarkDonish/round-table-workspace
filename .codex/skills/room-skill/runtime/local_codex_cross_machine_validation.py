#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_codex_executor as local_executor
import local_codex_regression as local_regression


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "local-codex-cross-machine-validation"
DEFAULT_TARGET_STATE_ROOT = "/tmp/round-table-local-codex-cross-machine"
DEFAULT_LOCAL_CODEX_PRESET = local_regression.DEFAULT_LOCAL_CODEX_PRESET


class LocalCodexCrossMachineValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_bundle(args)
        elif args.command == "verify":
            result = verify_bundle(args)
        else:
            raise LocalCodexCrossMachineValidationError(f"Unsupported command: {args.command}")
    except (LocalCodexCrossMachineValidationError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and verify a checked-in cross-machine validation lane for the local Codex /room -> /debate mainline."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Create a portable manifest, runbook, and target command for another machine.",
    )
    prepare.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for prepared cross-machine validation bundles.",
    )
    prepare.add_argument("--run-id", help="Optional stable bundle run id.")
    prepare.add_argument(
        "--target-run-id",
        help="Optional regression run id that the target machine should use.",
    )
    prepare.add_argument(
        "--target-state-root",
        default=DEFAULT_TARGET_STATE_ROOT,
        help="Suggested state-root for the target machine's local regression run.",
    )
    prepare.add_argument(
        "--target-python",
        default=resolve_default_python_launcher(),
        help="Python launcher for the target machine command, for example `python`, `py -3`, or `python3`.",
    )
    add_regression_config_args(prepare)

    verify = subparsers.add_parser(
        "verify",
        help="Verify imported regression evidence from another machine against a prepared manifest.",
    )
    verify.add_argument(
        "--manifest-json",
        required=True,
        help="Prepared cross-machine manifest JSON from the source machine.",
    )
    verify.add_argument(
        "--report-json",
        required=True,
        help="Imported local-codex-regression-report.json from the target machine.",
    )
    verify.add_argument(
        "--runtime-profile-json",
        help="Imported runtime-profile.json from the target machine. If omitted, verification tries the report artifact path.",
    )
    verify.add_argument(
        "--verification-dir",
        help="Optional explicit directory for verified imported evidence and the verification report.",
    )

    return parser


def add_regression_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--local-codex-preset",
        choices=sorted(local_executor.LOCAL_CODEX_PRESETS),
        default=DEFAULT_LOCAL_CODEX_PRESET,
        help="Checked-in local Codex preset for the target machine regression run.",
    )
    parser.add_argument("--local-codex-model", help="Optional model override for target local Codex child tasks.")
    parser.add_argument(
        "--local-codex-fallback-models",
        help="Optional comma-separated fallback models for target local Codex child tasks.",
    )
    parser.add_argument("--local-codex-profile", help="Optional Codex profile for target local Codex child tasks.")
    parser.add_argument(
        "--local-codex-reasoning-effort",
        default=None,
        help="Reasoning effort override for target local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-sandbox",
        default=None,
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode for target local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-timeout-seconds",
        type=int,
        default=None,
        help="Timeout for one target local Codex child task.",
    )
    parser.add_argument(
        "--local-codex-timeout-retries",
        type=int,
        default=None,
        help="How many times the target machine should retry a timed-out local Codex child task.",
    )
    parser.add_argument(
        "--local-codex-retry-timeout-multiplier",
        type=float,
        default=None,
        help="Timeout multiplier applied on each retry after a timeout.",
    )
    parser.add_argument(
        "--local-codex-persist-session",
        action="store_true",
        help="Keep target local Codex child sessions on disk instead of using --ephemeral.",
    )
    parser.add_argument(
        "--topic",
        default=local_regression.room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for the target machine regression run.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=local_regression.DEFAULT_REGRESSION_FOLLOW_UP,
        help="Follow-up /room input for the target machine regression run.",
    )


def prepare_bundle(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"local-codex-cross-machine-{uuid.uuid4().hex[:8]}"
    bundle_dir = state_root / run_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = bundle_dir / "cross-machine-validation-manifest.json"
    target_command_path = bundle_dir / "target-command.txt"
    runbook_path = bundle_dir / "target-runbook.md"
    target_run_id = args.target_run_id or f"local-codex-regression-{run_id}"
    provider_config = build_provider_config(args)
    source_repo = local_regression.build_repo_metadata(REPO_ROOT)
    warnings: list[str] = []
    if source_repo.get("dirty"):
        warnings.append(
            "Source repo is dirty. Commit and push before using this bundle for a true cross-machine replay."
        )
    target_command = build_target_regression_command(
        args=args,
        target_state_root=args.target_state_root,
        target_run_id=target_run_id,
    )
    manifest = {
        "ok": True,
        "schema_version": "v0.1",
        "mode": "local_codex_cross_machine_validation",
        "action": "prepare",
        "run_id": run_id,
        "prepared_at": utc_now_iso(),
        "source_host": local_regression.build_host_metadata(),
        "source_repo": source_repo,
        "ready_for_handoff": not bool(source_repo.get("dirty")),
        "warnings": warnings,
        "expected_regression": {
            "action": "local-codex-regression",
            "run_id": target_run_id,
            "inputs": {
                "topic": args.topic,
                "follow_up_input": args.follow_up_input,
            },
            "provider_config": provider_config,
            "python_launcher": args.target_python,
            "target_state_root_hint": args.target_state_root,
            "target_command": target_command,
            "target_command_text": " ".join(shlex.quote(part) for part in target_command),
        },
        "artifacts": {
            "bundle_dir": str(bundle_dir),
            "manifest_json": str(manifest_path),
            "target_command_txt": str(target_command_path),
            "target_runbook_md": str(runbook_path),
        },
    }
    target_command_path.write_text(manifest["expected_regression"]["target_command_text"] + "\n", encoding="utf-8")
    runbook_path.write_text(build_runbook(manifest), encoding="utf-8")
    write_json(manifest_path, manifest)
    return manifest


def verify_bundle(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest_json).expanduser().resolve()
    report_path = Path(args.report_json).expanduser().resolve()
    manifest = load_json_dict(manifest_path)
    report = load_json_dict(report_path)
    runtime_profile_path = resolve_runtime_profile_path(args=args, report=report)
    runtime_profile = load_json_dict(runtime_profile_path) if runtime_profile_path is not None else None

    verification_dir = resolve_verification_dir(args=args, manifest_path=manifest_path)
    verification_dir.mkdir(parents=True, exist_ok=True)
    imported_report_copy = verification_dir / "imported-local-codex-regression-report.json"
    imported_report_copy.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")

    imported_runtime_profile_copy = None
    if runtime_profile_path is not None and runtime_profile is not None:
        imported_runtime_profile_copy = verification_dir / "imported-runtime-profile.json"
        imported_runtime_profile_copy.write_text(
            runtime_profile_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    expected_regression = manifest.get("expected_regression", {})
    expected_provider_config = expected_regression.get("provider_config", {})
    checks = {
        "report_ok": bool(report.get("ok")),
        "report_action_match": report.get("action") == expected_regression.get("action"),
        "full_suite_passed": bool(report.get("pass_criteria", {}).get("full_suite_passed")),
        "provider_mode_match": report.get("provider_config", {}).get("mode") == expected_provider_config.get("mode"),
        "preset_match": report.get("provider_config", {}).get("preset") == expected_provider_config.get("preset"),
        "model_match": report.get("provider_config", {}).get("model") == expected_provider_config.get("model"),
        "fallback_models_match": normalize_list(report.get("provider_config", {}).get("fallback_models"))
        == normalize_list(expected_provider_config.get("fallback_models")),
        "reasoning_effort_match": report.get("provider_config", {}).get("reasoning_effort")
        == expected_provider_config.get("reasoning_effort"),
        "sandbox_match": report.get("provider_config", {}).get("sandbox") == expected_provider_config.get("sandbox"),
        "ephemeral_match": report.get("provider_config", {}).get("ephemeral") == expected_provider_config.get("ephemeral"),
        "timeout_seconds_match": report.get("provider_config", {}).get("timeout_seconds")
        == expected_provider_config.get("timeout_seconds"),
        "timeout_retries_match": report.get("provider_config", {}).get("timeout_retries")
        == expected_provider_config.get("timeout_retries"),
        "retry_timeout_multiplier_match": report.get("provider_config", {}).get("retry_timeout_multiplier")
        == expected_provider_config.get("retry_timeout_multiplier"),
        "topic_match": report.get("inputs", {}).get("topic") == expected_regression.get("inputs", {}).get("topic"),
        "follow_up_input_match": report.get("inputs", {}).get("follow_up_input")
        == expected_regression.get("inputs", {}).get("follow_up_input"),
        "head_commit_match": report.get("repo", {}).get("head_commit") == manifest.get("source_repo", {}).get("head_commit"),
        "runtime_profile_present": runtime_profile is not None,
        "runtime_profile_mode_match": (runtime_profile or {}).get("mode") == "local_codex_runtime_profile",
        "runtime_profile_head_commit_match": (runtime_profile or {}).get("repo", {}).get("head_commit")
        == manifest.get("source_repo", {}).get("head_commit"),
    }
    cross_machine_confirmed = is_cross_machine(
        source_host=manifest.get("source_host", {}),
        target_host=report.get("host", {}),
    )
    verification_ok = all(bool(value) for value in checks.values())
    verification_report = {
        "ok": verification_ok,
        "schema_version": "v0.1",
        "mode": "local_codex_cross_machine_validation",
        "action": "verify",
        "verified_at": utc_now_iso(),
        "manifest": str(manifest_path),
        "imported_report": str(imported_report_copy),
        "imported_runtime_profile": str(imported_runtime_profile_copy) if imported_runtime_profile_copy else None,
        "checks": checks,
        "summary": {
            "cross_machine_confirmed": cross_machine_confirmed,
            "needs_true_cross_machine_replay": not cross_machine_confirmed,
            "source_ready_for_handoff_at_prepare": manifest.get("ready_for_handoff"),
            "source_machine": manifest.get("source_host", {}).get("machine"),
            "target_machine": report.get("host", {}).get("machine"),
            "source_commit": manifest.get("source_repo", {}).get("short_commit"),
            "target_commit": report.get("repo", {}).get("short_commit"),
            "slowest_stage": (runtime_profile or {}).get("summary", {}).get("slowest_stage"),
            "slowest_policy_key": (runtime_profile or {}).get("summary", {}).get("slowest_policy_key"),
        },
        "artifacts": {
            "verification_dir": str(verification_dir),
            "verification_report": str(verification_dir / "cross-machine-verification-report.json"),
        },
    }
    verification_report_path = verification_dir / "cross-machine-verification-report.json"
    write_json(verification_report_path, verification_report)
    return verification_report


def build_provider_config(args: argparse.Namespace) -> dict[str, Any]:
    settings = local_regression.resolve_local_codex_settings(args)
    return {
        "mode": "local_codex",
        **settings,
    }


def build_target_regression_command(
    *,
    args: argparse.Namespace,
    target_state_root: str,
    target_run_id: str,
) -> list[str]:
    command = [
        *split_python_launcher(args.target_python),
        ".codex/skills/room-skill/runtime/local_codex_regression.py",
        "--state-root",
        target_state_root,
        "--run-id",
        target_run_id,
        "--local-codex-preset",
        args.local_codex_preset,
        "--topic",
        args.topic,
        "--follow-up-input",
        args.follow_up_input,
    ]
    append_optional_arg(command, "--local-codex-model", args.local_codex_model)
    append_optional_arg(command, "--local-codex-fallback-models", args.local_codex_fallback_models)
    append_optional_arg(command, "--local-codex-profile", args.local_codex_profile)
    append_optional_arg(command, "--local-codex-reasoning-effort", args.local_codex_reasoning_effort)
    append_optional_arg(command, "--local-codex-sandbox", args.local_codex_sandbox)
    append_optional_arg(command, "--local-codex-timeout-seconds", args.local_codex_timeout_seconds)
    append_optional_arg(command, "--local-codex-timeout-retries", args.local_codex_timeout_retries)
    append_optional_arg(
        command,
        "--local-codex-retry-timeout-multiplier",
        args.local_codex_retry_timeout_multiplier,
    )
    if args.local_codex_persist_session:
        command.append("--local-codex-persist-session")
    return command


def build_runbook(manifest: dict[str, Any]) -> str:
    target_command = manifest["expected_regression"]["target_command_text"]
    python_launcher = manifest["expected_regression"].get("python_launcher") or "python3"
    warning_block = ""
    if manifest.get("warnings"):
        warning_lines = "\n".join(f"- {warning}" for warning in manifest["warnings"])
        warning_block = f"{warning_lines}\n\n"
    return (
        "# Cross-Machine Local Mainline Validation\n\n"
        f"{warning_block}"
        "1. On the target machine, open the same repository revision.\n"
        f"   Required commit: `{manifest['source_repo'].get('head_commit')}`\n"
        "2. Confirm the target machine can run local Codex child tasks from this repo.\n"
        "3. Run the checked-in local regression command exactly as prepared below.\n\n"
        "```bash\n"
        f"{target_command}\n"
        "```\n\n"
        "4. Copy these files back to the source machine:\n"
        "- `local-codex-regression-report.json`\n"
        "- `runtime-profile.json`\n\n"
        "5. On the source machine, verify the imported evidence with:\n\n"
        "```bash\n"
        f"{python_launcher} .codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py \\\n"
        "  verify \\\n"
        f"  --manifest-json {shlex.quote(manifest['artifacts']['manifest_json'])} \\\n"
        "  --report-json /path/to/imported/local-codex-regression-report.json \\\n"
        "  --runtime-profile-json /path/to/imported/runtime-profile.json\n"
        "```\n"
    )


def resolve_runtime_profile_path(
    *,
    args: argparse.Namespace,
    report: dict[str, Any],
) -> Path | None:
    if args.runtime_profile_json:
        return Path(args.runtime_profile_json).expanduser().resolve()
    artifact_path = report.get("artifacts", {}).get("runtime_profile")
    if not artifact_path:
        return None
    candidate = Path(str(artifact_path)).expanduser()
    return candidate.resolve() if candidate.exists() else None


def resolve_verification_dir(
    *,
    args: argparse.Namespace,
    manifest_path: Path,
) -> Path:
    if args.verification_dir:
        return Path(args.verification_dir).expanduser().resolve()
    return manifest_path.parent / f"verification-{uuid.uuid4().hex[:8]}"


def is_cross_machine(*, source_host: dict[str, Any], target_host: dict[str, Any]) -> bool:
    source_machine = source_host.get("machine")
    target_machine = target_host.get("machine")
    if source_machine and target_machine and source_machine != target_machine:
        return True
    source_platform = source_host.get("platform")
    target_platform = target_host.get("platform")
    if source_platform and target_platform and source_platform != target_platform:
        return True
    return False


def normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def append_optional_arg(command: list[str], flag: str, value: Any) -> None:
    if value is None:
        return
    command.extend([flag, str(value)])


def resolve_default_python_launcher() -> str:
    if sys.platform == "win32":
        if shutil.which("python"):
            return "python"
        if shutil.which("py"):
            return "py -3"
    return "python3"


def split_python_launcher(value: str) -> list[str]:
    parts = shlex.split(value, posix=(sys.platform != "win32"))
    if not parts:
        raise LocalCodexCrossMachineValidationError("Python launcher cannot be empty.")
    return parts


def load_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LocalCodexCrossMachineValidationError(f"Expected JSON object at {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
