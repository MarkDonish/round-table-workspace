#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check source-of-truth consistency across repo entry docs.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--output-markdown", help="Optional Markdown output path.")
    args = parser.parse_args()

    report = build_report()
    if args.output_json:
        write_json(Path(args.output_json).expanduser().resolve(), report)
    if args.output_markdown:
        write_text(Path(args.output_markdown).expanduser().resolve(), render_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def build_report() -> dict[str, Any]:
    agents = read("AGENTS.md")
    readme = read("README.md")
    launch = read("LAUNCH.md")
    source_paths = extract_primary_source_paths(agents)
    source_checks = [check_path(pattern) for pattern in source_paths]
    version_check = check_release_versions(readme, launch)
    quickstart = check_quickstart_commands(readme, launch)
    historical_boundary = check_historical_boundary(readme, launch, agents)
    required_docs = check_required_docs()
    checks = {
        "active_source_paths": {
            "ok": all(item["exists"] for item in source_checks),
            "items": source_checks,
        },
        "historical_boundary": historical_boundary,
        "release_version_consistency": version_check,
        "quickstart_commands": quickstart,
        "required_docs": required_docs,
    }
    ok = all(item["ok"] for item in checks.values())
    return {
        "ok": ok,
        "action": "source-truth-consistency-check",
        "checks": checks,
        "problems": collect_problems(checks),
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
        "docs/decision-quality-rubric.md",
    ]
    items = [{"path": path, "exists": (REPO_ROOT / path).is_file()} for path in docs]
    return {"ok": all(item["exists"] for item in items), "items": items}


def collect_problems(checks: dict[str, Any]) -> list[dict[str, Any]]:
    problems = []
    for name, check in checks.items():
        if not check["ok"]:
            problems.append({"check": name, "detail": check})
    return problems


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
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
