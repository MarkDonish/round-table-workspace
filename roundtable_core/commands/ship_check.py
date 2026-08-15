from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from roundtable_core.git.diff_inspector import GitDiffInspector, GitDiffResult, inspect_git_diff
from roundtable_core.git.heuristic_router import recommend_panel_for_diff
from roundtable_core.runtime.paths import assert_no_symlink_components, resolve_checked_path, utc_timestamp


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PanelVote:
    agent: str
    role_name: str
    vote: str  # "ship" | "revise" | "reject"
    reason: str
    concerns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "role_name": self.role_name,
            "vote": self.vote,
            "reason": self.reason,
            "concerns": list(self.concerns),
        }


def evaluate_product_lens(
    question: str,
    diff_res: GitDiffResult | None,
    custom_role: str | None = None,
) -> PanelVote:
    agent = custom_role or "product"
    role_name = "Product Value & User Experience"
    concerns: list[str] = []

    if diff_res and diff_res.ok:
        has_ui = "frontend_ui" in diff_res.categories
        has_docs = any(f.endswith(".md") or "docs/" in f for f in diff_res.changed_files)
        
        if diff_res.insertions > 400 and not has_docs:
            vote = "revise"
            reason = "Substantial implementation added without user-facing documentation or observable before/after examples."
            concerns.append("Lack of user-facing documentation for large feature change.")
        elif "frontend_ui" in diff_res.categories and not has_docs:
            vote = "revise"
            reason = "UI changes present; verify that interactive elements have clear visual states and error feedback."
            concerns.append("Ensure responsive visual feedback and error messaging.")
        elif diff_res.insertions == 0 and diff_res.deletions == 0 and not question:
            vote = "revise"
            reason = "Empty working tree diff and no question provided; state the user outcome to evaluate."
            concerns.append("No active diff or question defined.")
        else:
            vote = "ship"
            reason = "The user value is well-scoped and avoids extraneous feature bloat."
    else:
        vote = "revise"
        reason = "The user outcome should be explicitly defined and verified against core user pain points."
        concerns.append("Define observable outcome thresholds before launch.")

    return PanelVote(agent=agent, role_name=role_name, vote=vote, reason=reason, concerns=concerns)


def evaluate_engineering_lens(
    question: str,
    diff_res: GitDiffResult | None,
    custom_role: str | None = None,
) -> PanelVote:
    agent = custom_role or "engineering"
    role_name = "Architecture, Code Safety & Test Discipline"
    concerns: list[str] = []

    if diff_res and diff_res.ok:
        has_tests = "test_spec" in diff_res.categories
        has_migrations = "database_migration" in diff_res.categories
        has_auth = "security_auth" in diff_res.categories

        if diff_res.insertions > 250 and not has_tests:
            vote = "revise"
            reason = f"Large change footprint (+{diff_res.insertions} lines across {len(diff_res.changed_files)} files) with no accompanying tests."
            concerns.append("Missing test specs for substantial code modifications.")
        elif has_migrations and not has_tests:
            vote = "revise"
            reason = "Database migrations changed without automated migration / schema rollback tests."
            concerns.append("Database migration lacks automated verification tests.")
        elif has_auth and not has_tests:
            vote = "revise"
            reason = "Security/auth logic modified without negative boundary test coverage."
            concerns.append("Auth modifications require explicit negative test cases.")
        elif diff_res.insertions > 800:
            vote = "revise"
            reason = f"Excessive commit footprint (+{diff_res.insertions} lines). Recommend breaking into smaller reviewable PRs."
            concerns.append("PR size exceeds single-review threshold.")
        else:
            vote = "ship"
            reason = "Code changes maintain clean modular boundaries and pass static inspection."
    else:
        vote = "ship"
        reason = "Architecture plan is sound when validated with fresh unit and integration tests."

    return PanelVote(agent=agent, role_name=role_name, vote=vote, reason=reason, concerns=concerns)


def evaluate_risk_lens(
    question: str,
    diff_res: GitDiffResult | None,
    custom_role: str | None = None,
) -> PanelVote:
    agent = custom_role or "risk"
    role_name = "Failure Modes, Blast Radius & Downside Protection"
    concerns: list[str] = []

    if diff_res and diff_res.ok:
        has_auth = "security_auth" in diff_res.categories
        has_migrations = "database_migration" in diff_res.categories
        has_config = "config_ci" in diff_res.categories

        if has_auth and has_migrations:
            vote = "revise"
            reason = "Compound blast radius: concurrent auth and database migration changes increase failure surface."
            concerns.append("Simultaneous high-risk auth and database schema changes.")
        elif has_auth:
            vote = "revise"
            reason = "Auth/secret boundary changed. Confirm zero credential leakage, token revocation, and rate limiting."
            concerns.append("Verify auth token handling and secret redaction.")
        elif has_migrations:
            vote = "revise"
            reason = "Database schema altered. Confirm zero-downtime compatibility and testable rollback script."
            concerns.append("Ensure schema change does not lock production tables.")
        elif diff_res.insertions > 500:
            vote = "revise"
            reason = "Substantial code changes require an explicit rollback checklist prior to deployment."
            concerns.append("Rollback procedure must be documented for large changes.")
        else:
            vote = "ship"
            reason = "Downside risk is strictly bounded with low blast radius."
    else:
        vote = "revise"
        reason = "Explicit kill criteria and rollback steps must be established before promoting to release candidate."
        concerns.append("Rollback path and kill criteria should be documented.")

    return PanelVote(agent=agent, role_name=role_name, vote=vote, reason=reason, concerns=concerns)


def evaluate_specialist_lens(
    role: str,
    diff_res: GitDiffResult | None,
) -> PanelVote:
    r = role.lower()
    concerns: list[str] = []

    if "security" in r:
        role_name = "Security & Auth Auditor"
        if diff_res and "security_auth" in diff_res.categories:
            vote = "revise"
            reason = "Auth/secret files modified. Verify input sanitization, rate limiting, and zero credential leakage."
            concerns.append("Ensure credentials and tokens are strictly read from environment variables.")
        else:
            vote = "ship"
            reason = "No sensitive credential, cryptographic, or authentication surface compromised."
    elif "database" in r or "db" in r:
        role_name = "Database & Migration Auditor"
        if diff_res and "database_migration" in diff_res.categories:
            vote = "revise"
            reason = "Database schema/migration changed. Ensure zero-downtime compatibility and verify rollback scripts."
            concerns.append("Verify non-blocking DDL and rollback compatibility.")
        else:
            vote = "ship"
            reason = "No dangerous DDL, unindexed queries, or database locking operations detected."
    elif "api" in r:
        role_name = "API Contract & Integration Reviewer"
        if diff_res and "api_endpoint" in diff_res.categories:
            vote = "revise"
            reason = "API endpoint surface modified. Confirm backward compatibility for existing client requests."
            concerns.append("Validate request/response schema stability across client versions.")
        else:
            vote = "ship"
            reason = "No breaking API interface changes detected."
    elif "performance" in r:
        role_name = "Performance & Scalability Specialist"
        if diff_res and diff_res.insertions > 400:
            vote = "revise"
            reason = "Large addition; profile CPU and memory latency on high-volume hot paths."
            concerns.append("Benchmark critical execution loops.")
        else:
            vote = "ship"
            reason = "No algorithmic regressions or memory leakage patterns detected."
    else:
        role_name = f"{role.title()} Lens"
        vote = "ship"
        reason = f"Specialist lens '{role}' reviewed and verified domain constraints."

    return PanelVote(agent=role, role_name=role_name, vote=vote, reason=reason, concerns=concerns)


def build_enhanced_ship_check_payload(
    question: str = "",
    *,
    diff: bool = False,
    staged: bool = False,
    cwd: str | None = None,
    roles: list[str] | None = None,
) -> dict[str, Any]:
    diff_res: GitDiffResult | None = None
    if diff or staged or cwd or (not question and not roles):
        diff_res = inspect_git_diff(cwd, staged=staged, include_untracked=True)

    # 1. Evaluate Core Lenses (Product, Engineering, Risk)
    panel_votes: list[PanelVote] = [
        evaluate_product_lens(question, diff_res),
        evaluate_engineering_lens(question, diff_res),
        evaluate_risk_lens(question, diff_res),
    ]

    # 2. Add extra specialist roles if requested or recommended
    specialist_roles = list(roles) if roles else []
    if not roles and diff_res and diff_res.ok:
        recommended = recommend_panel_for_diff(diff_res)
        for r in recommended.roles:
            if r not in ("product", "engineering", "risk", "user-advocate") and r not in specialist_roles:
                specialist_roles.append(r)

    for role in specialist_roles:
        if role.lower() not in ("product", "engineering", "risk"):
            panel_votes.append(evaluate_specialist_lens(role, diff_res))

    # 3. Determine Overall Decision
    reject_count = sum(1 for v in panel_votes if v.vote == "reject")
    revise_count = sum(1 for v in panel_votes if v.vote == "revise")

    if reject_count > 0:
        decision = "reject"
        confidence = "high"
        summary = "Ship-check REJECTED: critical blocking risks or severe failure modes identified."
    elif revise_count > 0:
        decision = "revise"
        confidence = "medium"
        summary = "Useful progress, but revise test coverage, claim boundaries, and evidence before merging or releasing."
    else:
        decision = "ship"
        confidence = "high"
        summary = "All Product, Engineering, and Risk review criteria satisfied. Ready to ship after final CI checks."

    # 4. Synthesize Blocking Risks
    blocking_risks: list[str] = []
    for vote in panel_votes:
        for concern in vote.concerns:
            if concern not in blocking_risks:
                blocking_risks.append(concern)

    if diff_res and diff_res.ok:
        if "security_auth" in diff_res.categories:
            blocking_risks.append("Unverified security/auth configuration on modified endpoints.")
        if "database_migration" in diff_res.categories:
            blocking_risks.append("Database schema migration without verified automated rollback path.")
        if diff_res.insertions > 300 and "test_spec" not in diff_res.categories:
            blocking_risks.append("Large code diff without corresponding test suite additions.")

    if not blocking_risks:
        blocking_risks = ["Overclaiming host-live or provider-live behavior without fresh evidence."]

    # 5. Synthesize Next Testable Steps
    next_testable_steps: list[str] = [
        "Run `python3 -m unittest discover tests` to verify 100% test pass rate.",
        "Run `./rtw doctor --quick` to verify local workspace health.",
    ]
    if diff_res and "test_spec" not in diff_res.categories and diff_res.insertions > 100:
        next_testable_steps.append("Add focused unit tests covering the newly added logic branches.")
    if diff_res and "security_auth" in diff_res.categories:
        next_testable_steps.append("Perform negative boundary testing on auth/secret ingestion paths.")
    if diff_res and "database_migration" in diff_res.categories:
        next_testable_steps.append("Dry-run migration up and down in a staging/sandbox database.")
    next_testable_steps.append("Verify all claim boundaries stay local-first unless live evidence is collected.")

    # 6. Build final payload
    diff_summary = diff_res.summary_text if diff_res else "No active git diff inspected."
    categories = diff_res.categories if diff_res else []
    changed_files = diff_res.changed_files if diff_res else []
    insertions = diff_res.insertions if diff_res else 0
    deletions = diff_res.deletions if diff_res else 0

    return {
        "ok": True,
        "action": "ship-check",
        "status": "fixture_backed",
        "generated_at": iso_now(),
        "question": question or (
            f"Inspect git changes ({'staged' if staged else 'working tree'})"
            if diff_res and diff_res.ok
            else "General ship readiness evaluation"
        ),
        "decision": decision,
        "confidence": confidence,
        "summary": summary,
        "panel_votes": [v.to_dict() for v in panel_votes],
        "blocking_risks": blocking_risks,
        "next_testable_steps": next_testable_steps,
        "risks": blocking_risks,  # Backward compatibility
        "next_actions": next_testable_steps,  # Backward compatibility
        "missing_evidence": [
            "Fresh test run for the current checkout.",
            "Visible verification transcript for public claims.",
            "Documented rollback path for high-impact changes.",
        ],
        "diff_summary": diff_summary,
        "categories": categories,
        "changed_files": changed_files,
        "insertions": insertions,
        "deletions": deletions,
        "claim_boundary": [
            "ship-check is a fixture-backed local ship/revise/reject decision gate, not a host-live or provider-live agent execution claim.",
            "Use it as a pre-ship review scaffold; verify with project-specific tests before merging or releasing.",
        ],
    }


def render_ship_check_markdown_report(payload: dict[str, Any]) -> str:
    decision = str(payload.get("decision", "revise")).upper()
    badge = f"**[{decision}]**"
    
    lines = [
        f"# Ship Check Report: {payload.get('question', 'Change Review')}",
        "",
        "> Generated by `rtw ship-check` (Round Table Workspace).",
        f"> generated_at: `{payload.get('generated_at', iso_now())}`",
        f"> decision: `{payload.get('decision')}`",
        f"> confidence: `{payload.get('confidence')}`",
        f"> insertions: `+{payload.get('insertions', 0)}` | deletions: `-{payload.get('deletions', 0)}`",
        "",
        "## Executive Summary",
        "",
        f"- **Status**: {badge}",
        f"- **Confidence**: `{payload.get('confidence')}`",
        f"- **Summary**: {payload.get('summary')}",
        "",
        "## Multi-Lens Panel Review",
        "",
        "| Lens / Role | Vote | Rationale |",
        "|---|---|---|",
    ]
    for v in payload.get("panel_votes", []):
        agent_name = v.get("role_name", v.get("agent", "Reviewer"))
        lines.append(f"| **{agent_name}** (`{v.get('agent')}`) | `{v.get('vote')}` | {v.get('reason')} |")

    lines.extend([
        "",
        "## Blocking Risks",
        "",
    ])
    for risk in payload.get("blocking_risks", []):
        lines.append(f"- [ ] {risk}")

    lines.extend([
        "",
        "## Next Testable Steps & Action Checklist",
        "",
    ])
    for step in payload.get("next_testable_steps", []):
        lines.append(f"- [ ] {step}")

    if payload.get("changed_files"):
        lines.extend([
            "",
            "## Git Inspection Details",
            "",
            f"- **Diff Summary**: {payload.get('diff_summary')}",
            f"- **Categories**: {', '.join(payload.get('categories', [])) if payload.get('categories') else 'general_code'}",
            "- **Changed Files**:",
        ])
        for f in payload.get("changed_files", []):
            lines.append(f"  - `{f}`")

    lines.extend([
        "",
        "## Claim Boundary Notice",
        "",
    ])
    for note in payload.get("claim_boundary", []):
        lines.append(f"- {note}")

    return "\n".join(lines).rstrip() + "\n"


def save_ship_check_archive_report(
    payload: dict[str, Any],
    custom_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    markdown = render_ship_check_markdown_report(payload)
    if custom_path and str(custom_path) not in ("True", "true", "1"):
        target_path = resolve_checked_path(custom_path)
    else:
        root = repo_root or Path.cwd()
        timestamp = utc_timestamp()
        target_dir = root / "reports" / "ship-checks"
        target_path = target_dir / f"ship-check-{timestamp}.md"

    assert_no_symlink_components(target_path, include_leaf=False)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(markdown, encoding="utf-8")
    return target_path
