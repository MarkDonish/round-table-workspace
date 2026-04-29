from __future__ import annotations

from typing import Any

from roundtable_core.runtime.paths import utc_timestamp


def build_evidence_metadata(
    *,
    workflow: str,
    action: str,
    claim_boundary: dict[str, Any],
    generated_at: str | None = None,
    schema_version: str = "0.1.0",
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "workflow": workflow,
        "action": action,
        "generated_at": generated_at or utc_timestamp(),
        "claim_boundary": claim_boundary,
    }
