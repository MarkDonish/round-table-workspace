from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from roundtable_core.validation import validate_instance


JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class OutputParseResult:
    ok: bool
    data: dict[str, Any] | None
    error: str | None
    source: str
    candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "source": self.source,
            "candidates": self.candidates,
        }


def parse_structured_output(
    text: str,
    *,
    required_keys: list[str] | tuple[str, ...] = (),
    schema: dict[str, Any] | None = None,
    schema_path: str | Path | None = None,
) -> OutputParseResult:
    if schema is None and schema_path is not None:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))

    candidates = build_json_candidates(text)
    candidate_reports: list[dict[str, Any]] = []
    for source, candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            candidate_reports.append({"source": source, "parse_ok": False, "error": str(exc), "data": None})
            continue
        if not isinstance(parsed, dict):
            report = {"source": source, "parse_ok": False, "error": "parsed JSON is not an object", "data": parsed}
            candidate_reports.append(report)
            continue
        missing = [key for key in required_keys if key not in parsed]
        if missing:
            report = {
                "source": source,
                "parse_ok": True,
                "error": f"missing required keys: {', '.join(missing)}",
                "data": parsed,
            }
            candidate_reports.append(report)
            continue
        if schema is not None:
            errors = validate_instance(instance=parsed, schema=schema)
            if errors:
                report = {"source": source, "parse_ok": True, "error": "; ".join(errors), "data": parsed}
                candidate_reports.append(report)
                continue
        candidate_reports.append({"source": source, "parse_ok": True, "error": None, "data": parsed})
        return OutputParseResult(True, parsed, None, source, candidate_reports)
    return OutputParseResult(False, None, "no valid JSON object found", "none", candidate_reports)


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
