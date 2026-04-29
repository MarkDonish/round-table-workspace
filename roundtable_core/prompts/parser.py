from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class OutputParseResult:
    ok: bool
    data: dict[str, Any] | None
    error: str | None
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "source": self.source,
        }


def parse_structured_output(
    text: str,
    *,
    required_keys: list[str] | tuple[str, ...] = (),
) -> OutputParseResult:
    candidates = build_json_candidates(text)
    for source, candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            return OutputParseResult(False, None, "parsed JSON is not an object", source)
        missing = [key for key in required_keys if key not in parsed]
        if missing:
            return OutputParseResult(False, parsed, f"missing required keys: {', '.join(missing)}", source)
        return OutputParseResult(True, parsed, None, source)
    return OutputParseResult(False, None, "no parseable JSON object found", "none")


def build_json_candidates(text: str) -> list[tuple[str, str]]:
    stripped = text.strip()
    candidates: list[tuple[str, str]] = []
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(("raw", stripped))
    for match in JSON_FENCE_RE.finditer(text):
        candidates.append(("fenced_json", match.group(1).strip()))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(("embedded_json", text[start : end + 1]))
    return candidates
