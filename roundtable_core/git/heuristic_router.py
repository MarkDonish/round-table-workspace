from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from .diff_inspector import GitDiffResult


DEFAULT_PANEL = ["engineering", "product", "risk", "user-advocate"]

CATEGORY_TO_ROLE_MAP: dict[str, str] = {
    "database_migration": "database-auditor",
    "security_auth": "security-auditor",
    "api_endpoint": "api-contract-reviewer",
    "config_ci": "security-auditor",
}


@dataclass(frozen=True)
class RecommendedPanel:
    roles: list[str]
    rationale: dict[str, str]
    primary_focus: str
    categories: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "roles": self.roles,
            "rationale": self.rationale,
            "primary_focus": self.primary_focus,
            "categories": self.categories,
        }


class HeuristicRoleRouter:
    def __init__(self, max_panel_size: int = 5) -> None:
        self.max_panel_size = max_panel_size

    def route(self, diff_result: GitDiffResult) -> RecommendedPanel:
        if not diff_result.ok or not diff_result.changed_files:
            return RecommendedPanel(
                roles=list(DEFAULT_PANEL),
                rationale={
                    "engineering": "Standard technical verification.",
                    "product": "Standard value proposition check.",
                    "risk": "Standard claim boundary and downside review.",
                    "user-advocate": "Standard user impact and documentation review.",
                },
                primary_focus="general_engineering_review",
                categories=list(diff_result.categories),
            )

        roles: list[str] = ["engineering"]
        rationale: dict[str, str] = {
            "engineering": f"Core code review for {len(diff_result.changed_files)} changed files (+{diff_result.insertions}, -{diff_result.deletions})."
        }

        specialist_added = False
        for cat in diff_result.categories:
            if cat in CATEGORY_TO_ROLE_MAP:
                specialist = CATEGORY_TO_ROLE_MAP[cat]
                if specialist not in roles and len(roles) < self.max_panel_size:
                    roles.append(specialist)
                    if cat == "database_migration":
                        rationale[specialist] = "Detected database migrations or schema files; audit locks, rollbacks, and indexes."
                    elif cat == "security_auth":
                        rationale[specialist] = "Detected auth/credential/env files; audit secret leaks, injection, and permissions."
                    elif cat == "api_endpoint":
                        rationale[specialist] = "Detected API routes/contracts; audit breaking changes and error payloads."
                    elif cat == "config_ci":
                        rationale[specialist] = "Detected CI/build/dependency config; audit supply-chain and pipeline safety."
                    specialist_added = True

        if "risk" not in roles and len(roles) < self.max_panel_size:
            roles.append("risk")
            rationale["risk"] = "Downside protection, test coverage, and claim boundary verification."

        if "product" not in roles and len(roles) < self.max_panel_size:
            roles.append("product")
            rationale["product"] = "Ensure modified capabilities clearly deliver the intended user value."

        if "frontend_ui" in diff_result.categories or len(roles) < self.max_panel_size:
            if "user-advocate" not in roles and len(roles) < self.max_panel_size:
                roles.append("user-advocate")
                rationale["user-advocate"] = "Validate UX clarity, documentation, and error feedback for end users."

        primary_focus = "specialist_verification" if specialist_added else "standard_code_review"

        return RecommendedPanel(
            roles=roles,
            rationale=rationale,
            primary_focus=primary_focus,
            categories=list(diff_result.categories),
        )


def recommend_panel_for_diff(diff_result: GitDiffResult, max_panel_size: int = 5) -> RecommendedPanel:
    router = HeuristicRoleRouter(max_panel_size=max_panel_size)
    return router.route(diff_result)
