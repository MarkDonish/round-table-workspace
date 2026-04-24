#!/usr/bin/env python3
"""Audit source-of-truth boundaries without mutating repository files."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


SOURCE_TRUTH_ROOTS = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "docs",
    "prompts",
    "examples",
    ".codex/skills",
    ".claude/skills",
    ".env.room.example",
    ".env.debate.example",
]

SUPPORTING_ACTIVE_ROOTS = [
    ".claude/README.md",
    ".claude/scripts",
]

BOUNDARY_GUARDRAIL_FILES = [
    "reports/README.md",
    "artifacts/README.md",
]

REQUIRED_SOURCE_ROOTS = [
    "AGENTS.md",
    "README.md",
    "docs",
    "prompts",
    "examples",
    ".codex/skills",
]

HISTORICAL_ROOTS = [
    "reports",
    "artifacts",
]


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "README.md").is_file():
            return candidate
    raise SystemExit("Could not locate repository root from script path.")


def iter_files(repo_root: Path, rel_paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for rel_path in rel_paths:
        path = repo_root / rel_path
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
    return sorted(files)


def rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def git_ls_files(repo_root: Path, pathspec: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", pathspec],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def classify_historical_path(path: str) -> str:
    if path.startswith("reports/"):
        return "historical_report"
    if path.startswith("artifacts/runtime/rooms/"):
        return "generated_room_runtime_output"
    if path.startswith("artifacts/runtime/"):
        return "runtime_evidence"
    if path.startswith("artifacts/fixtures/"):
        return "durable_fixture"
    if path.startswith("artifacts/rendered/"):
        return "rendered_export"
    if path.startswith("artifacts/"):
        return "artifact"
    return "unknown"


def build_report(repo_root: Path) -> dict:
    active_files = iter_files(
        repo_root,
        [*SOURCE_TRUTH_ROOTS, *SUPPORTING_ACTIVE_ROOTS, *BOUNDARY_GUARDRAIL_FILES],
    )
    historical_files = [
        path
        for path in iter_files(repo_root, HISTORICAL_ROOTS)
        if rel(path, repo_root) not in BOUNDARY_GUARDRAIL_FILES
    ]

    active_by_basename: dict[str, list[str]] = defaultdict(list)
    for path in active_files:
        active_by_basename[path.name].append(rel(path, repo_root))

    basename_collisions = []
    for path in historical_files:
        active_matches = active_by_basename.get(path.name, [])
        if not active_matches:
            continue
        historical_path = rel(path, repo_root)
        basename_collisions.append(
            {
                "basename": path.name,
                "historical_path": historical_path,
                "historical_class": classify_historical_path(historical_path),
                "active_matches": sorted(active_matches),
                "interpretation": "Use active_matches as current source; use historical_path only for archaeology or evidence.",
            }
        )

    artifact_runtime_room_files = [
        rel(path, repo_root)
        for path in historical_files
        if rel(path, repo_root).startswith("artifacts/runtime/rooms/")
    ]
    tracked_artifact_runtime_room_files = git_ls_files(repo_root, "artifacts/runtime/rooms")
    missing_required_roots = [
        root for root in REQUIRED_SOURCE_ROOTS if not (repo_root / root).exists()
    ]
    historical_class_counts = Counter(
        classify_historical_path(rel(path, repo_root)) for path in historical_files
    )

    return {
        "ok": not missing_required_roots,
        "action": "source_boundary_audit",
        "repo_root": str(repo_root),
        "source_truth_roots": SOURCE_TRUTH_ROOTS,
        "supporting_active_roots": SUPPORTING_ACTIVE_ROOTS,
        "boundary_guardrail_files": BOUNDARY_GUARDRAIL_FILES,
        "historical_roots": HISTORICAL_ROOTS,
        "summary": {
            "active_files": len(active_files),
            "historical_files": len(historical_files),
            "missing_required_roots": len(missing_required_roots),
            "basename_collisions": len(basename_collisions),
            "artifact_runtime_room_files": len(artifact_runtime_room_files),
            "tracked_artifact_runtime_room_files": len(tracked_artifact_runtime_room_files),
            "historical_classes": dict(sorted(historical_class_counts.items())),
        },
        "missing_required_roots": missing_required_roots,
        "basename_collisions": sorted(
            basename_collisions,
            key=lambda item: (item["basename"], item["historical_path"]),
        ),
        "artifact_runtime_room_files": sorted(artifact_runtime_room_files),
        "tracked_artifact_runtime_room_files": sorted(tracked_artifact_runtime_room_files),
        "interpretation": {
            "reports_and_artifacts_are_source": False,
            "collisions_are_errors": False,
            "local_mainline_requires_provider_url": False,
            "next_action": (
                "Start from AGENTS.md, README.md, docs/, prompts/, examples/, .codex/skills/, "
                "and .claude/skills/. Treat reports/ and artifacts/ matches as historical context unless "
                "a current source file explicitly promotes them."
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit source-of-truth boundaries without moving or editing reports/artifacts."
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path where the audit JSON should be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path(__file__).resolve())
    report = build_report(repo_root)
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
