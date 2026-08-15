from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from roundtable_core.agents.factory import (
    DEFAULT_FACTORY_REGISTRY_PATH,
    register_factory_agent,
    resolve_repo_path,
)


def create_agent_bundle(
    *,
    agent_id: str,
    display_name: str,
    short_name: str,
    structural_role: str = "moderate",
    strength: str = "Domain analysis and balanced review",
    expression: str = "Analytical, structured, and objective",
    cognitive_lens: list[str] | None = None,
    useful_when: list[str] | None = None,
    avoid: list[str] | None = None,
    task_types: list[str] | None = None,
    sub_problem_tags: list[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    clean_id = agent_id.strip().lower().replace(" ", "-")
    skill_name = f"{clean_id}-skill" if not clean_id.endswith("-skill") else clean_id
    raw_agent_id = clean_id.replace("-skill", "")

    lens = cognitive_lens or ["Domain Reasoning", "Systematic Review"]
    useful = useful_when or ["Detailed domain review required", "Multi-perspective decision balance"]
    avoid_list = avoid or ["Unsupported claims", "Premature conclusions"]
    tasks = task_types or ["product", "engineering", "risk"]
    sub_tags = sub_problem_tags or ["strategy", "implementation", "verification"]

    # 1. Write Profile Markdown
    skill_dir = root / ".codex" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    profile_path = skill_dir / "roundtable-profile.md"

    profile_content = f"""# {display_name} ({short_name})

- Agent ID: `{raw_agent_id}`
- Role Category: `{structural_role}`
- Core Expression: {expression}
- Key Strength: {strength}

## Cognitive Lens
{chr(10).join(f"- {item}" for item in lens)}

## Useful When
{chr(10).join(f"- {item}" for item in useful)}

## Avoid / Counter-Signals
{chr(10).join(f"- {item}" for item in avoid_list)}
"""
    profile_path.write_text(profile_content, encoding="utf-8")

    # 2. Write Manifest JSON
    manifest_payload = {
        "$schema": "../../schemas/agent-manifest.schema.json",
        "agent_id": raw_agent_id,
        "display_name": display_name,
        "short_name": short_name,
        "version": "1.0.0",
        "structural_role": structural_role,
        "expression": expression,
        "strength": strength,
        "cognitive_lens": lens,
        "useful_when": useful,
        "avoid": avoid_list,
        "default_excluded": False,
        "task_types": tasks,
        "stage_fit": ["decision", "review", "refinement"],
        "sub_problem_tags": sub_tags,
        "profile_path": f".codex/skills/{skill_name}/roundtable-profile.md",
    }

    manifest_path = skill_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 3. Register in registry.json
    reg_result = register_factory_agent(
        registry_path=root / "agents" / "registry.json",
        manifest_path=manifest_path,
        replace=True,
        enable=True,
    )

    # 4. Sync to local user skills directories if present
    for host_dir in [Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"]:
        if host_dir.exists():
            target_skill_dir = host_dir / skill_name
            target_skill_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(profile_path, target_skill_dir / "roundtable-profile.md")
            shutil.copy2(manifest_path, target_skill_dir / "manifest.json")

    return {
        "ok": True,
        "action": "agent-wizard-create",
        "agent_id": raw_agent_id,
        "skill_dir": str(skill_dir),
        "manifest_path": str(manifest_path),
        "profile_path": str(profile_path),
        "registry_result": reg_result,
    }
