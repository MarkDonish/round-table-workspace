# Changelog

All notable release-scope changes for this repository are documented here.

This changelog follows the repository release boundary in
`docs/release-readiness.md` and `docs/release-candidate-scope.md`: release notes
may claim the Codex local mainline scope only when the checked-in gate has no P0
blockers. Real third-party host-live and provider-live support require their own
live validation evidence.

## Unreleased

### Added

- Post-release consumer audit runner that clones a fresh release checkout and
  verifies the local-first consumer path from that checkout.
- Host/provider live lane evidence report that renders claimable, missing,
  blocked, pending, and provider-not-configured lanes without forcing live
  provider calls or third-party agent execution.

## v0.1.0 - 2026-04-26

### Released

- Promoted the validated `v0.1.0-rc4` support scope to the first stable
  local-first release.

### Supported Scope

- Codex local mainline for `/room`, `/debate`, and `/room -> /debate`.
- Checked-in protocol, prompts, skills, runtime bridges, and validation
  harnesses.
- Clone-friendly `LAUNCH.md` and agent consumer self-check.
- Claude Code project-skill discovery structure as an adapter layer.
- Default Claude Code CLI host-live support for the validated Mac account where
  `claude_code_live_validation.py` returned
  `claimable_as_default_claude_code_host_live=true`.
- Generic local agent adapter contract with fixture-backed validation.
- Third-party local agent JSON wrapper and validation matrix tooling.
- Chat Completions-compatible fallback/mock regression tooling.

### Not Claimed

- Claude Code host-live support on machines/accounts that have not rerun and
  passed `claude_code_live_validation.py`.
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent host-live support before
  each host passes its own live validation.
- Real Chat Completions-compatible provider-live support before `.env.room` and
  `.env.debate` are valid and `chat_completions_live_validation.py` passes.
- Universal production stability across every possible local agent host.

## v0.1.0-rc4 - 2026-04-26

### Added

- Host recipe consistency check to keep third-party local agent docs aligned
  with the checked-in host inventory candidates.
- Repo-local development checkpoint writer for durable continuity when host
  memory is read-only.
- Checked-in Claude Code host-live evidence report for this validated Mac
  account and default wrapper command.

### Changed

- Clarified third-party local agent host recipes, decision tree, and host-live
  claim rules for Claude Code, Gemini CLI, OpenCode, Aider, Goose, and Cursor
  Agent.
- Exposed copy-safe host validation argv in the local agent host validation
  matrix.
- Updated release readiness and release candidate reporting so checked-in,
  machine/account-scoped host-live evidence can support a claim without
  overclaiming every third-party agent host.
- Updated the clone-friendly consumer self-check summary so checked-in host-live
  evidence appears in the same support view as matrix live rows.

### Supported Scope

- Everything in `v0.1.0-rc3`.
- Default Claude Code CLI host-live support for the validated Mac account where
  `claude_code_live_validation.py` returned
  `claimable_as_default_claude_code_host_live=true`.
- Repo-local continuity checkpoints under `reports/checkpoints/generated/` as
  historical handoff evidence, not implementation source.

### Not Claimed

- Claude Code host-live support on machines/accounts that have not rerun and
  passed `claude_code_live_validation.py`.
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent host-live support before
  each host passes its own live validation.
- Real Chat Completions-compatible provider-live support before `.env.room` and
  `.env.debate` are valid and `chat_completions_live_validation.py` passes.

## v0.1.0-rc3 - 2026-04-25

### Added

- Root `LAUNCH.md` quickstart for clone-friendly self-checks and runtime path
  selection.

### Supported Scope

- Everything in `v0.1.0-rc2`.
- Clone-friendly launch quickstart as the shortest safe entrypoint for newly
  cloned copies and external local agent hosts.

## v0.1.0-rc2 - 2026-04-25

### Added

- Source-truth boundary audit tooling and historical materials guidance to keep
  `reports/` and `artifacts/` from being mistaken for active implementation
  source.
- Clone-friendly agent consumer self-check and quickstart documentation for
  Codex, Claude Code, and generic local agent users.

### Supported Scope

- Everything in `v0.1.0-rc1`.
- Source-truth boundary audit tooling.
- Clone-friendly agent consumer self-check tooling.

## v0.1.0-rc1 - 2026-04-24

Release candidate for the Codex local mainline scope.

### Supported Scope

- Codex local mainline for `/room`, `/debate`, and `/room -> /debate`.
- Checked-in protocol, prompts, skills, runtime bridges, and validation harnesses.
- Claude Code project-skill discovery structure as an adapter layer, not a forked
  implementation source.
- Generic local agent adapter contract with fixture-backed validation.
- Third-party local agent JSON wrapper tooling and local host validation matrix.
- Chat Completions-compatible fallback/mock regression tooling.

### Validation Baseline

- `release_readiness_check.py --include-fixture-runs --strict-git-clean` passed
  with no P0 blockers before this release note was prepared.
- `release_candidate_report.py --include-fixture-runs --strict-git-clean`
  returned `release_decision=ready_for_codex_local_mainline_scope`.
- The release gate confirmed source-truth files, runtime entrypoints, Claude Code
  project-skill structure, host inventory/matrix tooling, provider readiness
  tooling, generic fixture validation, and JSON wrapper validation.

### Not Claimed

- Real Claude Code host-live execution is not claimed while the local account is
  not logged in or entitled.
- Gemini CLI, OpenCode, Aider, Goose, and Cursor Agent host-live execution are
  not claimed without per-host live validation.
- Real Chat Completions-compatible provider-live support is not claimed until
  `.env.room` and `.env.debate` are valid and `chat_completions_live_validation.py`
  passes.
- Universal production stability across all possible local agent hosts is not
  claimed.
