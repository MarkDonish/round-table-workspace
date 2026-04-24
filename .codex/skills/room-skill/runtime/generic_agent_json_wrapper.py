#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chat_completions_executor import parse_json_from_text
import local_codex_executor as local_executor


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_TIMEOUT_SECONDS = 900


class JsonWrapperError(Exception):
    pass


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        payload = run_wrapped_agent(args)
    except JsonWrapperError as exc:
        error = {
            "ok": False,
            "action": "generic-agent-json-wrapper",
            "error": str(exc),
            "generated_at": utc_now_iso(),
        }
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    final_output = os.environ.get("ROUND_TABLE_OUTPUT_JSON", "").strip()
    if final_output:
        final_output_path = Path(final_output).expanduser().resolve()
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
        final_output_path.write_text(output_text, encoding="utf-8")
    sys.stdout.write(output_text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Wrap a local agent command and normalize its noisy stdout or file output into one JSON object. "
            "Use this when a third-party agent tends to emit Markdown fences or explanatory text around JSON."
        )
    )
    parser.add_argument(
        "--agent-command",
        required=True,
        help=(
            "Wrapped local agent command. The wrapper passes the task prompt on stdin and supports "
            "{prompt_file}, {input_file}, {output_file}, {raw_output_file}, and {repo_root} placeholders."
        ),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for the wrapped agent command.",
    )
    parser.add_argument(
        "--no-stdin",
        action="store_true",
        help="Do not pass the task prompt on stdin. Use only for agents that read ROUND_TABLE_PROMPT_FILE directly.",
    )
    parser.add_argument(
        "--raw-output-file",
        help="Optional raw output capture path. Defaults to a temporary file outside the repository.",
    )
    return parser


def run_wrapped_agent(args: argparse.Namespace) -> dict[str, Any]:
    task_prompt = read_task_prompt()
    final_output_path = resolve_optional_path(os.environ.get("ROUND_TABLE_OUTPUT_JSON", ""))
    prompt_file = resolve_optional_path(os.environ.get("ROUND_TABLE_PROMPT_FILE", ""))
    input_file = resolve_optional_path(os.environ.get("ROUND_TABLE_INPUT_JSON", ""))
    repo_root = Path(os.environ.get("ROUND_TABLE_REPO_ROOT", str(REPO_ROOT))).expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="round-table-json-wrapper-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        raw_output_path = (
            Path(args.raw_output_file).expanduser().resolve()
            if args.raw_output_file
            else temp_dir / "wrapped-agent-output.txt"
        )
        raw_output_path.parent.mkdir(parents=True, exist_ok=True)

        command_tokens = prepare_wrapped_command_tokens(
            command=args.agent_command,
            prompt_file=prompt_file,
            input_file=input_file,
            final_output_file=final_output_path,
            raw_output_file=raw_output_path,
            repo_root=repo_root,
        )
        env = os.environ.copy()
        if final_output_path:
            env["ROUND_TABLE_FINAL_OUTPUT_JSON"] = str(final_output_path)
        env["ROUND_TABLE_OUTPUT_JSON"] = str(raw_output_path)
        env["ROUND_TABLE_WRAPPER_RAW_OUTPUT_JSON"] = str(raw_output_path)
        env["ROUND_TABLE_JSON_WRAPPER"] = "1"

        try:
            completed = subprocess.run(
                command_tokens,
                input=None if args.no_stdin else task_prompt,
                cwd=str(repo_root),
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=args.timeout_seconds,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise JsonWrapperError(
                "wrapped agent timed out after "
                f"{args.timeout_seconds} seconds. stdout={local_executor.build_text_excerpt(ensure_text(exc.stdout))} "
                f"stderr={local_executor.build_text_excerpt(ensure_text(exc.stderr))}"
            ) from exc
        except OSError as exc:
            raise JsonWrapperError(f"wrapped agent could not be launched: {exc}") from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if completed.returncode != 0:
            raise JsonWrapperError(
                "wrapped agent exited with code "
                f"{completed.returncode}. stdout={local_executor.build_text_excerpt(stdout)} "
                f"stderr={local_executor.build_text_excerpt(stderr)}"
            )

        candidates = build_response_candidates(
            stdout=stdout,
            raw_output_file=raw_output_path,
            final_output_file=final_output_path,
        )
        payload, _source = parse_first_json_payload(candidates)
        return payload


def read_task_prompt() -> str:
    stdin_text = sys.stdin.read()
    if stdin_text.strip():
        return stdin_text
    prompt_file = os.environ.get("ROUND_TABLE_PROMPT_FILE", "").strip()
    if prompt_file:
        path = Path(prompt_file).expanduser().resolve()
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def prepare_wrapped_command_tokens(
    *,
    command: str,
    prompt_file: Path | None,
    input_file: Path | None,
    final_output_file: Path | None,
    raw_output_file: Path,
    repo_root: Path,
) -> list[str]:
    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except ValueError as exc:
        raise JsonWrapperError(f"wrapped agent command could not be parsed: {exc}") from exc
    replacements = {
        "{prompt_file}": str(prompt_file or ""),
        "{input_file}": str(input_file or ""),
        "{output_file}": str(final_output_file or raw_output_file),
        "{final_output_file}": str(final_output_file or ""),
        "{raw_output_file}": str(raw_output_file),
        "{repo_root}": str(repo_root),
    }
    resolved: list[str] = []
    for token in tokens:
        for marker, value in replacements.items():
            token = token.replace(marker, value)
        resolved.append(token)
    if not resolved:
        raise JsonWrapperError("wrapped agent command resolved to an empty command.")
    return resolved


def build_response_candidates(
    *,
    stdout: str,
    raw_output_file: Path,
    final_output_file: Path | None,
) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    if raw_output_file.exists() and raw_output_file.stat().st_size > 0:
        candidates.append(("raw_output_file", raw_output_file.read_text(encoding="utf-8", errors="replace")))
    if final_output_file and final_output_file.exists() and final_output_file.stat().st_size > 0:
        candidates.append(("final_output_file_before_cleanup", final_output_file.read_text(encoding="utf-8", errors="replace")))
    if stdout.strip():
        candidates.append(("stdout", stdout))
    return candidates


def parse_first_json_payload(candidates: list[tuple[str, str]]) -> tuple[dict[str, Any], str]:
    errors: list[str] = []
    for source, text in candidates:
        for candidate in candidate_json_texts(text):
            try:
                payload = parse_json_from_text(candidate)
                return payload, source
            except Exception as exc:  # Keep trying alternate candidates.
                errors.append(f"{source}: {exc}")
    raise JsonWrapperError("wrapped agent output did not contain a parseable JSON object. " + "; ".join(errors))


def candidate_json_texts(text: str) -> list[str]:
    candidates = [text]
    repaired = local_executor.repair_runtime_json_text(text)
    if repaired and repaired != text:
        candidates.append(repaired)
    # Agents may emit telemetry JSON before the final answer; prefer the last
    # balanced object after whole-response parsing fails.
    extracted = list(reversed(extract_balanced_json_objects(text)))
    candidates.extend(extracted)
    return candidates


def extract_balanced_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    for start_index, char in enumerate(text):
        if char != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start_index, len(text)):
            current = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    objects.append(text[start_index : index + 1])
                    break
    return objects


def resolve_optional_path(value: str) -> Path | None:
    stripped = value.strip()
    if not stripped:
        return None
    return Path(stripped).expanduser().resolve()


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
