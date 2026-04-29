from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STATE_ROOT_BASE = Path("/tmp") / "round-table-workspace"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def default_state_root(command: str, *, timestamp: str | None = None) -> Path:
    return DEFAULT_STATE_ROOT_BASE / command / (timestamp or utc_timestamp())


def resolve_state_root(explicit_state_root: str | None, command: str, *, timestamp: str | None = None) -> Path:
    if explicit_state_root:
        return Path(explicit_state_root).expanduser()
    return default_state_root(command, timestamp=timestamp)
