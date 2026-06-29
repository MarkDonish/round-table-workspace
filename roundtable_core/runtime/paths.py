from __future__ import annotations

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STATE_ROOT_BASE = Path(tempfile.gettempdir()) / "round-table-workspace"
ALLOWED_SYSTEM_SYMLINK_DIRS = {Path("/tmp"), Path("/var")}
SAFE_PATH_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class UnsafePathError(ValueError):
    pass


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def default_state_root(command: str, *, timestamp: str | None = None) -> Path:
    return DEFAULT_STATE_ROOT_BASE / command / (timestamp or utc_timestamp())


def resolve_state_root(explicit_state_root: str | None, command: str, *, timestamp: str | None = None) -> Path:
    if explicit_state_root:
        return Path(explicit_state_root).expanduser()
    return default_state_root(command, timestamp=timestamp)


def assert_no_symlink_components(path: str | Path, *, include_leaf: bool = True) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    scan_path = normalize_path_without_resolving_symlinks(candidate if include_leaf else candidate.parent)
    current = Path(scan_path.anchor) if scan_path.is_absolute() else Path(".")
    parts = scan_path.parts[1:] if scan_path.is_absolute() else scan_path.parts
    for part in parts:
        current = current / part
        if not current.exists():
            continue
        if current.is_symlink() and current not in ALLOWED_SYSTEM_SYMLINK_DIRS:
            raise UnsafePathError(f"refusing path through symlink component: {current}")
    return candidate


def normalize_path_without_resolving_symlinks(path: Path) -> Path:
    anchor = path.anchor
    normalized_parts: list[str] = []
    parts = path.parts[1:] if anchor else path.parts
    for part in parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if normalized_parts:
                normalized_parts.pop()
            continue
        normalized_parts.append(part)
    result = Path(anchor) if anchor else Path(".")
    for part in normalized_parts:
        result = result / part
    return result


def validate_path_segment(value: str, name: str = "path segment") -> str:
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise UnsafePathError(f"{name} must not contain path traversal: {value!r}")
    if not SAFE_PATH_SEGMENT_RE.fullmatch(value):
        raise UnsafePathError(f"{name} must be a safe single path segment: {value!r}")
    return value
