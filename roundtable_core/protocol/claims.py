from __future__ import annotations

from enum import Enum
from typing import Any


class ClaimStatus(str, Enum):
    NOT_CLAIMED = "not_claimed"
    FIXTURE_ONLY = "fixture_only"
    PENDING_LIVE_VALIDATION = "pending_live_validation"
    LIVE_PASSED = "live_passed"


def local_first_claim_boundary(
    *,
    host_live: ClaimStatus = ClaimStatus.NOT_CLAIMED,
    provider_live: ClaimStatus = ClaimStatus.NOT_CLAIMED,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "local_first": True,
        "host_live": host_live.value,
        "provider_live": provider_live.value,
        "notes": notes or [
            "Local-first scope only.",
            "Fixture validation is not host-live or provider-live support.",
        ],
    }
