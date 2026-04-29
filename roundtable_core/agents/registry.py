from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "agents" / "registry.json"


@dataclass(frozen=True)
class AgentLens:
    agent_id: str
    display_name: str
    short_name: str
    cognitive_lens: tuple[str, ...]
    useful_when: tuple[str, ...]
    avoid: tuple[str, ...]
    style_rule: str

    def to_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "short_name": self.short_name,
            "cognitive_lens": list(self.cognitive_lens),
            "useful_when": list(self.useful_when),
            "avoid": list(self.avoid),
            "style_rule": self.style_rule,
        }


def load_agent_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    registry_path = path or DEFAULT_REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    agents = payload.get("agents")
    if not isinstance(agents, list):
        raise ValueError(f"Agent registry must contain an agents array: {registry_path}")

    registry: dict[str, dict[str, Any]] = {}
    for item in agents:
        if not isinstance(item, dict):
            raise ValueError("Agent registry entries must be objects.")
        agent_id = item.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("Agent registry entry missing non-empty agent_id.")
        if agent_id in registry:
            raise ValueError(f"Duplicate agent_id in registry: {agent_id}")
        registry[agent_id] = item
    if not registry:
        raise ValueError(f"Agent registry is empty: {registry_path}")
    return registry


def _lens_from_entry(entry: dict[str, Any]) -> AgentLens:
    return AgentLens(
        agent_id=str(entry["agent_id"]),
        display_name=str(entry["display_name"]),
        short_name=str(entry["short_name"]),
        cognitive_lens=tuple(str(item) for item in entry.get("cognitive_lens", [])),
        useful_when=tuple(str(item) for item in entry.get("useful_when", [])),
        avoid=tuple(str(item) for item in entry.get("avoid", [])),
        style_rule=str(entry["style_rule"]),
    )


def load_agent_lenses(path: Path | None = None) -> dict[str, AgentLens]:
    return {agent_id: _lens_from_entry(entry) for agent_id, entry in load_agent_registry(path).items()}


AGENT_LENSES: dict[str, AgentLens] = load_agent_lenses()

ALIASES = {
    "jobs": "steve-jobs",
    "steve jobs": "steve-jobs",
    "musk": "elon-musk",
    "elon musk": "elon-musk",
    "pg": "paul-graham",
    "paul graham": "paul-graham",
    "zhang yiming": "zhang-yiming",
    "zhang xuefeng": "zhangxuefeng",
    "mrbeast": "mrbeast",
    "mr beast": "mrbeast",
    "ilya": "ilya-sutskever",
    "ilya sutskever": "ilya-sutskever",
    "sun": "justin-sun",
    "justin sun": "justin-sun",
    "taleb": "taleb",
    "munger": "munger",
    "karpathy": "karpathy",
    "feynman": "feynman",
    "naval": "naval",
    "trump": "trump",
}


def resolve_agent_lens(name: str) -> AgentLens | None:
    key = name.strip().lower()
    agent_id = ALIASES.get(key, key)
    return AGENT_LENSES.get(agent_id)
