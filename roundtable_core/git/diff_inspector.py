from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from roundtable_core.runtime.paths import assert_no_symlink_components


CATEGORY_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "database_migration": [
        re.compile(r"migrations?\/.*\.py$", re.IGNORECASE),
        re.compile(r".*\.sql$", re.IGNORECASE),
        re.compile(r"schema\.(prisma|sql|rb)$", re.IGNORECASE),
        re.compile(r".*migration.*", re.IGNORECASE),
    ],
    "security_auth": [
        re.compile(r".*(auth|login|session|jwt|crypto|permission|rbac|oauth).*", re.IGNORECASE),
        re.compile(r".*\.env(\..+)?$", re.IGNORECASE),
        re.compile(r".*(secret|key|token|credential).*", re.IGNORECASE),
    ],
    "api_endpoint": [
        re.compile(r".*(routes?|controllers?|endpoints?|handlers?|views?)\/.*", re.IGNORECASE),
        re.compile(r".*(api|graphql|openapi|proto|swagger).*", re.IGNORECASE),
    ],
    "frontend_ui": [
        re.compile(r".*\.(tsx|jsx|vue|svelte|css|scss|sass|less|html)$", re.IGNORECASE),
        re.compile(r".*(components?|styles?|ui|pages?|layouts?)\/.*", re.IGNORECASE),
    ],
    "test_spec": [
        re.compile(r".*(tests?|specs?|__tests?__)\/.*", re.IGNORECASE),
        re.compile(r".*(_test|\.test|\.spec)\..*", re.IGNORECASE),
    ],
    "config_ci": [
        re.compile(r"\.(github|gitlab|circleci)\/.*", re.IGNORECASE),
        re.compile(r"(Dockerfile|docker-compose.*|Makefile|\.gitlab-ci\.yml)$", re.IGNORECASE),
        re.compile(r"(pyproject\.toml|package\.json|Cargo\.toml|go\.mod|requirements\.txt)$", re.IGNORECASE),
    ],
}


@dataclass(frozen=True)
class GitDiffResult:
    ok: bool
    repo_root: str
    target_ref: str
    changed_files: list[str]
    categories: list[str]
    insertions: int
    deletions: int
    raw_diff: str
    summary_text: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "repo_root": self.repo_root,
            "target_ref": self.target_ref,
            "changed_files": self.changed_files,
            "categories": self.categories,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "raw_diff": self.raw_diff,
            "summary_text": self.summary_text,
            "error": self.error,
        }


class GitDiffInspector:
    def __init__(self, repo_path: str | Path | None = None, max_diff_chars: int = 12000) -> None:
        self.repo_path = Path(repo_path or os.getcwd()).resolve()
        assert_no_symlink_components(self.repo_path)
        self.max_diff_chars = max_diff_chars

    def inspect(
        self,
        *,
        staged: bool = False,
        ref: str | None = None,
        include_untracked: bool = False,
    ) -> GitDiffResult:
        if not (self.repo_path / ".git").exists():
            return GitDiffResult(
                ok=False,
                repo_root=str(self.repo_path),
                target_ref=ref or ("staged" if staged else "working_tree"),
                changed_files=[],
                categories=[],
                insertions=0,
                deletions=0,
                raw_diff="",
                summary_text="Target directory is not a Git repository root.",
                error="not_a_git_repository",
            )

        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if ref:
            cmd.append(ref)

        try:
            diff_proc = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            raw_diff = diff_proc.stdout if diff_proc.returncode == 0 else ""
            if diff_proc.returncode != 0 and diff_proc.stderr:
                return GitDiffResult(
                    ok=False,
                    repo_root=str(self.repo_path),
                    target_ref=ref or ("staged" if staged else "working_tree"),
                    changed_files=[],
                    categories=[],
                    insertions=0,
                    deletions=0,
                    raw_diff="",
                    summary_text=f"git diff failed: {diff_proc.stderr.strip()}",
                    error=diff_proc.stderr.strip(),
                )

            stat_cmd = cmd + ["--stat"]
            stat_proc = subprocess.run(
                stat_cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            stat_output = stat_proc.stdout.strip() if stat_proc.returncode == 0 else ""

            name_cmd = cmd + ["--name-only"]
            name_proc = subprocess.run(
                name_cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            changed_files = [f.strip() for f in name_proc.stdout.splitlines() if f.strip()]

            if include_untracked:
                untracked_proc = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                if untracked_proc.returncode == 0:
                    for line in untracked_proc.stdout.splitlines():
                        if line.startswith("?? "):
                            untracked_file = line[3:].strip()
                            if untracked_file not in changed_files:
                                changed_files.append(untracked_file)

            insertions, deletions = self._parse_stat_totals(stat_output)
            categories = self._categorize_files(changed_files)

            truncated_diff = raw_diff
            if len(raw_diff) > self.max_diff_chars:
                truncated_diff = (
                    raw_diff[: self.max_diff_chars]
                    + f"\n\n... [diff truncated: total {len(raw_diff)} chars, showing first {self.max_diff_chars}]"
                )

            summary = self._build_summary(changed_files, categories, insertions, deletions, stat_output)

            return GitDiffResult(
                ok=True,
                repo_root=str(self.repo_path),
                target_ref=ref or ("staged" if staged else "working_tree"),
                changed_files=changed_files,
                categories=categories,
                insertions=insertions,
                deletions=deletions,
                raw_diff=truncated_diff,
                summary_text=summary,
            )

        except subprocess.TimeoutExpired:
            return GitDiffResult(
                ok=False,
                repo_root=str(self.repo_path),
                target_ref=ref or "unknown",
                changed_files=[],
                categories=[],
                insertions=0,
                deletions=0,
                raw_diff="",
                summary_text="Git diff command timed out.",
                error="command_timeout",
            )
        except Exception as exc:
            return GitDiffResult(
                ok=False,
                repo_root=str(self.repo_path),
                target_ref=ref or "unknown",
                changed_files=[],
                categories=[],
                insertions=0,
                deletions=0,
                raw_diff="",
                summary_text=f"Failed to inspect git diff: {exc}",
                error=str(exc),
            )

    @staticmethod
    def _parse_stat_totals(stat_output: str) -> tuple[int, int]:
        insertions = 0
        deletions = 0
        if not stat_output:
            return insertions, deletions
        last_line = stat_output.splitlines()[-1]
        ins_match = re.search(r"(\d+)\s+insertion", last_line)
        del_match = re.search(r"(\d+)\s+deletion", last_line)
        if ins_match:
            insertions = int(ins_match.group(1))
        if del_match:
            deletions = int(del_match.group(1))
        return insertions, deletions

    @staticmethod
    def _categorize_files(files: Sequence[str]) -> list[str]:
        matched_categories: set[str] = set()
        for file_path in files:
            for cat_name, patterns in CATEGORY_PATTERNS.items():
                if any(pat.search(file_path) for pat in patterns):
                    matched_categories.add(cat_name)
        return sorted(matched_categories)

    @staticmethod
    def _build_summary(
        files: list[str],
        categories: list[str],
        insertions: int,
        deletions: int,
        stat_output: str,
    ) -> str:
        if not files:
            return "No modified or staged files detected in current working tree."
        cat_str = ", ".join(categories) if categories else "general_code"
        lines = [
            f"Changed files: {len(files)} (+{insertions}, -{deletions})",
            f"Detected categories: {cat_str}",
            "",
            "Top modified files:",
        ]
        for f in files[:8]:
            lines.append(f"  - {f}")
        if len(files) > 8:
            lines.append(f"  ... and {len(files) - 8} more files")
        return "\n".join(lines)


def inspect_git_diff(
    repo_path: str | Path | None = None,
    *,
    staged: bool = False,
    ref: str | None = None,
    include_untracked: bool = False,
) -> GitDiffResult:
    inspector = GitDiffInspector(repo_path)
    return inspector.inspect(staged=staged, ref=ref, include_untracked=include_untracked)
