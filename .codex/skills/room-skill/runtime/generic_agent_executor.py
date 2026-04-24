#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chat_completions_executor import parse_json_from_text
import local_codex_executor as local_executor


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_CLAUDE_CODE_COMMAND = "claude -p"
TRACE_MANIFEST_SUFFIX = ".agent-trace.json"


class GenericAgentExecutorError(Exception):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        command = resolve_agent_command(executor_name=args.host_name, command=args.agent_command)
        if args.check_agent_exec:
            result = check_agent_exec(
                repo_root=REPO_ROOT,
                command=command,
                host_name=args.host_name,
                timeout_seconds=args.timeout_seconds,
            )
        else:
            if not args.prompt_file or not args.input_json:
                raise GenericAgentExecutorError(
                    "--prompt-file and --input-json are required unless --check-agent-exec is used.",
                    details=build_generic_agent_error_details(
                        failure_category="missing_prompt_input",
                        trace_base=None,
                        host_name=args.host_name,
                        command=command,
                    ),
                )
            prompt_path = Path(args.prompt_file).expanduser().resolve()
            input_path = Path(args.input_json).expanduser().resolve()
            result = call_generic_agent_cli(
                prompt_path=prompt_path,
                prompt_text=prompt_path.read_text(encoding="utf-8"),
                prompt_input=json.loads(input_path.read_text(encoding="utf-8")),
                repo_root=REPO_ROOT,
                command=command,
                host_name=args.host_name,
                timeout_seconds=args.timeout_seconds,
            )
    except (GenericAgentExecutorError, json.JSONDecodeError, ValueError) as exc:
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
        description="Run checked-in round-table prompts through a host-neutral local agent CLI."
    )
    parser.add_argument("--check-agent-exec", action="store_true", help="Run a minimal local agent CLI smoke test.")
    parser.add_argument("--host-name", default="generic_cli", help="Logical host name written into trace metadata.")
    parser.add_argument(
        "--agent-command",
        help=(
            "Local agent command. The adapter passes the task prompt on stdin and also supports "
            "{prompt_file}, {input_file}, {output_file}, and {repo_root} placeholders."
        ),
    )
    parser.add_argument("--prompt-file", help="Prompt markdown file to execute.")
    parser.add_argument("--input-json", help="Structured JSON input file for the prompt.")
    parser.add_argument("--output-json", help="Optional path for the parsed JSON output.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for one local agent CLI prompt call.",
    )
    return parser


def resolve_agent_command(*, executor_name: str, command: str | None) -> str:
    if command and command.strip():
        return command.strip()
    if executor_name == "claude_code":
        env_command = os.environ.get("CLAUDE_CODE_AGENT_COMMAND", "").strip() or os.environ.get(
            "CLAUDE_CODE_COMMAND", ""
        ).strip()
        return env_command or DEFAULT_CLAUDE_CODE_COMMAND
    raise GenericAgentExecutorError(
        "--agent-command is required for the generic_cli executor.",
        details=build_generic_agent_error_details(
            failure_category="missing_agent_command",
            trace_base=None,
            host_name=executor_name,
            command=None,
        ),
    )


def describe_agent_executor(*, executor_name: str, command: str | None, timeout_seconds: int | None) -> dict[str, Any]:
    resolved_command = resolve_agent_command(executor_name=executor_name, command=command)
    return {
        "mode": executor_name,
        "host_adapter": "local_agent_cli",
        "command": resolved_command,
        "timeout_seconds": timeout_seconds or DEFAULT_TIMEOUT_SECONDS,
        "stdin_contract": "round-table task prompt",
        "stdout_contract": "one JSON object, or write one JSON object to {output_file}",
    }


def check_agent_exec(*, repo_root: Path, command: str, host_name: str, timeout_seconds: int) -> dict[str, Any]:
    response = run_generic_agent_prompt(
        task_prompt='Return exactly this JSON object and nothing else: {"ok": true, "mode": "generic_agent_exec"}',
        prompt_input={"mode": "generic_agent_smoke"},
        repo_root=repo_root,
        command=command,
        host_name=host_name,
        timeout_seconds=timeout_seconds,
        trace_base=None,
        extra_env=None,
        execution_metadata={"check": "agent_exec"},
    )
    try:
        payload = parse_json_from_text(response)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GenericAgentExecutorError(
            "agent CLI smoke test returned a non-parseable JSON object.",
            details=build_generic_agent_error_details(
                failure_category="invalid_json_output",
                trace_base=None,
                host_name=host_name,
                command=command,
                response_excerpt=local_executor.build_text_excerpt(response),
            ),
        ) from exc
    if payload.get("ok") is not True:
        raise GenericAgentExecutorError(
            "agent CLI smoke test did not return ok=true.",
            details=build_generic_agent_error_details(
                failure_category="unexpected_agent_output",
                trace_base=None,
                host_name=host_name,
                command=command,
                response_excerpt=local_executor.build_text_excerpt(response),
            ),
        )
    return {
        "ready": True,
        "mode": "generic_agent_exec",
        "host_name": host_name,
        "command": command,
        "response": payload,
    }


def call_generic_agent_cli(
    *,
    prompt_path: Path,
    prompt_text: str,
    prompt_input: dict[str, Any],
    repo_root: Path,
    command: str,
    host_name: str,
    timeout_seconds: int,
    trace_base: Path | None = None,
    extra_env: dict[str, str] | None = None,
    execution_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_prompt = local_executor.build_task_prompt(
        prompt_path=prompt_path,
        prompt_text=prompt_text,
        prompt_input=prompt_input,
    )
    response = run_generic_agent_prompt(
        task_prompt=task_prompt,
        prompt_input=prompt_input,
        repo_root=repo_root,
        command=command,
        host_name=host_name,
        timeout_seconds=timeout_seconds,
        trace_base=trace_base,
        extra_env=extra_env,
        execution_metadata=execution_metadata,
    )
    repaired_response = local_executor.repair_runtime_json_text(response) or response
    try:
        payload = parse_json_from_text(repaired_response)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GenericAgentExecutorError(
            "agent CLI returned a non-parseable JSON object." + build_trace_hint(trace_base),
            details=build_generic_agent_error_details(
                failure_category="invalid_json_output",
                trace_base=trace_base,
                host_name=host_name,
                command=command,
                response_excerpt=local_executor.build_text_excerpt(repaired_response),
            ),
        ) from exc
    return local_executor.normalize_prompt_output(prompt_path=prompt_path, prompt_input=prompt_input, payload=payload)


def run_generic_agent_prompt(
    *,
    task_prompt: str,
    prompt_input: dict[str, Any],
    repo_root: Path,
    command: str,
    host_name: str,
    timeout_seconds: int,
    trace_base: Path | None,
    extra_env: dict[str, str] | None,
    execution_metadata: dict[str, Any] | None,
) -> str:
    started_monotonic = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="round-table-agent-cli-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        paths = build_trace_paths(trace_base=trace_base, temp_dir=temp_dir)
        prompt_file = require_path(paths["prompt_file"])
        input_file = require_path(paths["input_file"])
        output_file = require_path(paths["output_file"])
        prompt_file.write_text(task_prompt, encoding="utf-8")
        input_file.write_text(json.dumps(prompt_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        command_tokens = prepare_command_tokens(
            command=command,
            host_name=host_name,
            prompt_file=prompt_file,
            input_file=input_file,
            output_file=output_file,
            repo_root=repo_root,
        )
        if not command_tokens:
            raise GenericAgentExecutorError(
                "agent command resolved to an empty command.",
                details=build_generic_agent_error_details(
                    failure_category="missing_agent_command",
                    trace_base=trace_base,
                    host_name=host_name,
                    command=command,
                ),
            )

        env = os.environ.copy()
        env.update(
            {
                "ROUND_TABLE_PROMPT_FILE": str(prompt_file),
                "ROUND_TABLE_INPUT_JSON": str(input_file),
                "ROUND_TABLE_OUTPUT_JSON": str(output_file),
                "ROUND_TABLE_REPO_ROOT": str(repo_root),
            }
        )
        if extra_env:
            env.update(extra_env)

        trace_payload = {
            "mode": "generic_agent_cli_trace",
            "host_name": host_name,
            "command": command_tokens,
            "timeout_seconds": timeout_seconds,
            "repo_root": str(repo_root),
            "paths": serialize_trace_paths(paths),
            "extra_env_keys": sorted((extra_env or {}).keys()),
            "execution_metadata": execution_metadata or {},
            "started_at": utc_now_iso(),
            "final_status": "started",
        }
        write_trace_manifest(paths["trace_manifest"], trace_payload)
        write_json_file(
            paths["command"],
            {
                "host_name": host_name,
                "command": command_tokens,
                "timeout_seconds": timeout_seconds,
                "repo_root": str(repo_root),
                "extra_env_keys": sorted((extra_env or {}).keys()),
            },
        )

        try:
            completed = subprocess.run(
                command_tokens,
                input=task_prompt,
                cwd=str(repo_root),
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = ensure_text(exc.stdout)
            stderr = ensure_text(exc.stderr)
            write_text_file(paths["stdout"], stdout)
            write_text_file(paths["stderr"], stderr)
            set_trace_manifest_finished(trace_payload, final_status="timeout", started_monotonic=started_monotonic)
            trace_payload["failure_category"] = "agent_cli_timeout"
            write_trace_manifest(paths["trace_manifest"], trace_payload)
            raise GenericAgentExecutorError(
                f"agent CLI timed out after {timeout_seconds} seconds." + build_trace_hint(trace_base),
                details=build_generic_agent_error_details(
                    failure_category="agent_cli_timeout",
                    trace_base=trace_base,
                    host_name=host_name,
                    command=command,
                    timeout_seconds=timeout_seconds,
                    stdout_excerpt=local_executor.build_text_excerpt(stdout),
                    stderr_excerpt=local_executor.build_text_excerpt(stderr),
                ),
            ) from exc
        except OSError as exc:
            set_trace_manifest_finished(trace_payload, final_status="os_error", started_monotonic=started_monotonic)
            trace_payload["failure_category"] = "agent_cli_launch_failed"
            trace_payload["error"] = str(exc)
            write_trace_manifest(paths["trace_manifest"], trace_payload)
            raise GenericAgentExecutorError(
                f"agent CLI could not be launched: {exc}" + build_trace_hint(trace_base),
                details=build_generic_agent_error_details(
                    failure_category="agent_cli_launch_failed",
                    trace_base=trace_base,
                    host_name=host_name,
                    command=command,
                    summary=str(exc),
                ),
            ) from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        write_text_file(paths["stdout"], stdout)
        write_text_file(paths["stderr"], stderr)
        if completed.returncode != 0:
            failure = local_executor.classify_command_failure(
                stdout=stdout,
                stderr=stderr,
                returncode=completed.returncode,
            )
            set_trace_manifest_finished(trace_payload, final_status="command_failed", started_monotonic=started_monotonic)
            trace_payload["returncode"] = completed.returncode
            trace_payload["failure_category"] = failure["failure_category"]
            write_trace_manifest(paths["trace_manifest"], trace_payload)
            raise GenericAgentExecutorError(
                f"agent CLI exited with code {completed.returncode}: {failure['summary']}"
                + build_trace_hint(trace_base),
                details=build_generic_agent_error_details(
                    failure_category=failure["failure_category"],
                    trace_base=trace_base,
                    host_name=host_name,
                    command=command,
                    timeout_seconds=timeout_seconds,
                    returncode=completed.returncode,
                    summary=failure["summary"],
                    stdout_excerpt=local_executor.build_text_excerpt(stdout),
                    stderr_excerpt=local_executor.build_text_excerpt(stderr),
                ),
            )

        response, response_source = read_agent_response(stdout=stdout, output_file=output_file)
        write_text_file(paths["last_message"], response)
        if not response.strip():
            set_trace_manifest_finished(trace_payload, final_status="empty_response", started_monotonic=started_monotonic)
            trace_payload["failure_category"] = "empty_agent_response"
            write_trace_manifest(paths["trace_manifest"], trace_payload)
            raise GenericAgentExecutorError(
                "agent CLI returned an empty response." + build_trace_hint(trace_base),
                details=build_generic_agent_error_details(
                    failure_category="empty_agent_response",
                    trace_base=trace_base,
                    host_name=host_name,
                    command=command,
                    timeout_seconds=timeout_seconds,
                    response_source=response_source,
                ),
            )

        set_trace_manifest_finished(trace_payload, final_status="completed", started_monotonic=started_monotonic)
        trace_payload["returncode"] = completed.returncode
        trace_payload["response_source"] = response_source
        write_trace_manifest(paths["trace_manifest"], trace_payload)
        return response


def prepare_command_tokens(
    *,
    command: str,
    host_name: str,
    prompt_file: Path,
    input_file: Path,
    output_file: Path,
    repo_root: Path,
) -> list[str]:
    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except ValueError as exc:
        raise GenericAgentExecutorError(
            f"agent command could not be parsed: {exc}",
            details=build_generic_agent_error_details(
                failure_category="invalid_agent_command",
                trace_base=None,
                host_name=host_name,
                command=command,
                summary=str(exc),
            ),
        ) from exc
    replacements = {
        "{prompt_file}": str(prompt_file),
        "{input_file}": str(input_file),
        "{output_file}": str(output_file),
        "{repo_root}": str(repo_root),
    }
    resolved: list[str] = []
    for token in tokens:
        for marker, value in replacements.items():
            token = token.replace(marker, value)
        resolved.append(token)
    return resolved


def read_agent_response(*, stdout: str, output_file: Path) -> tuple[str, str]:
    if output_file.exists() and output_file.stat().st_size > 0:
        return output_file.read_text(encoding="utf-8", errors="replace"), "output_file"
    return stdout, "stdout"


def build_trace_paths(*, trace_base: Path | None, temp_dir: Path) -> dict[str, Path | None]:
    if trace_base is not None:
        trace_base.parent.mkdir(parents=True, exist_ok=True)
        return {
            "prompt_file": Path(f"{trace_base}.agent-task-prompt.md"),
            "input_file": Path(f"{trace_base}.agent-input.json"),
            "output_file": Path(f"{trace_base}.agent-output.json"),
            "stdout": Path(f"{trace_base}.agent-stdout.txt"),
            "stderr": Path(f"{trace_base}.agent-stderr.txt"),
            "last_message": Path(f"{trace_base}.agent-last-message.txt"),
            "command": Path(f"{trace_base}.agent-command.json"),
            "trace_manifest": Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"),
        }
    return {
        "prompt_file": temp_dir / "task-prompt.md",
        "input_file": temp_dir / "input.json",
        "output_file": temp_dir / "output.json",
        "stdout": None,
        "stderr": None,
        "last_message": temp_dir / "last-message.txt",
        "command": None,
        "trace_manifest": None,
    }


def serialize_trace_paths(paths: dict[str, Path | None]) -> dict[str, str]:
    return {key: str(path) for key, path in paths.items() if path is not None}


def require_path(path: Path | None) -> Path:
    if path is None:
        raise GenericAgentExecutorError("internal trace path is missing.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_generic_agent_error_details(
    *,
    failure_category: str,
    trace_base: Path | None,
    host_name: str,
    command: str | None,
    timeout_seconds: int | None = None,
    returncode: int | None = None,
    response_source: str | None = None,
    summary: str | None = None,
    response_excerpt: str | None = None,
    stdout_excerpt: str | None = None,
    stderr_excerpt: str | None = None,
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "failure_category": failure_category,
        "host_name": host_name,
    }
    if command is not None:
        details["command"] = command
    if trace_base is not None:
        details["trace_base"] = str(trace_base)
        details["trace_manifest"] = str(Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"))
    if timeout_seconds is not None:
        details["timeout_seconds"] = timeout_seconds
    if returncode is not None:
        details["returncode"] = returncode
    if response_source is not None:
        details["response_source"] = response_source
    if summary is not None:
        details["summary"] = summary
    if response_excerpt is not None:
        details["response_excerpt"] = response_excerpt
    if stdout_excerpt is not None:
        details["stdout_excerpt"] = stdout_excerpt
    if stderr_excerpt is not None:
        details["stderr_excerpt"] = stderr_excerpt
    return details


def serialize_prompt_executor_error(exc: Exception, *, trace_base: Path | None = None) -> dict[str, Any]:
    if isinstance(exc, GenericAgentExecutorError):
        payload = {
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
        if trace_base is not None:
            payload["trace_base"] = str(trace_base)
            payload["trace_manifest"] = str(Path(f"{trace_base}{TRACE_MANIFEST_SUFFIX}"))
        if exc.details:
            payload["failure_category"] = exc.details.get("failure_category")
            payload["generic_agent"] = exc.details
            payload["trace_base"] = exc.details.get("trace_base", payload.get("trace_base"))
            payload["trace_manifest"] = exc.details.get("trace_manifest", payload.get("trace_manifest"))
        return payload
    return local_executor.serialize_local_codex_error(exc, trace_base=trace_base)


def build_trace_hint(trace_base: Path | None) -> str:
    if trace_base is None:
        return ""
    return f" Trace manifest: {Path(f'{trace_base}{TRACE_MANIFEST_SUFFIX}')}"


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


def write_json_file(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text_file(path: Path | None, text: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
