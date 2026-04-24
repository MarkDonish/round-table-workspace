#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

SKILL_REQUIREMENTS = {
    "room": {
        "path": REPO_ROOT / ".claude" / "skills" / "room" / "SKILL.md",
        "name": "room",
        "required_refs": [
            "AGENTS.md",
            ".codex/skills/room-skill/SKILL.md",
            ".codex/skills/room-skill/WORKFLOW.md",
            ".codex/skills/room-skill/runtime/README.md",
            "docs/room-runtime-status.md",
            "docs/room-runtime-bridge.md",
            "docs/host-adapter-architecture.md",
            "docs/room-architecture.md",
            "docs/room-selection-policy.md",
            "docs/room-chat-contract.md",
            "docs/agent-registry.md",
            "docs/room-to-debate-handoff.md",
            "prompts/room-selection.md",
            "prompts/room-chat.md",
            "prompts/room-summary.md",
            "prompts/room-upgrade.md",
        ],
        "required_phrases": [
            "explicit",
            "not the canonical implementation source",
            "only state writer",
            "do not use `reports/`",
            "do not require provider URLs",
            "claude_code_not_logged_in",
        ],
    },
    "debate": {
        "path": REPO_ROOT / ".claude" / "skills" / "debate" / "SKILL.md",
        "name": "debate",
        "required_refs": [
            "AGENTS.md",
            ".codex/skills/debate-roundtable-skill/SKILL.md",
            ".codex/skills/debate-roundtable-skill/runtime/README.md",
            "docs/debate-runtime-bridge.md",
            "docs/host-adapter-architecture.md",
            "docs/debate-skill-architecture.md",
            "docs/agent-role-map.md",
            "docs/reviewer-protocol.md",
            "docs/red-flags.md",
            "docs/room-to-debate-handoff.md",
            "prompts/debate-roundtable.md",
            "prompts/debate-reviewer.md",
            "prompts/debate-followup.md",
        ],
        "required_phrases": [
            "explicit",
            "not the canonical implementation source",
            "do not use old Windows paths",
            "Do not fabricate reviewer approval",
            "claude_code_not_logged_in",
        ],
    },
}


def main() -> int:
    report = validate_project_skills()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def validate_project_skills() -> dict[str, Any]:
    skill_reports = []
    for skill_id, requirements in SKILL_REQUIREMENTS.items():
        skill_reports.append(validate_skill(skill_id=skill_id, requirements=requirements))

    pass_criteria = {
        "all_expected_skills_exist": all(item["exists"] for item in skill_reports),
        "frontmatter_valid": all(item["frontmatter_valid"] for item in skill_reports),
        "source_refs_present": all(not item["missing_refs"] for item in skill_reports),
        "guardrails_present": all(not item["missing_phrases"] for item in skill_reports),
        "canonical_sources_exist": all(not item["missing_source_files"] for item in skill_reports),
    }
    return {
        "ok": all(pass_criteria.values()),
        "action": "validate-claude-project-skills",
        "checked_against": str(Path(__file__).resolve()),
        "skills": skill_reports,
        "pass_criteria": pass_criteria,
    }


def validate_skill(*, skill_id: str, requirements: dict[str, Any]) -> dict[str, Any]:
    path = requirements["path"]
    exists = path.exists()
    text = path.read_text(encoding="utf-8") if exists else ""
    text_lower = text.lower()
    frontmatter = parse_frontmatter(text) if exists else {}
    missing_refs = [ref for ref in requirements["required_refs"] if ref not in text]
    missing_source_files = [ref for ref in requirements["required_refs"] if not (REPO_ROOT / ref).exists()]
    missing_phrases = [phrase for phrase in requirements["required_phrases"] if phrase.lower() not in text_lower]
    description = frontmatter.get("description", "")
    return {
        "skill": skill_id,
        "path": str(path.relative_to(REPO_ROOT)),
        "exists": exists,
        "frontmatter_valid": frontmatter.get("name") == requirements["name"] and bool(description.strip()),
        "frontmatter": frontmatter,
        "missing_refs": missing_refs,
        "missing_source_files": missing_source_files,
        "missing_phrases": missing_phrases,
    }


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    frontmatter: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter


if __name__ == "__main__":
    sys.exit(main())
