#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_RELEASE_DRAFT = "docs/releases/v0.1.2-github-release.md"
DEFAULT_OUTPUT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-github-release-body.md"


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(args)
    if report["ok"]:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report["release_body"] + "\n", encoding="utf-8")
        report["artifacts"]["release_body"] = str(output_path)
        report.pop("release_body")

    if args.output_json:
        output_json = Path(args.output_json).expanduser().resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["artifacts"]["json"] = str(output_json)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract the copy-ready GitHub Release body from the checked-in release draft. "
            "This keeps GitHub Actions publication and manual publication on the same source text."
        )
    )
    parser.add_argument(
        "--release-draft",
        default=DEFAULT_RELEASE_DRAFT,
        help="Repo-relative release draft path containing a fenced body under '## Release Body'.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the extracted Markdown release body.",
    )
    parser.add_argument("--output-json", help="Optional path to write extraction metadata JSON.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    draft_path = (REPO_ROOT / args.release_draft).resolve()
    report: dict[str, Any] = {
        "ok": False,
        "action": "extract-github-release-body",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "release_draft": args.release_draft,
        "release_draft_absolute_path": str(draft_path),
        "artifacts": {
            "release_body": str(Path(args.output).expanduser().resolve()),
            "json": None,
        },
    }
    if not draft_path.is_file():
        report["error"] = "release_draft_not_found"
        return report

    text = draft_path.read_text(encoding="utf-8")
    extraction = extract_release_body(text)
    if not extraction["ok"]:
        report["error"] = extraction["error"]
        return report

    release_body = extraction["body"]
    validation_error = validate_release_body(release_body)
    if validation_error:
        report["error"] = validation_error
        return report

    report.update(
        {
            "ok": True,
            "error": None,
            "release_body": release_body,
            "summary": {
                "line_count": len(release_body.splitlines()),
                "char_count": len(release_body),
                "starts_with_h1": release_body.lstrip().startswith("# "),
                "source_start_line": extraction["source_start_line"],
                "source_end_line": extraction["source_end_line"],
            },
        }
    )
    return report


def extract_release_body(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    heading_index = next((index for index, line in enumerate(lines) if line.strip() == "## Release Body"), None)
    if heading_index is None:
        return {"ok": False, "error": "release_body_heading_not_found"}

    fence_index = None
    fence = None
    for index in range(heading_index + 1, len(lines)):
        line = lines[index]
        if not line.strip():
            continue
        match = re.match(r"^(`{3,})[A-Za-z0-9_-]*\s*$", line.strip())
        if not match:
            return {"ok": False, "error": "release_body_fence_not_found_after_heading"}
        fence_index = index
        fence = match.group(1)
        break
    if fence_index is None or fence is None:
        return {"ok": False, "error": "release_body_fence_not_found_after_heading"}

    body_lines: list[str] = []
    for index in range(fence_index + 1, len(lines)):
        if lines[index].strip() == fence:
            body = "\n".join(body_lines).strip()
            return {
                "ok": True,
                "body": body,
                "source_start_line": fence_index + 2,
                "source_end_line": index,
            }
        body_lines.append(lines[index])

    return {"ok": False, "error": "release_body_closing_fence_not_found"}


def validate_release_body(release_body: str) -> str | None:
    if not release_body.strip():
        return "release_body_empty"
    if not release_body.lstrip().startswith("# "):
        return "release_body_missing_h1"
    if "Current launch decision:" not in release_body:
        return "release_body_missing_launch_decision"
    if "docs/releases/v0.1.2.md" not in release_body:
        return "release_body_missing_canonical_release_notes"
    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
