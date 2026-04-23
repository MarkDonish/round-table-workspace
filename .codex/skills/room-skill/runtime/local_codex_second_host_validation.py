#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chat_completions_executor import parse_json_from_text

import local_codex_executor as local_executor
import local_codex_regression as local_regression


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "runtime" / "local-codex-second-host-validation"
DEFAULT_LOCAL_CODEX_PRESET = local_regression.DEFAULT_LOCAL_CODEX_PRESET
DEFAULT_HOST_SANDBOX = "workspace-write"
DEFAULT_HOST_TIMEOUT_SECONDS = 3600


class LocalCodexSecondHostValidationError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_validation(args)
    except (LocalCodexSecondHostValidationError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the checked-in local Codex regression suite through a second standalone `codex exec` host, "
            "then persist wrapper evidence plus the nested runtime profile."
        )
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for persisted second-host validation evidence.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional stable second-host validation run id.",
    )
    parser.add_argument(
        "--host-sandbox",
        default=DEFAULT_HOST_SANDBOX,
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox for the outer standalone `codex exec` host.",
    )
    parser.add_argument("--host-model", help="Optional model override for the outer standalone `codex exec` host.")
    parser.add_argument("--host-profile", help="Optional Codex profile for the outer standalone `codex exec` host.")
    parser.add_argument(
        "--host-reasoning-effort",
        help="Optional reasoning effort override for the outer standalone `codex exec` host.",
    )
    parser.add_argument(
        "--host-timeout-seconds",
        type=int,
        default=DEFAULT_HOST_TIMEOUT_SECONDS,
        help="Timeout for the full outer standalone `codex exec` host run.",
    )
    parser.add_argument(
        "--nested-python",
        default=resolve_default_python_launcher(),
        help="Python launcher for the nested regression command, for example `python`, `py -3`, or `python3`.",
    )
    parser.add_argument(
        "--local-codex-preset",
        choices=sorted(local_executor.LOCAL_CODEX_PRESETS),
        default=DEFAULT_LOCAL_CODEX_PRESET,
        help="Checked-in local Codex preset for the nested regression suite.",
    )
    parser.add_argument("--local-codex-model", help="Optional model override for nested local Codex child tasks.")
    parser.add_argument(
        "--local-codex-fallback-models",
        help="Optional comma-separated fallback models for nested local Codex child tasks.",
    )
    parser.add_argument("--local-codex-profile", help="Optional Codex profile for nested local Codex child tasks.")
    parser.add_argument(
        "--local-codex-reasoning-effort",
        default=None,
        help="Reasoning effort override for nested local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-sandbox",
        default=None,
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode for nested local Codex child tasks.",
    )
    parser.add_argument(
        "--local-codex-timeout-seconds",
        type=int,
        default=None,
        help="Timeout for one nested local Codex child task.",
    )
    parser.add_argument(
        "--local-codex-timeout-retries",
        type=int,
        default=None,
        help="How many times to retry a timed-out or transiently disconnected nested local Codex child task.",
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
        help="Keep nested local Codex child sessions on disk instead of using --ephemeral.",
    )
    parser.add_argument(
        "--topic",
        default=local_regression.room_validation.DEFAULT_TOPIC,
        help="Initial /room topic for the nested regression suite.",
    )
    parser.add_argument(
        "--follow-up-input",
        default=local_regression.DEFAULT_REGRESSION_FOLLOW_UP,
        help="Follow-up /room input for the nested regression suite.",
    )
    return parser


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    run_id = args.run_id or f"local-codex-second-host-{uuid.uuid4().hex[:8]}"
    validation_dir = state_root / run_id
    validation_dir.mkdir(parents=True, exist_ok=True)

    report_path = validation_dir / "second-host-validation-report.json"
    command_path = validation_dir / "second-host.command.json"
    stdout_path = validation_dir / "second-host.stdout.txt"
    stderr_path = validation_dir / "second-host.stderr.txt"
    last_message_path = validation_dir / "second-host.last-message.txt"
    nested_state_root = validation_dir / "nested-regression"
    nested_run_id = f"local-codex-regression-{run_id}"
    nested_report_path = nested_state_root / nested_run_id / "local-codex-regression-report.json"
    nested_runtime_profile_path = nested_state_root / nested_run_id / "runtime-profile.json"

    started_at = utc_now_iso()
    started_monotonic = time.monotonic()
    codex_path = shutil.which("codex")
    if not codex_path:
        raise LocalCodexSecondHostValidationError("Could not find `codex` on PATH.")

    regression_command = build_nested_regression_command(
        args=args,
        nested_state_root=nested_state_root,
        nested_run_id=nested_run_id,
    )
    host_prompt = build_host_prompt(
        regression_command=regression_command,
        nested_report_path=nested_report_path,
        nested_runtime_profile_path=nested_runtime_profile_path,
    )
    codex_exec_command = build_codex_exec_command(
        codex_path=codex_path,
        args=args,
        last_message_path=last_message_path,
    )

    command_payload = {
        "cmd": codex_exec_command,
        "cwd": str(REPO_ROOT),
        "host_prompt": host_prompt,
        "nested_regression_command": regression_command,
        "nested_report_path": str(nested_report_path),
        "nested_runtime_profile_path": str(nested_runtime_profile_path),
    }
    write_json(command_path, command_payload)

    try:
        completed = subprocess.run(
            codex_exec_command,
            input=host_prompt,
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=REPO_ROOT,
            timeout=args.host_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        write_text(stdout_path, exc.stdout)
        write_text(stderr_path, exc.stderr)
        failure_report = build_failure_report(
            run_id=run_id,
            validation_dir=validation_dir,
            report_path=report_path,
            command_path=command_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            last_message_path=last_message_path,
            started_at=started_at,
            started_monotonic=started_monotonic,
            error=f"second host timed out after {args.host_timeout_seconds}s",
            outer_host_result=None,
            nested_report_path=nested_report_path,
            nested_runtime_profile_path=nested_runtime_profile_path,
        )
        write_json(report_path, failure_report)
        raise LocalCodexSecondHostValidationError(failure_report["error"])

    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)

    outer_host_result = parse_outer_host_result(last_message_path=last_message_path, stdout_text=completed.stdout)
    if outer_host_result is None:
        failure_report = build_failure_report(
            run_id=run_id,
            validation_dir=validation_dir,
            report_path=report_path,
            command_path=command_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            last_message_path=last_message_path,
            started_at=started_at,
            started_monotonic=started_monotonic,
            error="second host completed without a parseable final JSON object",
            outer_host_result=None,
            nested_report_path=nested_report_path,
            nested_runtime_profile_path=nested_runtime_profile_path,
        )
        write_json(report_path, failure_report)
        raise LocalCodexSecondHostValidationError(failure_report["error"])
    if completed.returncode != 0:
        failure_report = build_failure_report(
            run_id=run_id,
            validation_dir=validation_dir,
            report_path=report_path,
            command_path=command_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            last_message_path=last_message_path,
            started_at=started_at,
            started_monotonic=started_monotonic,
            error=f"second host exited with code {completed.returncode}",
            outer_host_result=outer_host_result,
            nested_report_path=nested_report_path,
            nested_runtime_profile_path=nested_runtime_profile_path,
        )
        write_json(report_path, failure_report)
        raise LocalCodexSecondHostValidationError(failure_report["error"])

    nested_report = load_optional_json(nested_report_path)
    nested_runtime_profile = load_optional_json(nested_runtime_profile_path)
    finished_at = utc_now_iso()
    wall_time_seconds = round(max(time.monotonic() - started_monotonic, 0.0), 3)
    overall_passed = bool((outer_host_result or {}).get("ok")) and bool(
        (nested_report or {}).get("pass_criteria", {}).get("full_suite_passed")
    )

    report = {
        "ok": overall_passed,
        "action": "local-codex-second-host-validation",
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "wall_time_seconds": wall_time_seconds,
        "outer_host": {
            "machine": socket.gethostname(),
            "codex_binary": codex_path,
            "sandbox": args.host_sandbox,
            "model": args.host_model,
            "profile": args.host_profile,
            "reasoning_effort": args.host_reasoning_effort,
            "timeout_seconds": args.host_timeout_seconds,
        },
        "nested_regression": {
            "state_root": str(nested_state_root),
            "run_id": nested_run_id,
            "provider_config": nested_report.get("provider_config") if isinstance(nested_report, dict) else None,
            "pass_criteria": nested_report.get("pass_criteria") if isinstance(nested_report, dict) else None,
            "runtime_profile_summary": (
                nested_report.get("runtime_profile") if isinstance(nested_report, dict) else None
            ),
        },
        "outer_host_result": outer_host_result,
        "artifacts": {
            "validation_dir": str(validation_dir),
            "validation_report": str(report_path),
            "host_command": str(command_path),
            "host_stdout": str(stdout_path),
            "host_stderr": str(stderr_path),
            "host_last_message": str(last_message_path),
            "nested_regression_report": str(nested_report_path),
            "nested_runtime_profile": str(nested_runtime_profile_path),
            "nested_integration_report": (
                nested_report.get("artifacts", {}).get("integration_report")
                if isinstance(nested_report, dict)
                else None
            ),
        },
        "summary": build_summary(
            outer_host_result=outer_host_result,
            nested_report=nested_report,
            nested_runtime_profile=nested_runtime_profile,
            wall_time_seconds=wall_time_seconds,
        ),
    }
    write_json(report_path, report)
    return report


def build_nested_regression_command(
    *,
    args: argparse.Namespace,
    nested_state_root: Path,
    nested_run_id: str,
) -> list[str]:
    command = [
        *split_python_launcher(args.nested_python),
        ".codex/skills/room-skill/runtime/local_codex_regression.py",
        "--state-root",
        str(nested_state_root),
        "--run-id",
        nested_run_id,
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


def build_codex_exec_command(
    *,
    codex_path: str,
    args: argparse.Namespace,
    last_message_path: Path,
) -> list[str]:
    command = [
        codex_path,
        "exec",
        "--color",
        "never",
        "-C",
        str(REPO_ROOT),
        "--sandbox",
        args.host_sandbox,
        "--output-last-message",
        str(last_message_path),
    ]
    if args.host_model:
        command.extend(["--model", args.host_model])
    if args.host_profile:
        command.extend(["--profile", args.host_profile])
    if args.host_reasoning_effort:
        command.extend(["-c", f'model_reasoning_effort="{args.host_reasoning_effort}"'])
    return command


def build_host_prompt(
    *,
    regression_command: list[str],
    nested_report_path: Path,
    nested_runtime_profile_path: Path,
) -> str:
    regression_command_text = " ".join(shlex.quote(part) for part in regression_command)
    return (
        "You are validating the checked-in round-table local mainline from a second standalone Codex host.\n"
        "Do not edit files.\n"
        "Do not browse the web.\n"
        "Stay in this repository.\n"
        "Run exactly this shell command:\n"
        f"{regression_command_text}\n\n"
        f"After it finishes, read the nested regression report at:\n{nested_report_path}\n"
        f"And the nested runtime profile at:\n{nested_runtime_profile_path}\n\n"
        "Return exactly one JSON object and nothing else with these keys:\n"
        '{"ok":true,"action":"local-codex-regression","host":"<hostname>","full_suite_passed":true,"report_path":"<absolute path>","integration_report_path":"<absolute path>","runtime_profile_path":"<absolute path>","notes":"<short note>"}\n'
        "If the regression fails, keep the same keys but set `ok` to false and explain the failure briefly in `notes`.\n"
    )


def parse_outer_host_result(*, last_message_path: Path, stdout_text: str) -> dict[str, Any] | None:
    if last_message_path.exists():
        try:
            parsed = parse_json_from_text(last_message_path.read_text(encoding="utf-8"))
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            return parsed
    try:
        parsed_from_stdout = parse_json_from_text(stdout_text)
    except Exception:
        parsed_from_stdout = None
    return parsed_from_stdout if isinstance(parsed_from_stdout, dict) else None


def build_failure_report(
    *,
    run_id: str,
    validation_dir: Path,
    report_path: Path,
    command_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    last_message_path: Path,
    started_at: str,
    started_monotonic: float,
    error: str,
    outer_host_result: dict[str, Any] | None,
    nested_report_path: Path,
    nested_runtime_profile_path: Path,
) -> dict[str, Any]:
    return {
        "ok": False,
        "action": "local-codex-second-host-validation",
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "wall_time_seconds": round(max(time.monotonic() - started_monotonic, 0.0), 3),
        "error": error,
        "outer_host_result": outer_host_result,
        "artifacts": {
            "validation_dir": str(validation_dir),
            "validation_report": str(report_path),
            "host_command": str(command_path),
            "host_stdout": str(stdout_path),
            "host_stderr": str(stderr_path),
            "host_last_message": str(last_message_path),
            "nested_regression_report": str(nested_report_path),
            "nested_runtime_profile": str(nested_runtime_profile_path),
        },
    }


def build_summary(
    *,
    outer_host_result: dict[str, Any] | None,
    nested_report: dict[str, Any] | None,
    nested_runtime_profile: dict[str, Any] | None,
    wall_time_seconds: float,
) -> dict[str, Any]:
    return {
        "outer_host_ok": bool((outer_host_result or {}).get("ok")),
        "full_suite_passed": bool((nested_report or {}).get("pass_criteria", {}).get("full_suite_passed")),
        "outer_host_wall_time_seconds": wall_time_seconds,
        "nested_suite_wall_time_seconds": (nested_report or {}).get("wall_time_seconds"),
        "slowest_stage": (nested_runtime_profile or {}).get("summary", {}).get("slowest_stage"),
        "slowest_policy_key": (nested_runtime_profile or {}).get("summary", {}).get("slowest_policy_key"),
    }


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
        raise LocalCodexSecondHostValidationError("Python launcher cannot be empty.")
    return parts


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str | None) -> None:
    if text is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
