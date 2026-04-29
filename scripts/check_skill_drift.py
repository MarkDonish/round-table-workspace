#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    shared = load_json(REPO_ROOT / "skills_src" / "shared_rules.yaml")
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
    source = load_json(REPO_ROOT / "skills_src" / f"{skill_id}.skill.yaml")
    targets = [source["canonical_codex_path"], *source["adapter_paths"]]
    target_reports = []
    for rel_path in targets:
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        text_lower = text.lower()
        missing_rules = [phrase for phrase in shared["required_phrases"] if phrase.lower() not in text_lower]
        missing_refs = [ref for ref in source["canonical_refs"] if ref not in text]
        target_reports.append(
            {
                "target": rel_path,
                "exists": path.exists(),
                "shared_rule_present": not missing_rules,
                "missing_rules": missing_rules,
                "missing_refs": missing_refs,
                "changed_wording_requiring_review": [],
                "host_specific": ".claude/" in rel_path,
                "ok": path.exists() and not missing_rules and not missing_refs,
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


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Skill Drift Check", "", f"- Result: `{'PASS' if report['ok'] else 'FAIL'}`", ""]
    for skill in report["skills"]:
        lines.append(f"## {skill['skill']}")
        lines.append("")
        for target in skill["targets"]:
            lines.append(
                f"- `{target['target']}`: ok=`{target['ok']}`, missing_rules=`{target['missing_rules']}`, missing_refs=`{target['missing_refs']}`"
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
