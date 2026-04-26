#!/usr/bin/env python3
"""Write a repo-local development checkpoint.

This does not mutate Codex global memory. It creates durable project evidence
that future Codex, Claude Code, or generic local agent hosts can read after
cloning the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports" / "checkpoints" / "generated"

ACTIVE_SOURCE_TRUTH = [
    "AGENTS.md",
    "README.md",
    "LAUNCH.md",
    "docs/",
    "prompts/",
    "examples/",
    ".codex/skills/",
    ".claude/skills/",
]

HISTORICAL_OUTPUT_ROOTS = [
    "reports/",
    "artifacts/",
]


def main() -> int:
    args = build_parser().parse_args()
    report = build_checkpoint(args)
    output_json, output_markdown = resolve_output_paths(args, report)

    write_text(output_markdown, render_markdown(report))
    report["artifacts"]["markdown"] = str(output_markdown)
    report["artifacts"]["json"] = str(output_json)
    write_json(output_json, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a repo-local checkpoint for development continuity. "
            "The output is historical evidence under reports/checkpoints by default, not global agent memory."
        )
    )
    parser.add_argument(
        "--title",
        default="Development Checkpoint",
        help="Checkpoint title used in the report and generated filename.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated checkpoint files.",
    )
    parser.add_argument("--output-json", help="Optional explicit JSON output path.")
    parser.add_argument("--output-markdown", help="Optional explicit Markdown output path.")
    parser.add_argument("--topic", action="append", default=[], help="Key topic from the session. Repeatable.")
    parser.add_argument("--decision", action="append", default=[], help="Decision to persist. Repeatable.")
    parser.add_argument("--quote", action="append", default=[], help="Verbatim quote to preserve. Repeatable.")
    parser.add_argument("--completed", action="append", default=[], help="Completed item. Repeatable.")
    parser.add_argument("--partial", action="append", default=[], help="Partially completed item. Repeatable.")
    parser.add_argument("--unfinished", action="append", default=[], help="Unfinished item. Repeatable.")
    parser.add_argument("--blocked", action="append", default=[], help="Blocked item. Repeatable.")
    parser.add_argument("--next-task", action="append", default=[], help="Recommended next task. Repeatable.")
    parser.add_argument("--verification", action="append", default=[], help="Verification evidence. Repeatable.")
    parser.add_argument("--code-ref", action="append", default=[], help="Important code or doc reference. Repeatable.")
    parser.add_argument(
        "--include-release-readiness",
        action="store_true",
        help="Also run the checked-in release readiness gate and summarize the result.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Timeout for optional readiness subprocess checks.",
    )
    return parser


def build_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = utc_now_iso()
    git_state = build_git_state()
    release_readiness = None
    if args.include_release_readiness:
        release_readiness = run_release_readiness(timeout_seconds=args.timeout_seconds)

    return {
        "ok": True,
        "action": "development-checkpoint",
        "title": args.title,
        "generated_at": generated_at,
        "repo_root": str(REPO_ROOT),
        "memory_boundary": {
            "global_codex_memory_mutated": False,
            "repo_local_checkpoint": True,
            "checkpoint_is_source_of_truth": False,
            "why": (
                "The host-level Codex memory store may be read-only to this agent. "
                "This checkpoint persists project continuity inside the repository instead."
            ),
        },
        "source_boundary": {
            "active_source_truth": ACTIVE_SOURCE_TRUTH,
            "historical_output_roots": HISTORICAL_OUTPUT_ROOTS,
            "interpretation": (
                "Use docs, prompts, examples, and skill runtime as active source. "
                "Use reports/checkpoints as recoverable history."
            ),
        },
        "git_state": git_state,
        "session": {
            "topics": args.topic,
            "decisions": args.decision,
            "quotes": args.quote,
            "completed": args.completed,
            "partial": args.partial,
            "unfinished": args.unfinished,
            "blocked": args.blocked,
            "next_tasks": args.next_task,
            "verification": args.verification,
            "code_refs": args.code_ref,
        },
        "release_readiness": summarize_release_readiness(release_readiness),
        "artifacts": {
            "json": None,
            "markdown": None,
        },
    }


def build_git_state() -> dict[str, Any]:
    status = run_command(["git", "status", "-sb"])
    log = run_command(["git", "log", "--oneline", "-5"])
    remote = run_command(["git", "remote", "-v"])
    diff_stat = run_command(["git", "diff", "--stat"])
    cached_diff_stat = run_command(["git", "diff", "--cached", "--stat"])
    branch_line = first_non_empty_line(status["stdout"])
    return {
        "status_sb": status,
        "recent_log": log,
        "remote_v": remote,
        "diff_stat": diff_stat,
        "cached_diff_stat": cached_diff_stat,
        "dirty": any(
            line and not line.startswith("##")
            for line in status["stdout"].splitlines()
        ),
        "branch_line": branch_line,
    }


def run_release_readiness(*, timeout_seconds: int) -> dict[str, Any]:
    output_json = Path(os.environ.get("TMPDIR", "/tmp")) / (
        f"round-table-development-checkpoint-readiness-{os.getpid()}.json"
    )
    return run_json_command(
        [
            sys.executable,
            ".codex/skills/room-skill/runtime/release_readiness_check.py",
            "--include-fixture-runs",
            "--output-json",
            str(output_json),
        ],
        timeout_seconds=timeout_seconds,
    )


def summarize_release_readiness(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    release_scope = payload.get("release_scope") if isinstance(payload, dict) else {}
    return {
        "command": result.get("command"),
        "returncode": result.get("returncode"),
        "ok": result.get("ok"),
        "json_parse_ok": result.get("json_parse_ok"),
        "ship_decision": release_scope.get("ship_decision") if isinstance(release_scope, dict) else None,
        "p0_blockers": payload.get("p0_blockers") if isinstance(payload, dict) else None,
        "pass_criteria": payload.get("pass_criteria") if isinstance(payload, dict) else None,
        "non_blocking_gap_ids": [
            gap.get("id")
            for gap in payload.get("non_blocking_gaps", [])
            if isinstance(gap, dict) and gap.get("id")
        ]
        if isinstance(payload.get("non_blocking_gaps"), list)
        else [],
        "stderr": result.get("stderr"),
        "timed_out": result.get("timed_out", False),
    }


def resolve_output_paths(args: argparse.Namespace, report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = Path(args.output_dir).expanduser().resolve()
    slug = slugify(report["title"])
    timestamp = compact_utc_timestamp(report["generated_at"])
    default_base = output_dir / f"checkpoint-{timestamp}-{slug}"
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else default_base.with_suffix(".json")
    output_markdown = (
        Path(args.output_markdown).expanduser().resolve()
        if args.output_markdown
        else default_base.with_suffix(".md")
    )
    return output_json, output_markdown


def render_markdown(report: dict[str, Any]) -> str:
    session = report["session"]
    git_state = report["git_state"]
    lines = [
        f"# {report['title']}",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Branch: `{git_state.get('branch_line')}`",
        f"- Dirty tree: `{git_state.get('dirty')}`",
        "- Global Codex memory mutated: `False`",
        "- Checkpoint authority: historical continuity evidence, not protocol source of truth",
        "",
        "## Boundary",
        "",
        report["memory_boundary"]["why"],
        "",
        "Active source of truth:",
    ]
    lines.extend(f"- `{item}`" for item in report["source_boundary"]["active_source_truth"])
    lines.extend(
        [
            "",
            "Historical/output roots:",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in report["source_boundary"]["historical_output_roots"])

    add_section(lines, "Topics", session["topics"])
    add_section(lines, "Decisions", session["decisions"])
    add_section(lines, "Quotes", [f"> {quote}" for quote in session["quotes"]])
    add_section(lines, "Completed", session["completed"])
    add_section(lines, "Partial", session["partial"])
    add_section(lines, "Unfinished", session["unfinished"])
    add_section(lines, "Blocked", session["blocked"])
    add_section(lines, "Verification", session["verification"])
    add_section(lines, "Code References", session["code_refs"])
    add_section(lines, "Next Tasks", session["next_tasks"])

    lines.extend(
        [
            "",
            "## Git State",
            "",
            "```text",
            "$ git status -sb",
            git_state["status_sb"]["stdout"].rstrip(),
            "",
            "$ git log --oneline -5",
            git_state["recent_log"]["stdout"].rstrip(),
            "",
            "$ git remote -v",
            git_state["remote_v"]["stdout"].rstrip(),
            "```",
        ]
    )
    release_readiness = report.get("release_readiness")
    if release_readiness is not None:
        lines.extend(
            [
                "",
                "## Release Readiness Snapshot",
                "",
                f"- OK: `{release_readiness.get('ok')}`",
                f"- Ship decision: `{release_readiness.get('ship_decision')}`",
                f"- P0 blockers: `{release_readiness.get('p0_blockers')}`",
                f"- Non-blocking gaps: `{release_readiness.get('non_blocking_gap_ids')}`",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def add_section(lines: list[str], title: str, values: list[str]) -> None:
    if not values:
        return
    lines.extend(["", f"## {title}", ""])
    for value in values:
        if value.startswith("> "):
            lines.append(value)
        else:
            lines.append(f"- {value}")


def run_command(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "launch_failed": True,
        }


def run_json_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        payload = parse_json_object(completed.stdout)
        return {
            "command": command,
            "returncode": completed.returncode,
            "json_parse_ok": isinstance(payload, dict),
            "ok": completed.returncode == 0 and isinstance(payload, dict) and payload.get("ok") is not False,
            "payload": payload,
            "stderr": completed.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "json_parse_ok": False,
            "ok": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "stdout": ensure_text(exc.stdout).strip(),
            "stderr": ensure_text(exc.stderr).strip(),
        }
    except OSError as exc:
        return {
            "command": command,
            "returncode": None,
            "json_parse_ok": False,
            "ok": False,
            "launch_failed": True,
            "stderr": str(exc),
        }


def parse_json_object(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def first_non_empty_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    return slug or "checkpoint"


def compact_utc_timestamp(iso_value: str) -> str:
    return iso_value.replace("-", "").replace(":", "").replace(".", "").replace("Z", "Z")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
