#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from roundtable_core.agents.registry import load_agent_registry


DOC_PATH = REPO_ROOT / "docs" / "agent-registry.md"
REGISTRY_PATH = REPO_ROOT / "agents" / "registry.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check docs/agent-registry.md against agents/registry.json.")
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
    registry = load_agent_registry(REGISTRY_PATH)
    doc_agents = parse_registry_doc(DOC_PATH)
    registry_ids = set(registry)
    doc_ids = set(doc_agents)
    missing_in_doc = sorted(registry_ids - doc_ids)
    missing_in_json = sorted(doc_ids - registry_ids)
    field_mismatches: list[dict[str, Any]] = []
    for agent_id in sorted(registry_ids & doc_ids):
        doc_entry = doc_agents[agent_id]
        json_entry = registry[agent_id]
        for field in [
            "short_name",
            "structural_role",
            "expression",
            "strength",
            "default_excluded",
            "task_types",
            "stage_fit",
            "sub_problem_tags",
        ]:
            if doc_entry.get(field) != json_entry.get(field):
                field_mismatches.append(
                    {
                        "agent_id": agent_id,
                        "field": field,
                        "doc": doc_entry.get(field),
                        "json": json_entry.get(field),
                    }
                )

    missing_lens_fields = [
        agent_id
        for agent_id, entry in registry.items()
        if not entry.get("display_name")
        or not entry.get("cognitive_lens")
        or not entry.get("useful_when")
        or not entry.get("avoid")
        or not entry.get("style_rule")
    ]

    return {
        "ok": not missing_in_doc and not missing_in_json and not field_mismatches and not missing_lens_fields,
        "action": "agent-registry-sync-check",
        "registry": str(REGISTRY_PATH.relative_to(REPO_ROOT)),
        "doc": str(DOC_PATH.relative_to(REPO_ROOT)),
        "registry_agent_count": len(registry),
        "doc_agent_count": len(doc_agents),
        "missing_in_doc": missing_in_doc,
        "missing_in_json": missing_in_json,
        "field_mismatches": field_mismatches,
        "missing_lens_fields": missing_lens_fields,
    }


def parse_registry_doc(path: Path) -> dict[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("| agent_id | short_name | structural_role |"):
            start = index + 2
            break
    if start is None:
        return {}

    entries: dict[str, dict[str, Any]] = {}
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [clean_cell(part) for part in stripped.strip("|").split("|")]
        if len(cells) != 9:
            continue
        entries[cells[0]] = {
            "agent_id": cells[0],
            "short_name": cells[1],
            "structural_role": cells[2],
            "expression": cells[3],
            "strength": cells[4],
            "default_excluded": cells[5] == "yes",
            "task_types": split_csv(cells[6]),
            "stage_fit": split_csv(cells[7]),
            "sub_problem_tags": split_csv(cells[8]),
        }
    return entries


def clean_cell(value: str) -> str:
    return re.sub(r"^`|`$", "", value.strip())


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Agent Registry Sync Check", "", f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`", ""]
    for field in ["missing_in_doc", "missing_in_json", "field_mismatches", "missing_lens_fields"]:
        lines.append(f"- `{field}`: `{len(report[field])}`")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
