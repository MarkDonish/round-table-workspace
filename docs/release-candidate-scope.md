# Release Support Scope

This document is the source of truth for turning the current readiness checks into a claim-safe release summary.

## Current Release Claim

The repository may currently be claimed as ready for:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- checked-in protocol, prompts, skills, runtime bridges, and validation harnesses
- Claude Code project-skill discovery structure
- default Claude Code CLI host-live support on the Mac where `claude_code_live_validation.py` reports `claimable_as_default_claude_code_host_live=true`
- generic local agent adapter contract with fixture-backed validation
- third-party local agent JSON wrapper and host validation matrix tooling
- OpenCode local-agent wrapper tooling without host-live claim
- host/provider live-lane evidence report tooling
- clone-friendly agent consumer self-check tooling
- clone-friendly launch quickstart
- GitHub Release publication status checker and workflow source
- Chat Completions-compatible fallback/mock regression tooling

This is not the same as claiming every local agent host or every provider is live-validated.

## Current Release Artifact

The current release is `v0.1.2`.

Use:

- `CHANGELOG.md` for the release history.
- `docs/releases/v0.1.2.md` for the human-readable release note.
- `release_candidate_report.py` output for machine-readable support-scope evidence.

The tag must point to a commit that has passed the strict release gate.

## Not Claimed

Do not claim these until the matching live validation report exists:

- real Claude Code host-live support on machines/accounts that have not passed `claude_code_live_validation.py`
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent host-live support before a host matrix row reports `live_passed`
- real Chat Completions-compatible provider support before `.env.room` and `.env.debate` are valid and `chat_completions_live_validation.py` passes
- universal production stability across all possible local agent hosts

## One-Command Report

Generate the claim-safe release report:

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate
```

The command writes:

- `/tmp/round-table-release-candidate/release-candidate-report.json`
- `/tmp/round-table-release-candidate/release-candidate-report.md`

Use the Markdown report for human review and the JSON report for future automation.

For a focused host/provider support-claim view, generate the live lane evidence
report:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

## Interpretation Rules

- `release_decision: "ready_for_codex_local_mainline_scope"` means the Codex local mainline can be launched within the current scope.
- `release_decision: "blocked"` means at least one P0 release gate blocker exists.
- `real_host_live_passed` is the list that can support a real third-party host-live claim. It may be populated by host matrix `live_passed` rows or by checked-in machine/account-scoped live evidence reports that cite the checked-in validation command and a `claimable=true` result.
- `provider_live_ready: false` means provider support is still fallback/mock/readiness tooling only.
- `live_lane_evidence_report.py` is the focused view for current claimable, missing, blocked, pending, and provider-not-configured lanes.
- `reports/` remains historical evidence and must not override this document or `docs/release-readiness.md`.

## Current Known Gaps

The current non-blocking gaps are expected unless the local machine has more authenticated tools configured:

- Claude Code CLI may be installed but auth-blocked on machines other than the validated Mac.
- Gemini CLI, Aider, Goose, and Cursor Agent may be absent from `PATH`.
- OpenCode may be installed but still not host-live claimable until its matrix
  row reports `live_passed`; the latest Mac attempt failed inside OpenCode's
  local SQLite/WAL checkpoint path.
- `.env.room` and `.env.debate` may be present but not provider-live ready.

These gaps do not block the Codex local mainline release scope, but they do block broader host/provider support claims.
