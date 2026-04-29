#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


RUNTIME_DIR = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parents[3]
DEFAULT_STATE_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "round-table-github-release-publication"
DEFAULT_REPOSITORY = "MarkDonish/round-table-workspace"
DEFAULT_TAG = "v0.2.0-alpha"
DEFAULT_RELEASE_DRAFT = "docs/releases/v0.2.0-alpha-github-release.md"
DEFAULT_RELEASE_WORKFLOW = ".github/workflows/publish-github-release.yml"
DEFAULT_WORKFLOW_RUN_LIMIT = 5


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(args)
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else Path(report["artifacts"]["json"])
    output_markdown = (
        Path(args.output_markdown).expanduser().resolve()
        if args.output_markdown
        else Path(report["artifacts"]["markdown"])
    )
    write_json(output_json, report)
    write_text(output_markdown, render_markdown(report))
    report["artifacts"]["json"] = str(output_json)
    report["artifacts"]["markdown"] = str(output_markdown)
    write_json(output_json, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict_published and report["summary"]["release_page_status"] != "published":
        return 1
    return 0 if report["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a GitHub Release page exists for a release tag and whether this host "
            "has local publication capability. This command does not create a release."
        )
    )
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY, help="GitHub repository in owner/name form.")
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Release tag to check.")
    parser.add_argument(
        "--release-draft",
        default=DEFAULT_RELEASE_DRAFT,
        help="Repo-relative copy-ready release draft path.",
    )
    parser.add_argument(
        "--release-workflow",
        default=DEFAULT_RELEASE_WORKFLOW,
        help="Repo-relative GitHub Actions workflow path for repository-side release publication.",
    )
    parser.add_argument(
        "--state-root",
        default=str(DEFAULT_STATE_ROOT),
        help="Directory for generated JSON/Markdown status evidence.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="Timeout for git, gh, and GitHub API checks.",
    )
    parser.add_argument(
        "--workflow-run-limit",
        type=int,
        default=DEFAULT_WORKFLOW_RUN_LIMIT,
        help="Maximum number of recent release workflow runs to inspect when authenticated access exists.",
    )
    parser.add_argument(
        "--strict-published",
        action="store_true",
        help="Exit non-zero unless the release page is confirmed published.",
    )
    parser.add_argument("--output-json", help="Optional path to write the report JSON.")
    parser.add_argument("--output-markdown", help="Optional path to write the report Markdown.")
    return parser


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    state_root = Path(args.state_root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)

    token_state = detect_token_state()
    gh_state = detect_gh_state(args.timeout_seconds)
    local_tag = check_local_tag(args.tag, args.timeout_seconds)
    release_draft = check_release_draft(args.release_draft)
    release_workflow = check_release_workflow(args.release_workflow)
    workflow_runs = check_github_actions_workflow_runs(
        repository=args.repository,
        release_workflow=args.release_workflow,
        token=token_state["token_value"],
        gh_state=gh_state,
        timeout_seconds=args.timeout_seconds,
        limit=args.workflow_run_limit,
    )
    gh_release = check_github_release_gh(
        repository=args.repository,
        tag=args.tag,
        gh_state=gh_state,
        timeout_seconds=args.timeout_seconds,
    )
    api_check = check_github_release_api(
        repository=args.repository,
        tag=args.tag,
        token=token_state["token_value"],
        timeout_seconds=args.timeout_seconds,
    )
    summary = build_summary(
        api_check=api_check,
        gh_release=gh_release,
        gh_state=gh_state,
        token_state=token_state,
        local_tag=local_tag,
        release_draft=release_draft,
        release_workflow=release_workflow,
        workflow_runs=workflow_runs,
        repository=args.repository,
        tag=args.tag,
    )
    report = {
        "ok": local_tag["exists"] and release_draft["exists"] and release_workflow["usable"],
        "action": "github-release-publication-check",
        "generated_at": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "repository": args.repository,
        "tag": args.tag,
        "release_urls": {
            "release_page": f"https://github.com/{args.repository}/releases/tag/{args.tag}",
            "new_release_page": f"https://github.com/{args.repository}/releases/new?tag={args.tag}",
            "api": f"https://api.github.com/repos/{args.repository}/releases/tags/{args.tag}",
        },
        "summary": summary,
        "checks": {
            "local_tag": local_tag,
            "release_draft": release_draft,
            "release_publication_workflow": release_workflow,
            "github_actions_workflow_runs": workflow_runs,
            "github_release_gh": gh_release,
            "github_api_release": redact_api_check(api_check),
            "local_publication_capability": {
                "gh": gh_state,
                "token": {
                    "present": token_state["present"],
                    "env_names_present": token_state["env_names_present"],
                },
            },
        },
        "interpretation": {
            "blocks_current_launch_scope": False,
            "why_not_p0": "GitHub Release page publication is a distribution/announcement step; the tag and local-first release are already reproducible.",
            "private_repo_rule": (
                "For a private repository, unauthenticated GitHub API 404 is inconclusive: it can mean not published, "
                "not authorized, or hidden by repository privacy. Use gh, a token, or the GitHub web UI to confirm."
            ),
        },
        "next_actions": build_next_actions(summary, args.repository, args.tag, args.release_draft, args.release_workflow),
        "artifacts": {
            "json": str(state_root / "github-release-publication-check.json"),
            "markdown": str(state_root / "github-release-publication-check.md"),
        },
    }
    return report


def build_summary(
    *,
    api_check: dict[str, Any],
    gh_release: dict[str, Any],
    gh_state: dict[str, Any],
    token_state: dict[str, Any],
    local_tag: dict[str, Any],
    release_draft: dict[str, Any],
    release_workflow: dict[str, Any],
    workflow_runs: dict[str, Any],
    repository: str,
    tag: str,
) -> dict[str, Any]:
    status_code = api_check.get("status_code")
    token_present = token_state["present"]
    if status_code == 200 or gh_release.get("published") is True:
        release_page_status = "published"
    elif gh_release.get("status") == "not_found":
        release_page_status = "not_published"
    elif gh_release.get("status") == "draft":
        release_page_status = "draft_not_published"
    elif status_code == 404 and token_present:
        release_page_status = "not_published"
    elif status_code == 404:
        release_page_status = "unknown_requires_authenticated_check"
    elif api_check.get("request_completed") is not True:
        release_page_status = "unknown_api_unreachable"
    else:
        release_page_status = "unknown_api_error"

    repo_automation_available = release_workflow["usable"]
    workflow_run_status = summarize_workflow_run_status(workflow_runs)
    can_publish = bool(token_present or gh_state.get("authenticated"))
    if release_page_status == "published":
        publication_decision = "published"
    elif workflow_run_status == "latest_success":
        publication_decision = "release_workflow_succeeded_release_page_requires_authenticated_confirmation"
    elif workflow_run_status in {"latest_failure", "latest_cancelled", "latest_timed_out"}:
        publication_decision = "release_workflow_failed"
    elif workflow_run_status == "latest_in_progress":
        publication_decision = "release_workflow_in_progress"
    elif can_publish:
        publication_decision = "ready_to_publish_from_capable_host"
    elif repo_automation_available:
        publication_decision = "ready_to_publish_from_repo_workflow"
    else:
        publication_decision = "blocked_on_local_release_capability"

    return {
        "release_page_status": release_page_status,
        "publication_decision": publication_decision,
        "repository": repository,
        "tag": tag,
        "local_tag_exists": local_tag["exists"],
        "release_draft_exists": release_draft["exists"],
        "release_publication_workflow_exists": release_workflow["exists"],
        "release_publication_workflow_usable": release_workflow["usable"],
        "repo_automation_available": repo_automation_available,
        "release_workflow_run_status": workflow_run_status,
        "release_workflow_latest_run": workflow_runs.get("latest_run"),
        "can_check_workflow_runs_from_this_host": workflow_runs.get("authenticated") is True,
        "can_attempt_automated_publication_from_this_host": can_publish,
        "gh_installed": gh_state.get("installed") is True,
        "gh_release_check_authenticated": gh_release.get("authenticated") is True,
        "gh_release_check_status": gh_release.get("status"),
        "github_token_present": token_present,
        "api_status_code": status_code,
        "api_check_authenticated": api_check.get("authenticated") is True,
    }


def build_next_actions(
    summary: dict[str, Any],
    repository: str,
    tag: str,
    release_draft: str,
    release_workflow: str,
) -> list[dict[str, str]]:
    status = summary["release_page_status"]
    if status == "published":
        return [
            {
                "priority": "P2",
                "task": "Keep release evidence fresh before broader support claims",
                "why": f"GitHub Release `{tag}` is already published; remaining work is host/provider validation expansion.",
            }
        ]
    workflow_status = summary.get("release_workflow_run_status")
    if workflow_status == "latest_success":
        return [
            {
                "priority": "P1",
                "task": f"Confirm GitHub Release `{tag}` page with authenticated release access",
                "why": "The latest release workflow run appears successful, but strict publication still requires release-page confirmation.",
            },
            {
                "priority": "P2",
                "task": "Validate additional real local agent hosts only when their authenticated CLIs exist",
                "why": "Missing host CLIs block only their own lanes, not the Codex local mainline.",
            },
        ]
    if workflow_status in {"latest_failure", "latest_cancelled", "latest_timed_out"}:
        return [
            {
                "priority": "P1",
                "task": f"Inspect and fix the failed GitHub Actions release workflow for `{tag}`",
                "why": f"`{release_workflow}` reported `{workflow_status}`; use the run URL in the checker output before attempting manual publication.",
            },
            {
                "priority": "P1",
                "task": f"Publish GitHub Release `{tag}` manually only if the workflow cannot be repaired quickly",
                "why": f"Use `{release_draft}` as the copy-ready fallback body at https://github.com/{repository}/releases/new?tag={tag}.",
            },
        ]
    if workflow_status == "latest_in_progress":
        return [
            {
                "priority": "P1",
                "task": f"Wait for the GitHub Actions release workflow for `{tag}` to finish",
                "why": "The latest release workflow run is still queued or running.",
            }
        ]
    if summary["can_attempt_automated_publication_from_this_host"]:
        return [
            {
                "priority": "P1",
                "task": f"Publish GitHub Release `{tag}` from this capable host",
                "why": "This host appears to have authenticated gh or token capability; use the checked release draft and rerun this check.",
            }
        ]
    if summary["repo_automation_available"]:
        return [
            {
                "priority": "P1",
                "task": f"Check or manually run the GitHub Actions release workflow for `{tag}` from an authenticated host",
                "why": (
                    f"`{release_workflow}` can publish or update the release with the repository GITHUB_TOKEN; this host "
                    "cannot list workflow runs without gh or a token."
                ),
            },
            {
                "priority": "P1",
                "task": f"Publish GitHub Release `{tag}` manually only if Actions is disabled",
                "why": f"Use `{release_draft}` as the copy-ready fallback body at https://github.com/{repository}/releases/new?tag={tag}.",
            },
            {
                "priority": "P2",
                "task": "Validate additional real local agent hosts only when their authenticated CLIs exist",
                "why": "Missing host CLIs block only their own lanes, not the Codex local mainline.",
            },
        ]
    return [
        {
            "priority": "P1",
            "task": f"Publish GitHub Release `{tag}` manually or from a release-capable host",
            "why": f"Use `{release_draft}` as the copy-ready body at https://github.com/{repository}/releases/new?tag={tag}.",
        },
        {
            "priority": "P2",
            "task": "Validate additional real local agent hosts only when their authenticated CLIs exist",
            "why": "Missing host CLIs block only their own lanes, not the Codex local mainline.",
        },
    ]


def check_local_tag(tag: str, timeout_seconds: int) -> dict[str, Any]:
    ref = run_command(["git", "rev-parse", "--verify", f"refs/tags/{tag}"], timeout_seconds=timeout_seconds)
    commit = run_command(["git", "rev-list", "-n", "1", tag], timeout_seconds=timeout_seconds) if ref["returncode"] == 0 else None
    return {
        "exists": ref["returncode"] == 0,
        "tag_ref_sha": ref["stdout"].strip() if ref["returncode"] == 0 else None,
        "target_commit_sha": commit["stdout"].strip() if commit and commit["returncode"] == 0 else None,
        "error": None if ref["returncode"] == 0 else (ref.get("stderr") or ref.get("stdout") or "tag_not_found"),
    }


def check_release_draft(release_draft: str) -> dict[str, Any]:
    path = REPO_ROOT / release_draft
    return {
        "exists": path.is_file(),
        "path": release_draft,
        "absolute_path": str(path),
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }


def check_release_workflow(release_workflow: str) -> dict[str, Any]:
    path = REPO_ROOT / release_workflow
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    uses_github_token = "GH_TOKEN: ${{ github.token }}" in text
    has_workflow_dispatch = "workflow_dispatch:" in text
    has_push_trigger = "push:" in text
    publishes_release = "gh release create" in text or "gh release edit" in text
    return {
        "exists": path.is_file(),
        "path": release_workflow,
        "absolute_path": str(path),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "usable": bool(path.is_file() and uses_github_token and has_workflow_dispatch and has_push_trigger and publishes_release),
        "uses_github_token": uses_github_token,
        "has_workflow_dispatch": has_workflow_dispatch,
        "has_push_trigger": has_push_trigger,
        "publishes_release": publishes_release,
    }


def check_github_actions_workflow_runs(
    *,
    repository: str,
    release_workflow: str,
    token: str | None,
    gh_state: dict[str, Any],
    timeout_seconds: int,
    limit: int,
) -> dict[str, Any]:
    workflow_file = Path(release_workflow).name
    if gh_state.get("installed") and gh_state.get("authenticated"):
        gh_check = run_command(
            [
                "gh",
                "run",
                "list",
                "--repo",
                repository,
                "--workflow",
                workflow_file,
                "--branch",
                "main",
                "--limit",
                str(limit),
                "--json",
                "databaseId,status,conclusion,event,headSha,displayTitle,createdAt,updatedAt,url,workflowName",
            ],
            timeout_seconds=timeout_seconds,
        )
        payload = parse_json_or_none(gh_check["stdout"]) if gh_check["returncode"] == 0 else None
        runs = payload if isinstance(payload, list) else []
        return {
            "request_completed": gh_check["returncode"] == 0,
            "authenticated": True,
            "method": "gh",
            "workflow_file": workflow_file,
            "run_count": len(runs),
            "latest_run": runs[0] if runs else None,
            "runs": runs,
            "error": None if gh_check["returncode"] == 0 else (gh_check["stderr"] or gh_check["stdout"] or "gh_run_list_failed"),
        }

    if token:
        workflow_id = quote(workflow_file, safe="")
        url = (
            f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_id}/runs"
            f"?branch=main&per_page={max(1, min(limit, 100))}"
        )
        api_check = check_github_json_api(url=url, token=token, timeout_seconds=timeout_seconds)
        payload = api_check.get("payload") if isinstance(api_check.get("payload"), dict) else {}
        runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
        return {
            "request_completed": api_check["request_completed"],
            "authenticated": True,
            "method": "github_api",
            "workflow_file": workflow_file,
            "status_code": api_check.get("status_code"),
            "run_count": len(runs) if isinstance(runs, list) else 0,
            "latest_run": normalize_workflow_run(runs[0]) if isinstance(runs, list) and runs else None,
            "runs": [normalize_workflow_run(run) for run in runs] if isinstance(runs, list) else [],
            "error": api_check.get("error"),
        }

    return {
        "request_completed": False,
        "authenticated": False,
        "method": "none",
        "workflow_file": workflow_file,
        "run_count": None,
        "latest_run": None,
        "runs": [],
        "error": "auth_required_for_workflow_runs",
        "next_check_commands": [
            f"gh run list --repo {repository} --workflow {workflow_file} --branch main --limit {limit}",
            f"gh release view {DEFAULT_TAG} --repo {repository}",
        ],
    }


def check_github_release_gh(
    *,
    repository: str,
    tag: str,
    gh_state: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    if not (gh_state.get("installed") and gh_state.get("authenticated")):
        return {
            "request_completed": False,
            "authenticated": False,
            "status": "auth_required",
            "found": None,
            "published": None,
            "payload": None,
            "error": "authenticated_gh_required",
        }

    gh_check = run_command(
        [
            "gh",
            "release",
            "view",
            tag,
            "--repo",
            repository,
            "--json",
            "tagName,name,isDraft,isPrerelease,publishedAt,targetCommitish,url",
        ],
        timeout_seconds=timeout_seconds,
    )
    payload = parse_json_or_none(gh_check["stdout"]) if gh_check["returncode"] == 0 else None
    found = gh_check["returncode"] == 0 and isinstance(payload, dict)
    is_draft = payload.get("isDraft") if found else None
    missing = is_gh_release_not_found(gh_check["stdout"], gh_check["stderr"])
    published = bool(found and is_draft is False)
    status = "published" if published else ("draft" if is_draft is True else ("not_found" if missing else "unknown_error"))
    return {
        "request_completed": True,
        "authenticated": True,
        "status": status,
        "found": found,
        "published": published,
        "is_draft": is_draft,
        "is_prerelease": payload.get("isPrerelease") if found else None,
        "tag_name": payload.get("tagName") if found else None,
        "name": payload.get("name") if found else None,
        "url": payload.get("url") if found else None,
        "published_at": payload.get("publishedAt") if found else None,
        "target_commitish": payload.get("targetCommitish") if found else None,
        "payload": payload,
        "error": None if found else (gh_check["stderr"] or gh_check["stdout"] or "gh_release_view_failed"),
    }


def is_gh_release_not_found(stdout: str, stderr: str) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    return "not found" in text or "http 404" in text or "release not found" in text


def detect_token_state() -> dict[str, Any]:
    values = {name: os.environ.get(name) for name in ("GITHUB_TOKEN", "GH_TOKEN") if os.environ.get(name)}
    token = values.get("GITHUB_TOKEN") or values.get("GH_TOKEN")
    return {
        "present": bool(token),
        "env_names_present": sorted(values),
        "token_value": token,
    }


def detect_gh_state(timeout_seconds: int) -> dict[str, Any]:
    path = shutil.which("gh")
    state: dict[str, Any] = {"installed": bool(path), "path": path}
    if not path:
        state["auth_status_checked"] = False
        state["authenticated"] = False
        state["blocker"] = "gh_not_installed"
        return state

    auth = run_command(["gh", "auth", "status"], timeout_seconds=timeout_seconds)
    state.update(
        {
            "auth_status_checked": True,
            "authenticated": auth["returncode"] == 0,
            "auth_stdout": auth["stdout"],
            "auth_stderr": auth["stderr"],
            "blocker": None if auth["returncode"] == 0 else "gh_auth_status_failed",
        }
    )
    return state


def check_github_release_api(
    *,
    repository: str,
    tag: str,
    token: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repository}/releases/tags/{tag}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "round-table-release-publication-check",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw.strip() else {}
            return {
                "request_completed": True,
                "authenticated": bool(token),
                "status_code": response.status,
                "payload": payload,
                "error": None,
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "request_completed": True,
            "authenticated": bool(token),
            "status_code": exc.code,
            "payload": parse_json_or_none(body),
            "error": body,
        }
    except URLError as exc:
        return {
            "request_completed": False,
            "authenticated": bool(token),
            "status_code": None,
            "payload": None,
            "error": str(exc),
        }
    except TimeoutError as exc:
        return {
            "request_completed": False,
            "authenticated": bool(token),
            "status_code": None,
            "payload": None,
            "error": str(exc),
        }


def check_github_json_api(*, url: str, token: str, timeout_seconds: int) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "round-table-release-publication-check",
    }
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            return {
                "request_completed": True,
                "authenticated": True,
                "status_code": response.status,
                "payload": json.loads(raw) if raw.strip() else {},
                "error": None,
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "request_completed": True,
            "authenticated": True,
            "status_code": exc.code,
            "payload": parse_json_or_none(body),
            "error": body,
        }
    except (URLError, TimeoutError) as exc:
        return {
            "request_completed": False,
            "authenticated": True,
            "status_code": None,
            "payload": None,
            "error": str(exc),
        }


def normalize_workflow_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "databaseId": run.get("databaseId") or run.get("id"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "event": run.get("event"),
        "headSha": run.get("headSha") or run.get("head_sha"),
        "displayTitle": run.get("displayTitle") or run.get("display_title"),
        "createdAt": run.get("createdAt") or run.get("created_at"),
        "updatedAt": run.get("updatedAt") or run.get("updated_at"),
        "url": run.get("url") or run.get("html_url"),
        "workflowName": run.get("workflowName") or run.get("name"),
    }


def summarize_workflow_run_status(workflow_runs: dict[str, Any]) -> str:
    if workflow_runs.get("authenticated") is not True:
        return "unknown_auth_required"
    latest_run = workflow_runs.get("latest_run")
    if not latest_run:
        return "no_runs_found"
    status = latest_run.get("status")
    conclusion = latest_run.get("conclusion")
    if status in {"queued", "in_progress", "requested", "waiting", "pending"}:
        return "latest_in_progress"
    if status == "completed" and conclusion == "success":
        return "latest_success"
    if status == "completed" and conclusion == "failure":
        return "latest_failure"
    if status == "completed" and conclusion == "cancelled":
        return "latest_cancelled"
    if status == "completed" and conclusion == "timed_out":
        return "latest_timed_out"
    return "latest_unknown"


def redact_api_check(api_check: dict[str, Any]) -> dict[str, Any]:
    payload = api_check.get("payload")
    if isinstance(payload, dict) and api_check.get("status_code") == 200:
        payload = {
            "id": payload.get("id"),
            "tag_name": payload.get("tag_name"),
            "name": payload.get("name"),
            "html_url": payload.get("html_url"),
            "draft": payload.get("draft"),
            "prerelease": payload.get("prerelease"),
            "published_at": payload.get("published_at"),
        }
    return {
        "request_completed": api_check.get("request_completed"),
        "authenticated": api_check.get("authenticated"),
        "status_code": api_check.get("status_code"),
        "payload": payload,
        "error": api_check.get("error"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# GitHub Release Publication Check",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Repository: `{report['repository']}`",
        f"- Tag: `{report['tag']}`",
        f"- Release page status: `{summary['release_page_status']}`",
        f"- Publication decision: `{summary['publication_decision']}`",
        f"- Blocks current launch scope: `{str(report['interpretation']['blocks_current_launch_scope']).lower()}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|---|---|",
        row("Local tag exists", str(summary["local_tag_exists"]).lower()),
        row("Release draft exists", str(summary["release_draft_exists"]).lower()),
        row("Release publication workflow exists", str(summary["release_publication_workflow_exists"]).lower()),
        row("Release publication workflow usable", str(summary["release_publication_workflow_usable"]).lower()),
        row("Repo automation available", str(summary["repo_automation_available"]).lower()),
        row("Release workflow run status", summary["release_workflow_run_status"]),
        row("Can check workflow runs from this host", str(summary["can_check_workflow_runs_from_this_host"]).lower()),
        row("gh release check authenticated", str(summary["gh_release_check_authenticated"]).lower()),
        row("gh release check status", summary["gh_release_check_status"]),
        row("GitHub API status", summary["api_status_code"]),
        row("API check authenticated", str(summary["api_check_authenticated"]).lower()),
        row("gh installed", str(summary["gh_installed"]).lower()),
        row("GitHub token present", str(summary["github_token_present"]).lower()),
        row("Can attempt automated publication from this host", str(summary["can_attempt_automated_publication_from_this_host"]).lower()),
        "",
        "## URLs",
        "",
        f"- Release page: {report['release_urls']['release_page']}",
        f"- New release page: {report['release_urls']['new_release_page']}",
        "",
        "## Next Actions",
        "",
        "| Priority | Task | Why |",
        "|---|---|---|",
    ]
    for action in report["next_actions"]:
        lines.append(row(action["priority"], action["task"], action["why"]))
    lines.append("")
    return "\n".join(lines)


def run_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def parse_json_or_none(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def row(*values: Any) -> str:
    return "| " + " | ".join(escape_cell(value) for value in values) + " |"


def escape_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
