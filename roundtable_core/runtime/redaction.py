from __future__ import annotations

import re
from typing import Any


SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(?:"
    r"authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret|"
    r".*[_-](?:api[_-]?key|key|token|password|secret)"
    r")$"
)
SENSITIVE_FLAG_RE = re.compile(
    r"(?i)^--(?:"
    r"authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret"
    r")$"
)

SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*)basic\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(
        r"(?i)(--(?:authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret)(?:=|\s+))[^\s\"']{8,}"
    ),
    re.compile(
        r"(?i)((?:\"(?:authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret)\"|"
        r"(?:authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret))\s*:\s*\")[^\"]{8,}(\")"
    ),
    re.compile(r"sk-proj-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{12,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{12,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)(authorization|auth[_-]?bearer|github[_-]?token|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|token[_-]?value|api[_-]?key|token|password|secret)(\s*[:=]\s*)[^\s\"']{8,}"
    ),
]


def redact_sensitive_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, list):
        redacted_items: list[Any] = []
        redact_next = False
        for item in value:
            if redact_next:
                redacted_items.append("[REDACTED]" if isinstance(item, str) else redact_sensitive_value(item))
                redact_next = False
                continue
            redacted_items.append(redact_sensitive_value(item))
            if isinstance(item, str) and SENSITIVE_FLAG_RE.fullmatch(item.strip()):
                redact_next = True
        return redacted_items
    if isinstance(value, dict):
        redacted_object = {}
        for key, item in value.items():
            if isinstance(key, str) and SENSITIVE_KEY_RE.fullmatch(key):
                redacted_object[key] = "[REDACTED]" if isinstance(item, str) else redact_sensitive_value(item)
                continue
            redacted_object[key] = redact_sensitive_value(item)
        return redacted_object
    return value


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)((?:"):
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]{match.group(2)}", redacted)
        elif pattern.pattern.startswith("(?i)(authorization"):
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
        elif pattern.pattern.startswith("(?i)(--"):
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
        elif pattern.pattern.startswith("(?i)(api"):
            redacted = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
