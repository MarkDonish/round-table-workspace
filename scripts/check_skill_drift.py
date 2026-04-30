#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Codex/Claude skill drift against skills_src.")
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
    generator = run_command([sys.executable, "scripts/generate_skills.py", "check"])
    shared = load_json(REPO_ROOT / "skills_src" / "shared_rules.json")
    skill_reports = [inspect_skill("room", shared), inspect_skill("debate", shared)]
    allowed = [
        "Codex skill contains canonical runtime details.",
        "Claude project skill is an adapter and may be shorter.",
    ]
    ok = generator["returncode"] == 0 and all(item["ok"] for item in skill_reports)
    return {
        "ok": ok,
        "action": "skill-drift-check",
        "generator_check": generator,
        "skills": skill_reports,
        "allowed_host_specific_differences": allowed,
    }


def inspect_skill(skill_id: str, shared: dict[str, Any]) -> dict[str, Any]:
    source = load_json(REPO_ROOT / "skills_src" / f"{skill_id}.skill.json")
    targets = [source["canonical_codex_path"], *source["adapter_paths"]]
    target_reports = []
    for rel_path in targets:
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        text_lower = text.lower()
        missing_rules = [phrase for phrase in shared["required_phrases"] if phrase.lower() not in text_lower]
        missing_refs = [ref for ref in source["canonical_refs"] if ref not in text]
        missing_entry_commands = [command for command in source["entry_commands"] if command not in text]
        forbidden = [phrase for phrase in source.get("forbidden_unverified_claims", []) if phrase.lower() in text_lower]
        frontmatter = parse_frontmatter(text)
        generated_section = extract_generated_section(text)
        generated_section_hash = stable_hash(generated_section) if generated_section else None
        stale = not generated_section or source["skill_id"] not in generated_section or source["schema_version"] not in generated_section
        adapter_protocol_fork = ".claude/" in rel_path and any(ref.startswith("runtime/") for ref in source.get("adapter_refs", []))
        target_reports.append(
            {
                "target": rel_path,
                "exists": path.exists(),
                "frontmatter": frontmatter,
                "frontmatter_ok": bool(frontmatter.get("name") and frontmatter.get("description")),
                "shared_rule_present": not missing_rules,
                "missing_rules": missing_rules,
                "missing_refs": missing_refs,
                "missing_entry_commands": missing_entry_commands,
                "generated_section_hash": generated_section_hash,
                "generated_section_stale": stale,
                "forbidden": forbidden,
                "adapter_protocol_fork": adapter_protocol_fork,
                "allowed_host_specific": source.get("host_specific_allowed_differences", []),
                "changed_wording_requiring_review": [],
                "host_specific": ".claude/" in rel_path,
                "ok": (
                    path.exists()
                    and bool(frontmatter.get("name") and frontmatter.get("description"))
                    and not missing_rules
                    and not missing_refs
                    and not missing_entry_commands
                    and not stale
                    and not forbidden
                    and not adapter_protocol_fork
                ),
            }
        )
    return {
        "skill": skill_id,
        "targets": target_reports,
        "ok": all(item["ok"] for item in target_reports),
    }


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    current_key: str | None = None
    for line in text[3:end].splitlines():
        if line.startswith(" ") and current_key:
            result[current_key] = (result[current_key] + " " + line.strip()).strip()
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            result[current_key] = value.strip().strip("|").strip()
    return result


def extract_generated_section(text: str) -> str:
    start = "<!-- rtw:generated-skill-summary:start -->"
    end = "<!-- rtw:generated-skill-summary:end -->"
    if start not in text or end not in text:
        return ""
    return text[text.index(start) : text.index(end) + len(end)]


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Skill Drift Check", "", f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`", ""]
    for skill in report["skills"]:
        lines.append(f"## {skill['skill']}")
        lines.append("")
        for target in skill["targets"]:
            lines.append(
                f"- `{target['target']}`: ok=`{target['ok']}`, missing_rules=`{target['missing_rules']}`, "
                f"missing_refs=`{target['missing_refs']}`, missing_entry_commands=`{target['missing_entry_commands']}`, "
                f"stale=`{target['generated_section_stale']}`, forbidden=`{target['forbidden']}`"
            )
        lines.append("")
    lines.append("## Allowed Host-Specific Differences")
    lines.append("")
    for item in report["allowed_host_specific_differences"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
