# Release Candidate Scope

This document is the source of truth for turning the current readiness checks into a claim-safe release candidate summary.

## Current Release Candidate Claim

The repository may currently be claimed as ready for:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- checked-in protocol, prompts, skills, runtime bridges, and validation harnesses
- Claude Code project-skill discovery structure
- generic local agent adapter contract with fixture-backed validation
- third-party local agent JSON wrapper and host validation matrix tooling
- Chat Completions-compatible fallback/mock regression tooling

This is not the same as claiming every local agent host or every provider is live-validated.

## Not Claimed

Do not claim these until the matching live validation report exists:

- real Claude Code host-live support when the local account is not logged in or entitled
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent host-live support before a host matrix row reports `live_passed`
- real Chat Completions-compatible provider support before `.env.room` and `.env.debate` are valid and `chat_completions_live_validation.py` passes
- universal production stability across all possible local agent hosts

## One-Command Report

Generate the release candidate report:

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

## Interpretation Rules

- `release_decision: "ready_for_codex_local_mainline_scope"` means the Codex local mainline can be launched within the current scope.
- `release_decision: "blocked"` means at least one P0 release gate blocker exists.
- `real_host_live_passed` is the only list that can support a real third-party host-live claim.
- `provider_live_ready: false` means provider support is still fallback/mock/readiness tooling only.
- `reports/` remains historical evidence and must not override this document or `docs/release-readiness.md`.

## Current Known Gaps

The current non-blocking gaps are expected unless the local machine has more authenticated tools configured:

- Claude Code CLI may be installed but auth-blocked.
- Gemini CLI, OpenCode, Aider, Goose, and Cursor Agent may be absent from `PATH`.
- `.env.room` and `.env.debate` may be present but not provider-live ready.

These gaps do not block the Codex local mainline release scope, but they do block broader host/provider support claims.
