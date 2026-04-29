#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
START = "<!-- rtw:generated-skill-summary:start -->"
END = "<!-- rtw:generated-skill-summary:end -->"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/check normalized skill summary sections.")
    parser.add_argument("command", choices=["generate", "dry-run", "check"])
    parser.add_argument("--skill", choices=["room", "debate", "all"], default="all")
    args = parser.parse_args()

    reports = []
    for skill in selected_skills(args.skill):
        reports.extend(process_skill(skill, command=args.command))

    ok = all(item["ok"] for item in reports)
    print(json.dumps({"ok": ok, "action": f"skill-{args.command}", "reports": reports}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def selected_skills(selection: str) -> list[str]:
    return ["room", "debate"] if selection == "all" else [selection]


def process_skill(skill: str, *, command: str) -> list[dict[str, Any]]:
    source = load_jsonish(REPO_ROOT / "skills_src" / f"{skill}.skill.yaml")
    shared = load_jsonish(REPO_ROOT / "skills_src" / "shared_rules.yaml")
    section = render_section(source, shared)
    targets = [source["canonical_codex_path"], *source["adapter_paths"]]
    reports = []
    for rel_target in targets:
        target = REPO_ROOT / rel_target
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        new_text = replace_section(text, section)
        changed = text != new_text
        if command == "generate" and target.exists() and changed:
            target.write_text(new_text, encoding="utf-8")
        report: dict[str, Any] = {
            "skill": skill,
            "target": rel_target,
            "exists": target.exists(),
            "has_generated_section": START in text and END in text,
            "changed": changed,
            "ok": target.exists() and (command != "check" or not changed),
        }
        if command == "dry-run" and changed:
            report["diff"] = list(
                difflib.unified_diff(
                    text.splitlines(),
                    new_text.splitlines(),
                    fromfile=rel_target,
                    tofile=f"{rel_target} (generated)",
                    lineterm="",
                )
            )
        reports.append(report)
    return reports


def render_section(source: dict[str, Any], shared: dict[str, Any]) -> str:
    lines = [
        START,
        "",
        "## Generated Skill Summary",
        "",
        f"- Skill id: `{source['skill_id']}`",
        f"- Source schema: `{source['schema_version']}`",
        f"- Entry commands: {', '.join(f'`{item}`' for item in source['entry_commands'])}",
        f"- Shared rules: {', '.join(f'`{item}`' for item in shared['shared_rules'])}",
        "- Claim boundary: fixture/checker passes are not host-live and not provider-live evidence.",
        "",
        "Canonical refs:",
    ]
    for ref in source["canonical_refs"]:
        lines.append(f"- `{ref}`")
    lines.extend(
        [
            "",
            "Host-specific notes:",
        ]
    )
    for host, note in source["host_specific"].items():
        lines.append(f"- `{host}`: {note}")
    lines.extend(["", END, ""])
    return "\n".join(lines)


def replace_section(text: str, section: str) -> str:
    if START in text and END in text:
        before = text[: text.index(START)].rstrip()
        after = text[text.index(END) + len(END) :].lstrip()
        if after:
            return before + "\n\n" + section.rstrip() + "\n\n" + after
        return before + "\n\n" + section.rstrip() + "\n"
    return text.rstrip() + "\n\n" + section.rstrip() + "\n"


def load_jsonish(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} must contain JSON-compatible YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain an object")
    return data


if __name__ == "__main__":
    sys.exit(main())
