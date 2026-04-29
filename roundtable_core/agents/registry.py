from __future__ import annotations

from dataclasses import dataclass


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


AGENT_LENSES: dict[str, AgentLens] = {
    "steve-jobs": AgentLens(
        agent_id="steve-jobs",
        display_name="Jobs lens",
        short_name="Jobs",
        cognitive_lens=("product focus", "taste", "user experience compression"),
        useful_when=("product wedge", "positioning", "experience clarity"),
        avoid=("voice imitation", "invented personal opinions", "biographical claims"),
        style_rule="Use the product judgment lens; do not imitate Steve Jobs' voice.",
    ),
    "taleb": AgentLens(
        agent_id="taleb",
        display_name="Taleb lens",
        short_name="Taleb",
        cognitive_lens=("tail risk", "fragility", "skin in the game"),
        useful_when=("downside risk", "fragile assumptions", "asymmetric payoff"),
        avoid=("voice imitation", "insult style", "unverified claims about Taleb"),
        style_rule="Use the risk lens; do not imitate Nassim Taleb's voice.",
    ),
    "munger": AgentLens(
        agent_id="munger",
        display_name="Munger lens",
        short_name="Munger",
        cognitive_lens=("incentives", "inversion", "downside control"),
        useful_when=("kill rules", "decision filters", "risk review"),
        avoid=("voice imitation", "quotes presented as fact without source"),
        style_rule="Use the mental-model lens; do not imitate Charlie Munger's voice.",
    ),
    "karpathy": AgentLens(
        agent_id="karpathy",
        display_name="Karpathy lens",
        short_name="Karpathy",
        cognitive_lens=("technical feasibility", "learning loops", "system simplicity"),
        useful_when=("AI product loop", "implementation thin slice", "education workflow"),
        avoid=("voice imitation", "claiming private views"),
        style_rule="Use the technical-learning lens; do not imitate Andrej Karpathy's voice.",
    ),
}

ALIASES = {
    "jobs": "steve-jobs",
    "steve jobs": "steve-jobs",
    "taleb": "taleb",
    "munger": "munger",
    "karpathy": "karpathy",
}


def resolve_agent_lens(name: str) -> AgentLens | None:
    key = name.strip().lower()
    agent_id = ALIASES.get(key, key)
    return AGENT_LENSES.get(agent_id)
