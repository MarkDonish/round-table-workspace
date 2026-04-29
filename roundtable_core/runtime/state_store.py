from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .evidence import build_evidence_metadata
from .paths import utc_timestamp


STATE_SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class RunRecord:
    state_root: Path
    run_dir: Path
    run_id: str
    workflow: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "state_root": str(self.state_root),
            "run_dir": str(self.run_dir),
            "run_id": self.run_id,
            "workflow": self.workflow,
            "created_at": self.created_at,
        }


def create_run_dir(
    state_root: str | Path,
    workflow: str,
    *,
    run_id: str | None = None,
    created_at: str | None = None,
) -> RunRecord:
    created_at = created_at or utc_timestamp()
    run_id = run_id or f"{workflow}-{created_at}-{uuid4().hex[:8]}"
    root = Path(state_root).expanduser().resolve()
    run_dir = root / "runs" / run_id
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    record = RunRecord(
        state_root=root,
        run_dir=run_dir,
        run_id=run_id,
        workflow=workflow,
        created_at=created_at,
    )
    write_json(run_dir / "run.json", record.to_dict())
    return record


def write_input(run_dir: str | Path, data: dict[str, Any]) -> Path:
    return write_json(Path(run_dir) / "input.json", data)


def write_output(run_dir: str | Path, data: dict[str, Any]) -> Path:
    return write_json(Path(run_dir) / "output.json", data)


def write_evidence(run_dir: str | Path, data: dict[str, Any]) -> Path:
    return write_json(Path(run_dir) / "evidence.json", data)


def write_summary(run_dir: str | Path, markdown: str) -> Path:
    path = Path(run_dir) / "summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    return path


def build_run_evidence(
    *,
    run: RunRecord,
    action: str,
    input_data: dict[str, Any],
    claim_boundary: dict[str, Any],
    host: str | None = None,
    provider_lane: str | None = None,
) -> dict[str, Any]:
    metadata = build_evidence_metadata(
        workflow=run.workflow,
        action=action,
        claim_boundary=claim_boundary,
        generated_at=run.created_at,
    )
    metadata.update(
        {
            "schema_version": STATE_SCHEMA_VERSION,
            "run_id": run.run_id,
            "host": host or "local",
            "provider_lane": provider_lane or "not_required",
            "input_hash": stable_hash(input_data),
        }
    )
    return metadata


def stable_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
