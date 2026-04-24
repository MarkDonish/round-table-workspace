# AGENTS.md

Project entrypoint for this repository. Keep this file short and repo-local so it works the same way on Windows, Mac, and Codex Cloud.

## Always-On Rules

1. Do not fabricate missing facts. If information is insufficient, say `信息缺失`.
2. Keep outputs practical, clear, and structured. Avoid slogans, fluff, and unsupported certainty.
3. Distinguish facts, inferences, uncertainties, and recommendations when doing multi-agent or multi-perspective work.
4. Do not enter `/room` or `/debate` unless the user explicitly starts with that command or is already continuing inside that mode.
5. Prefer repo-relative paths and repo-local references over machine-specific absolute home-directory paths.

## Source Of Truth

Treat this repository as the long-term source of truth for the round-table system.

Primary source directories:

- `README.md`
- `AGENTS.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/debate-roundtable-skill/`
- `.codex/skills/room-skill/`
- `.codex/skills/*/roundtable-profile.md`
- `.claude/skills/` (Claude Code project-skill adapter layer only; not protocol implementation)

Historical material lives under:

- `reports/`
- `artifacts/`

## Development Sync

For every new development task, follow:

- `docs/development-sync-protocol.md`
- `docs/superpowers/local-development-integration.md` when local Superpowers is installed

Default rule:

- develop locally
- verify locally
- commit verified changes
- push to `origin/main`
- report completed work, verification, and remaining gaps

Do not treat exploratory local edits as complete work.
Do not treat `reports/` as the active implementation source.

Local Superpowers is a workflow helper, not a source-of-truth override.

## Room Roundtable

`/room` is an explicit-only stateful roundtable mode. It is not the default mode.

On `/room`, use:

- Skill: `.codex/skills/room-skill/SKILL.md`
- Claude Code project skill: `.claude/skills/room/SKILL.md`
- Supporting docs:
  - `docs/room-runtime-status.md`
  - `docs/room-runtime-bridge.md`
  - `docs/host-adapter-architecture.md`
  - `docs/generic-local-agent-adapter.md`
  - `docs/local-agent-host-recipes.md`
  - `docs/claude-code-skill-adapter.md`
  - `docs/room-architecture.md`
  - `docs/room-selection-policy.md`
  - `docs/room-chat-contract.md`
  - `docs/agent-registry.md`
  - `docs/room-to-debate-handoff.md`
  - `prompts/room-selection.md`
  - `prompts/room-chat.md`
  - `prompts/room-summary.md`
  - `prompts/room-upgrade.md`

## Debate Roundtable

`/debate` is an explicit-only roundtable dispatcher. It is not the default mode.

On `/debate`, use:

- Skill: `.codex/skills/debate-roundtable-skill/SKILL.md`
- Claude Code project skill: `.claude/skills/debate/SKILL.md`
- Supporting docs:
  - `docs/debate-runtime-bridge.md`
  - `docs/host-adapter-architecture.md`
  - `docs/generic-local-agent-adapter.md`
  - `docs/local-agent-host-recipes.md`
  - `docs/claude-code-skill-adapter.md`
  - `docs/debate-skill-architecture.md`
  - `docs/agent-role-map.md`
  - `docs/reviewer-protocol.md`
  - `docs/red-flags.md`
  - `docs/room-to-debate-handoff.md`
  - `prompts/debate-roundtable.md`
  - `prompts/debate-reviewer.md`
  - `prompts/debate-followup.md`

Historical archive only when needed for archaeology, not as active source of truth:

- `docs/archive/AGENTS.full-20260411-142320.md`

Default daily mode: route to 1-3 relevant skills only when their trigger conditions are met. Do not auto-run a room or roundtable.
