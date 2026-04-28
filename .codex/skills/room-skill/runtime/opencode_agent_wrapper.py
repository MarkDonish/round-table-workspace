#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_MODEL = os.environ.get("OPENCODE_MODEL", "opencode/gpt-5-nano")
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_RETRIES = int(os.environ.get("OPENCODE_RETRIES", "2"))
DEFAULT_RETRY_DELAY_SECONDS = float(os.environ.get("OPENCODE_RETRY_DELAY_SECONDS", "2"))


def main() -> int:
    args = build_parser().parse_args()
    prompt = read_prompt()
    if not prompt.strip():
        print("opencode wrapper received an empty prompt", file=sys.stderr)
        return 2

    opencode_bin = resolve_opencode_bin(args.opencode_bin)
    if not opencode_bin:
        print("opencode executable not found on PATH; set --opencode-bin or OPENCODE_BIN", file=sys.stderr)
        return 127

    command = [
        opencode_bin,
        "run",
        "--model",
        args.model,
        "--dir",
        str(Path(args.dir).expanduser().resolve()),
    ]
    if args.pure:
        command.append("--pure")
    command.append(prompt)

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CLICOLOR", "0")
    env.setdefault("TERM", "dumb")
    data_home_context: tempfile.TemporaryDirectory[str] | None = None
    if args.data_home:
        data_home = Path(args.data_home).expanduser().resolve()
    elif args.isolated_data_home:
        data_home_context = tempfile.TemporaryDirectory(prefix="round-table-opencode-data-")
        data_home = Path(data_home_context.name)
    else:
        data_home = None
    if data_home:
        data_home.mkdir(parents=True, exist_ok=True)
        env["XDG_DATA_HOME"] = str(data_home)

    completed: subprocess.CompletedProcess[str] | None = None
    try:
        for attempt in range(args.retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(REPO_ROOT),
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=args.timeout_seconds,
                    check=False,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                print(
                    "opencode wrapper timed out after "
                    f"{args.timeout_seconds} seconds. stdout={ensure_text(exc.stdout)} stderr={ensure_text(exc.stderr)}",
                    file=sys.stderr,
                )
                return 124
            if completed.returncode == 0 or not should_retry(completed) or attempt >= args.retries:
                break
            print(
                "opencode wrapper retrying after transient local OpenCode failure "
                f"(attempt {attempt + 1}/{args.retries}): {summarize_failure(completed)}",
                file=sys.stderr,
            )
            time.sleep(args.retry_delay_seconds)
    finally:
        if data_home_context:
            data_home_context.cleanup()

    if completed is None:
        print("opencode wrapper did not launch opencode", file=sys.stderr)
        return 1

    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run OpenCode non-interactively for the round-table generic local-agent adapter. "
            "The prompt is passed as the opencode run message instead of a file attachment."
        )
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenCode model id to use.")
    parser.add_argument(
        "--opencode-bin",
        default=os.environ.get("OPENCODE_BIN"),
        help="Optional path to the opencode executable. Defaults to PATH lookup.",
    )
    parser.add_argument("--dir", default=str(REPO_ROOT), help="OpenCode working directory.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for the opencode run subprocess.",
    )
    parser.add_argument(
        "--no-pure",
        dest="pure",
        action="store_false",
        help="Do not pass --pure to opencode run.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Retries for transient local OpenCode CLI failures.",
    )
    parser.add_argument(
        "--retry-delay-seconds",
        type=float,
        default=DEFAULT_RETRY_DELAY_SECONDS,
        help="Delay between transient OpenCode CLI retries.",
    )
    parser.add_argument(
        "--data-home",
        help="Optional XDG_DATA_HOME for OpenCode state.",
    )
    parser.add_argument(
        "--isolated-data-home",
        action="store_true",
        help="Use an isolated temporary XDG_DATA_HOME for OpenCode state. This is diagnostic and may require first-run migration.",
    )
    parser.set_defaults(pure=True)
    return parser


def read_prompt() -> str:
    stdin_text = sys.stdin.read()
    if stdin_text.strip():
        return stdin_text
    prompt_file = os.environ.get("ROUND_TABLE_PROMPT_FILE", "").strip()
    if prompt_file:
        path = Path(prompt_file).expanduser().resolve()
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def resolve_opencode_bin(explicit: str | None) -> str | None:
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return str(path.resolve())
    return shutil.which("opencode")


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def should_retry(completed: subprocess.CompletedProcess[str]) -> bool:
    combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part).lower()
    transient_signals = [
        "pragma wal_checkpoint",
        "database is locked",
        "sqlite_busy",
        "sqlite busy",
        "failed to run the query",
    ]
    return any(signal in combined for signal in transient_signals)


def summarize_failure(completed: subprocess.CompletedProcess[str]) -> str:
    combined = " ".join(part.strip() for part in (completed.stderr, completed.stdout) if part and part.strip())
    condensed = " ".join(combined.split())
    if len(condensed) > 240:
        return condensed[:240] + "..."
    return condensed or f"exit code {completed.returncode}"


if __name__ == "__main__":
    sys.exit(main())
