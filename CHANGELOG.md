# Changelog

All notable release-scope changes for this repository are documented here.

This changelog follows the repository release boundary in
`docs/release-readiness.md` and `docs/release-candidate-scope.md`: release notes
may claim the Codex local mainline scope only when the checked-in gate has no P0
blockers. Real third-party host-live and provider-live support require their own
live validation evidence.

## Unreleased

### Added

- Agent Factory Phase 1 backend foundation: custom/candidate registry,
  manifest/registry/selection-request schemas, Agent Builder skill runtime,
  Duan Yongping example bundle, and `./rtw agent` CLI bridge.
- `./rtw room` and `./rtw debate` now run fixture-backed local runtime paths,
  write standard `runs/<run_id>/` artifacts, and validate portable schema
  projections.
- Canonical handoff conversion helpers in `roundtable_core/protocol/handoff.py`
  and runtime artifact projection helpers in
  `roundtable_core/protocol/projections.py`.
- Machine-readable `agents/registry.json` plus registry sync checks so runtime
  no longer parses `docs/agent-registry.md` tables.
- Negative fixture runner for schema and claim-boundary rejection checks.
- `roundtable_core.commands` service layer for schema validation, fixture-backed
  room/debate runs, golden demo generation, and CLI state-root resolution.
- `roundtable_core.protocol.debate_result_builder` with allow/reject/follow-up
  portable `debate-result` construction paths.
- `docs/protocol-versioning.md` and GitHub Actions CI for the core non-secret
  validation chain.

### Changed

- `./rtw demo startup-idea` now generates output through the fixture-backed room
  and debate runtime paths instead of copying only static demo files.
- JSON Schema validation fallback now supports the conditional and composition
  keywords used by current schemas and reports its validator boundary.
- Default state roots now use `tempfile.gettempdir()`, with `python -m
  roundtable` and `pip install -e .` supported through `pyproject.toml`.
- Decision quality evals now use a seven-dimension rubric engine with positive
  and negative fixtures.
- Prompt rendering defaults to explicit variable contracts, and structured
  output parsing reports all JSON candidates.
- `skills_src` manifests are now strict `.json`, and skill drift checks include
  frontmatter, entry-command, generated-section, and forbidden-claim checks.
- Claim boundary dashboard snapshots now include freshness metadata and source
  commit scope; README points users to live `./rtw evidence`/`release-check`
  commands for current state.

## v0.2.0-alpha - 2026-04-29

### Added

- Unified CLI expansion with `./rtw release-check`, `./rtw interactive`, and
  `./rtw demo startup-idea`.
- `schemas/room-to-debate-handoff.schema.json` and matching fixture for the
  `/room -> /debate` handoff contract.
- `docs/decision-quality-rubric.md`, fixture/mock decision-quality eval cases,
  and regression fixture checks for room/debate/handoff flows.
- Skill generation and drift-check tooling under `skills_src/` and `scripts/`.
- Source-truth consistency, claim-boundary dashboard, and aggregate release
  check automation.
- `docs/index.md` and `docs/skill-generation.md` for documentation governance.

- Initial `roundtable_core/` package for host-neutral validation, state-root,
  evidence metadata, and claim boundary helpers.
- `docs/roadmap.md` and `docs/milestones/v0.2.0.md` for v0.2.0 planning.

### Changed

- `./rtw validate --schema ...` now uses `roundtable_core.validation` while the
  legacy `roundtable.schema_validation` import path remains compatible.
- `agent_consumer_self_check.py` now writes standardized JSON/Markdown aliases
  and a `state-root/runs/<run_id>/` record with input, output, evidence, and
  summary files.
- Codex and Claude skill entrypoints now include generated summary sections and
  long implementation-boundary content is moved into `references/`.
- `docs/roadmap.md` and `docs/milestones/v0.2.0.md` now mark all 27 v0.2.0
  development-canvas task IDs as implemented on `main`.

## v0.1.3 - 2026-04-28

### Added

- Final P2 provider/OpenCode live-lane closure report that records the real
  local attempts before launch.

### Changed

- Clarified that current `main` has no known P0/P1 Codex local mainline
  blockers after the P2 closure pass.
- Updated release support scope to separate launchable local-first support from
  non-claimable provider-live and OpenCode host-live lanes.
- Refreshed GitHub Release publication defaults for `v0.1.3`.

### Supported Scope

- Everything in `v0.1.2`.
- More precise launch-boundary documentation for provider/OpenCode P2 gaps.

### Not Claimed

- OpenCode host-live support. A direct OpenCode smoke passed on this Mac, but
  the full host-live matrix still failed inside OpenCode's local
  SQLite/WAL/upstream execution path.
- Real provider-live support before `.env.room` and `.env.debate` contain real
  provider URLs/models/tokens and `chat_completions_live_validation.py` passes.
- Universal production stability across every possible local agent host.

## v0.1.2 - 2026-04-28

### Added

- GitHub Release publication status checker that reports whether the target
  release page is published, whether the local tag and release draft exist, and
  whether the current host has authenticated `gh` or token-based publication
  capability.
- Release readiness and release candidate tooling now discover the latest
  checked-in Claude Code host-live evidence report instead of hard-coding a
  single dated report.
- Refreshed checked-in Claude Code host-live evidence for the validated Mac
  account on 2026-04-27.
- OpenCode local CLI wrapper that feeds the round-table prompt through
  `opencode run`, avoids unstable file attachment paths, and retries only
  narrow transient SQLite/WAL failures from OpenCode's local state store.
- Historical OpenCode host-live attempt report that records the current
  non-claimable OpenCode state without blocking the Codex local mainline.

### Changed

- Hardened `/room -> /debate` upgrade output handling so
  `handoff_packet.generated_at_turn` can only be normalized from placeholder
  `0` or `None` when prompt input and sibling metadata agree on the same
  positive turn.
- Updated `/room` upgrade prompt instructions to clarify that schema `0` values
  are placeholders and must not be copied as final positive-turn output.

### Supported Scope

- Everything in `v0.1.1`.
- GitHub Release publication status checking and workflow defaults for
  `v0.1.2`.
- OpenCode adapter tooling as a checked-in local-agent wrapper recipe.

### Not Claimed

- OpenCode host-live support. The latest forced matrix attempt on this Mac
  failed inside OpenCode's local SQLite/WAL checkpoint path and remains P2.
- Real provider-live support before `.env.room` and `.env.debate` are valid and
  `chat_completions_live_validation.py` passes.
- Universal production stability across every possible local agent host.

## v0.1.1 - 2026-04-26

### Added

- Post-release consumer audit runner that clones a fresh release checkout and
  verifies the local-first consumer path from that checkout.
- Host/provider live lane evidence report that renders claimable, missing,
  blocked, pending, and provider-not-configured lanes without forcing live
  provider calls or third-party agent execution.

### Supported Scope

- Everything in `v0.1.0`.
- Fresh-checkout release audit tooling for maintainers and local agent hosts.
- Focused live-lane evidence reporting for host/provider support claims.

### Not Claimed

- Claude Code host-live support on machines/accounts that have not rerun and
  passed `claude_code_live_validation.py`.
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent host-live support before
  each host passes its own live validation.
- Real Chat Completions-compatible provider-live support before `.env.room` and
  `.env.debate` are valid and `chat_completions_live_validation.py` passes.
- Universal production stability across every possible local agent host.

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
