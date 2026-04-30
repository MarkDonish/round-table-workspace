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


@dataclass(frozen=True)
class PromptSpec:
    prompt_path: str | Path
    required_variables: tuple[str, ...] = ()
    allowed_variables: tuple[str, ...] = ()
    expected_output_schema: str | None = None
    append_context_policy: str = "never"

    def allows_append_context(self) -> bool:
        return self.append_context_policy in {"explicit", "always"}


def render_prompt(
    prompt_path: str | Path,
    variables: dict[str, Any],
    *,
    required_variables: list[str] | tuple[str, ...] = (),
    allowed_variables: list[str] | tuple[str, ...] = (),
    allow_extra: bool = False,
    append_context: bool = False,
    prompt_spec: PromptSpec | None = None,
) -> RenderedPrompt:
    if prompt_spec is not None:
        prompt_path = prompt_spec.prompt_path
        required_variables = prompt_spec.required_variables
        allowed_variables = prompt_spec.allowed_variables
        append_context = prompt_spec.append_context_policy == "always" or (
            append_context and prompt_spec.allows_append_context()
        )

    path = Path(prompt_path)
    template = path.read_text(encoding="utf-8")
    missing = [name for name in required_variables if name not in variables]
    if missing:
        raise PromptRenderError(f"Missing prompt variables: {', '.join(missing)}")

    if allowed_variables and not allow_extra:
        extras = sorted(set(variables) - set(allowed_variables))
        if extras:
            raise PromptRenderError(f"Unexpected prompt variables: {', '.join(extras)}")

    if allowed_variables:
        render_variables = {name: variables[name] for name in allowed_variables if name in variables}
    else:
        render_variables = dict(variables)

    placeholder_names = sorted(set(PLACEHOLDER_RE.findall(template)))
    placeholder_missing = [name for name in placeholder_names if name not in render_variables]
    if placeholder_missing:
        raise PromptRenderError(f"Missing template placeholders: {', '.join(placeholder_missing)}")

    def replace(match: re.Match[str]) -> str:
        value = render_variables[match.group(1)]
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    rendered = PLACEHOLDER_RE.sub(replace, template)
    if append_context and render_variables:
        rendered = rendered.rstrip() + "\n\n---\n\n## Runtime Input\n\n```json\n"
        rendered += json.dumps(render_variables, ensure_ascii=False, indent=2)
        rendered += "\n```\n"
    return RenderedPrompt(prompt_path=str(path), variables=render_variables, text=rendered)
