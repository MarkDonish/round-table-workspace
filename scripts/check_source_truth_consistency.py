#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.runtime.paths import assert_no_symlink_components, resolve_checked_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check source-of-truth consistency across repo entry docs.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--output-markdown", help="Optional Markdown output path.")
    parser.add_argument(
        "--skip-claim-dashboard-freshness",
        action="store_true",
        help="Internal use while regenerating the claim dashboard; normal release-check must not pass this.",
    )
    args = parser.parse_args()

    report = build_report(skip_claim_dashboard_freshness=args.skip_claim_dashboard_freshness)
    if args.output_json:
        write_json(resolve_checked_path(args.output_json), report)
    if args.output_markdown:
        write_text(resolve_checked_path(args.output_markdown), render_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report(*, skip_claim_dashboard_freshness: bool = False) -> dict[str, Any]:
    agents = read("AGENTS.md")
    readme = read("README.md")
    launch = read("LAUNCH.md")
    source_paths = extract_primary_source_paths(agents)
    source_checks = [check_path(pattern) for pattern in source_paths]
    version_check = check_release_versions(readme, launch)
    quickstart = check_quickstart_commands(readme, launch)
    historical_boundary = check_historical_boundary(readme, launch, agents)
    required_docs = check_required_docs()
    claim_dashboard_freshness = (
        {
            "ok": True,
            "skipped": True,
            "reason": "claim dashboard is currently being regenerated",
            "report": "reports/claim-boundary-dashboard.md",
            "warnings": [],
            "problems": [],
        }
        if skip_claim_dashboard_freshness
        else check_claim_dashboard_freshness(readme)
    )
    protocol_versions = check_protocol_versioning(readme, launch)
    release_publication_defaults = check_release_publication_defaults(version_check)
    checks = {
        "active_source_paths": {
            "ok": all(item["exists"] for item in source_checks),
            "items": source_checks,
        },
        "historical_boundary": historical_boundary,
        "release_version_consistency": version_check,
        "quickstart_commands": quickstart,
        "required_docs": required_docs,
        "claim_dashboard_freshness": claim_dashboard_freshness,
        "protocol_versioning": protocol_versions,
        "release_publication_defaults": release_publication_defaults,
    }
    ok = all(item["ok"] for item in checks.values())
    return {
        "ok": ok,
        "action": "source-truth-consistency-check",
        "checks": checks,
        "problems": collect_problems(checks),
        "warnings": collect_warnings(checks),
    }


def extract_primary_source_paths(agents: str) -> list[str]:
    match = re.search(r"Primary source directories:\n\n(?P<body>.*?)(?:\n##|\nHistorical material)", agents, re.DOTALL)
    if not match:
        return []
    paths = []
    for line in match.group("body").splitlines():
        item = re.search(r"- `([^`]+)`", line)
        if item:
            paths.append(item.group(1))
    return paths


def check_path(pattern: str) -> dict[str, Any]:
    if "*" in pattern:
        matches = list(REPO_ROOT.glob(pattern))
        return {"path": pattern, "exists": bool(matches), "matches": [str(path.relative_to(REPO_ROOT)) for path in matches[:10]]}
    path = REPO_ROOT / pattern
    return {"path": pattern, "exists": path.exists(), "matches": [pattern] if path.exists() else []}


def check_release_versions(readme: str, launch: str) -> dict[str, Any]:
    readme_versions = sorted(set(re.findall(r"current release is `([^`]+)`", readme, flags=re.IGNORECASE)))
    launch_versions = sorted(set(re.findall(r"Current release notes: `docs/releases/([^`]+)\.md`", launch)))
    ok = bool(readme_versions and launch_versions and readme_versions[-1] == launch_versions[-1])
    return {"ok": ok, "readme_versions": readme_versions, "launch_versions": launch_versions}


def check_quickstart_commands(readme: str, launch: str) -> dict[str, Any]:
    commands = ["./rtw doctor", "./rtw room", "./rtw debate"]
    command_status = {command: command in readme or command in launch for command in commands}
    executable_status = {"./rtw": (REPO_ROOT / "rtw").is_file()}
    return {"ok": all(command_status.values()) and all(executable_status.values()), "commands": command_status, "executables": executable_status}


def check_historical_boundary(readme: str, launch: str, agents: str) -> dict[str, Any]:
    active_sections = "\n".join([readme, launch, agents])
    problems = []
    if "reports/` as an adapter layer" in active_sections:
        problems.append("reports_as_adapter_layer")
    if "artifacts/` as an adapter layer" in active_sections:
        problems.append("artifacts_as_adapter_layer")
    ok = "Historical" in agents and "reports/" in agents and "artifacts/" in agents and not problems
    return {"ok": ok, "problems": problems}


def check_required_docs() -> dict[str, Any]:
    docs = [
        "docs/release-candidate-scope.md",
        "docs/source-truth-map.md",
        "docs/protocol-spec.md",
        "docs/protocol-versioning.md",
        "docs/decision-quality-rubric.md",
    ]
    items = [{"path": path, "exists": (REPO_ROOT / path).is_file()} for path in docs]
    return {"ok": all(item["exists"] for item in items), "items": items}


def check_claim_dashboard_freshness(readme: str) -> dict[str, Any]:
    warnings = []
    problems = []
    report_path = REPO_ROOT / "reports" / "claim-boundary-dashboard.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    if "reports/claim-boundary-dashboard.md" in readme and not any(
        phrase in readme.lower()
        for phrase in ["snapshot", "generated", "run `./rtw evidence", "run `./rtw release-check"]
    ):
        warnings.append("readme_treats_claim_dashboard_report_as_current_authority")
    for marker in ["generated_at:", "source_commit:", "stale_after:"]:
        if marker not in report_text:
            problems.append(f"claim_dashboard_missing_{marker.rstrip(':')}")
    stale_after = extract_markdown_metadata(report_text, "stale_after")
    stale_after_dt = parse_iso_datetime(stale_after) if stale_after else None
    source_commit = extract_markdown_metadata(report_text, "source_commit")
    source_commit_is_ancestor: bool | None = None
    source_commit_ahead_count: int | None = None
    source_commit_changed_paths: list[str] | None = None
    if stale_after and stale_after_dt is None:
        problems.append("claim_dashboard_stale_after_unparseable")
    if stale_after_dt and stale_after_dt <= datetime.now(timezone.utc):
        problems.append("claim_dashboard_stale")
    if not source_commit:
        problems.append("claim_dashboard_source_commit_missing")
    elif source_commit.endswith("+dirty"):
        problems.append("claim_dashboard_source_commit_dirty")
    elif not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        problems.append("claim_dashboard_source_commit_unparseable")
    else:
        source_commit_is_ancestor = git_commit_is_ancestor(source_commit)
        if source_commit_is_ancestor is False:
            problems.append("claim_dashboard_source_commit_not_ancestor")
        elif source_commit_is_ancestor is None:
            problems.append("claim_dashboard_source_commit_unverifiable")
        else:
            source_commit_ahead_count = git_commit_ahead_count(source_commit)
            if source_commit_ahead_count is None:
                problems.append("claim_dashboard_source_commit_distance_unverifiable")
            elif source_commit_ahead_count > 0:
                source_commit_changed_paths = git_changed_paths_since(source_commit)
                if source_commit_changed_paths is None:
                    problems.append("claim_dashboard_source_commit_diff_unverifiable")
                elif not claim_dashboard_diff_only(source_commit_changed_paths):
                    problems.append("claim_dashboard_source_commit_stale")
    return {
        "ok": report_path.is_file() and not problems,
        "report": "reports/claim-boundary-dashboard.md",
        "stale_after": stale_after,
        "source_commit": source_commit,
        "source_commit_is_ancestor": source_commit_is_ancestor,
        "source_commit_ahead_count": source_commit_ahead_count,
        "source_commit_changed_paths": source_commit_changed_paths,
        "warnings": warnings,
        "problems": problems,
    }


def extract_markdown_metadata(text: str, key: str) -> str | None:
    match = re.search(rf"^> {re.escape(key)}:\s*`([^`]+)`", text, flags=re.MULTILINE)
    return match.group(1) if match else None


def parse_iso_datetime(value: str) -> datetime | None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def git_commit_is_ancestor(commit: str) -> bool | None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if head.returncode != 0:
        return None
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head.stdout.strip()],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    return None


def git_commit_ahead_count(commit: str) -> int | None:
    completed = subprocess.run(
        ["git", "rev-list", "--count", f"{commit}..HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    try:
        return int(completed.stdout.strip())
    except ValueError:
        return None


def git_changed_paths_since(commit: str) -> list[str] | None:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{commit}..HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def claim_dashboard_diff_only(paths: list[str]) -> bool:
    allowed = {"reports/claim-boundary-dashboard.md", "reports/claim-boundary-dashboard.json"}
    return bool(paths) and all(path in allowed for path in paths)


def check_protocol_versioning(readme: str, launch: str) -> dict[str, Any]:
    doc_exists = (REPO_ROOT / "docs" / "protocol-versioning.md").is_file()
    warnings = []
    release_pattern = r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-.][A-Za-z0-9]+)*"
    if re.search(release_pattern, readme) and "0.1.0" in readme and "protocol-versioning" not in readme:
        warnings.append("readme_mentions_release_and_schema_versions_without_versioning_link")
    if re.search(release_pattern, launch) and "protocol-versioning" not in launch:
        warnings.append("launch_mentions_release_without_versioning_link")
    return {
        "ok": doc_exists,
        "doc_exists": doc_exists,
        "warnings": warnings,
    }


def check_release_publication_defaults(version_check: dict[str, Any]) -> dict[str, Any]:
    current_release = version_check.get("readme_versions", [None])[-1] if version_check.get("readme_versions") else None
    expected_draft = f"docs/releases/{current_release}-github-release.md" if current_release else None
    publication_check = read(".codex/skills/room-skill/runtime/github_release_publication_check.py")
    extractor = read(".codex/skills/room-skill/runtime/extract_github_release_body.py")
    workflow = read(".github/workflows/publish-github-release.yml")
    helper_tag = extract_python_constant(publication_check, "DEFAULT_TAG")
    helper_draft = extract_python_constant(publication_check, "DEFAULT_RELEASE_DRAFT")
    extractor_draft = extract_python_constant(extractor, "DEFAULT_RELEASE_DRAFT")
    workflow_tag = extract_workflow_default(workflow, "tag")
    workflow_draft = extract_workflow_default(workflow, "release_draft")
    workflow_push_can_publish = workflow_push_trigger_can_publish(workflow)
    workflow_has_tag_checkout_guard = all(
        marker in workflow
        for marker in [
            "Verify checkout matches release tag",
            'tag_commit="$(git rev-list -n 1 "$TAG")"',
            'head_commit="$(git rev-parse HEAD)"',
            "release checkout does not match tag",
        ]
    )
    workflow_watches_gate_scripts = all(
        path in workflow
        for path in [
            ".codex/skills/room-skill/runtime/github_release_publication_check.py",
            "scripts/check_source_truth_consistency.py",
            "scripts/release_check.py",
        ]
    )
    workflow_has_pre_publish_release_guards = all(
        marker in workflow
        for marker in [
            "Run release guards before publication",
            "python3 scripts/check_source_truth_consistency.py",
            "./rtw release-check",
            "--include-fixtures",
            "--strict-git-clean",
            "$RUNNER_TEMP/rtw-publish-release-check",
        ]
    )
    problems = []
    warnings = []
    if current_release and helper_tag != current_release:
        problems.append("github_release_publication_check_default_tag_mismatch")
    if expected_draft and helper_draft != expected_draft:
        problems.append("github_release_publication_check_default_draft_mismatch")
    if expected_draft and extractor_draft != expected_draft:
        problems.append("extract_github_release_body_default_draft_mismatch")
    if current_release and workflow_tag != current_release:
        problems.append("publish_github_release_workflow_default_tag_mismatch")
    if expected_draft and workflow_draft != expected_draft:
        problems.append("publish_github_release_workflow_default_draft_mismatch")
    if workflow_push_can_publish:
        problems.append("publish_github_release_workflow_push_publication_risk")
    if not workflow_has_tag_checkout_guard:
        problems.append("publish_github_release_workflow_missing_tag_checkout_guard")
    if not workflow_watches_gate_scripts:
        problems.append("publish_github_release_workflow_missing_gate_script_paths")
    if not workflow_has_pre_publish_release_guards:
        problems.append("publish_github_release_workflow_missing_pre_publish_release_guards")
    return {
        "ok": not problems,
        "current_release": current_release,
        "expected_release_draft": expected_draft,
        "github_release_publication_check_default_tag": helper_tag,
        "github_release_publication_check_default_draft": helper_draft,
        "extract_github_release_body_default_draft": extractor_draft,
        "workflow_default_tag": workflow_tag,
        "workflow_default_release_draft": workflow_draft,
        "workflow_push_trigger_can_publish": workflow_push_can_publish,
        "workflow_has_tag_checkout_guard": workflow_has_tag_checkout_guard,
        "workflow_has_pre_publish_release_guards": workflow_has_pre_publish_release_guards,
        "workflow_watches_gate_scripts": workflow_watches_gate_scripts,
        "problems": problems,
        "warnings": warnings,
    }


def extract_python_constant(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}\s*=\s*[\"']([^\"']+)[\"']", text, flags=re.MULTILINE)
    return match.group(1) if match else None


def extract_workflow_default(text: str, input_name: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != f"{input_name}:":
            continue
        base_indent = len(line) - len(line.lstrip())
        for child in lines[index + 1 :]:
            if not child.strip():
                continue
            child_indent = len(child) - len(child.lstrip())
            if child_indent <= base_indent:
                break
            if child.strip().startswith("default:"):
                value = child.split(":", 1)[1].strip()
                return value.strip("\"'")
    return None


def workflow_push_trigger_can_publish(text: str) -> bool:
    has_push_trigger = "push:" in text
    publishes_release = "gh release create" in text or "gh release edit" in text
    push_defaults_to_dry_run = "DRY_RUN_INPUT:-true" in text
    return has_push_trigger and publishes_release and not push_defaults_to_dry_run


def collect_problems(checks: dict[str, Any]) -> list[dict[str, Any]]:
    problems = []
    for name, check in checks.items():
        if not check["ok"]:
            problems.append({"check": name, "detail": check})
    return problems


def collect_warnings(checks: dict[str, Any]) -> list[dict[str, Any]]:
    warnings = []
    for name, check in checks.items():
        for warning in check.get("warnings", []):
            warnings.append({"check": name, "warning": warning})
    return warnings


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Source Truth Consistency Check", "", f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`", ""]
    for name, check in report["checks"].items():
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- ok: `{check['ok']}`")
        lines.append("")
    if report["problems"]:
        lines.append("## Problems")
        lines.append("")
        for problem in report["problems"]:
            lines.append(f"- `{problem['check']}`")
    if report.get("warnings"):
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for warning in report["warnings"]:
            lines.append(f"- `{warning['check']}`: {warning['warning']}")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    assert_no_symlink_components(path, include_leaf=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    assert_no_symlink_components(path, include_leaf=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
