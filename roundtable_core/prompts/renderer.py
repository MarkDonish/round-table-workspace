from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


class PromptRenderError(ValueError):
    pass


@dataclass(frozen=True)
class RenderedPrompt:
    prompt_path: str
    variables: dict[str, Any]
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_path": self.prompt_path,
            "variables": self.variables,
            "text": self.text,
        }


def render_prompt(
    prompt_path: str | Path,
    variables: dict[str, Any],
    *,
    required_variables: list[str] | tuple[str, ...] = (),
    append_context: bool = True,
) -> RenderedPrompt:
    path = Path(prompt_path)
    template = path.read_text(encoding="utf-8")
    missing = [name for name in required_variables if name not in variables]
    if missing:
        raise PromptRenderError(f"Missing prompt variables: {', '.join(missing)}")

    placeholder_names = sorted(set(PLACEHOLDER_RE.findall(template)))
    placeholder_missing = [name for name in placeholder_names if name not in variables]
    if placeholder_missing:
        raise PromptRenderError(f"Missing template placeholders: {', '.join(placeholder_missing)}")

    def replace(match: re.Match[str]) -> str:
        value = variables[match.group(1)]
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    rendered = PLACEHOLDER_RE.sub(replace, template)
    if append_context and variables:
        rendered = rendered.rstrip() + "\n\n---\n\n## Runtime Input\n\n```json\n"
        rendered += json.dumps(variables, ensure_ascii=False, indent=2)
        rendered += "\n```\n"
    return RenderedPrompt(prompt_path=str(path), variables=dict(variables), text=rendered)
