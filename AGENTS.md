# AGENTS.md

Project entrypoint for this repository. Keep this file short and repo-local so it works the same way on Windows, Mac, and Codex Cloud.

## Always-On Rules

1. Do not fabricate missing facts. If information is insufficient, say `信息缺失`.
2. Keep outputs practical, clear, and structured. Avoid slogans, fluff, and unsupported certainty.
3. Distinguish facts, inferences, uncertainties, and recommendations when doing multi-agent or multi-perspective work.
4. Do not enter roundtable mode unless the user explicitly starts with `/debate`.
5. Prefer repo-relative paths and repo-local references over machine-specific absolute home-directory paths.

## Source Of Truth

Treat this repository as the long-term source of truth for the round-table system.

Primary source directories:

- `README.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/debate-roundtable-skill/`
- `.codex/skills/*/roundtable-profile.md`

Historical material lives under:

- `reports/`
- `artifacts/`

## Debate Roundtable

`/debate` is an explicit-only roundtable dispatcher. It is not the default mode.

On `/debate`, use:

- Skill: `.codex/skills/debate-roundtable-skill/SKILL.md`
- Archived spec: `docs/archive/AGENTS.full-20260411-142320.md`
- Supporting docs:
  - `docs/debate-skill-architecture.md`
  - `docs/agent-role-map.md`
  - `docs/reviewer-protocol.md`
  - `docs/red-flags.md`
  - `prompts/debate-roundtable.md`
  - `prompts/debate-reviewer.md`
  - `prompts/debate-followup.md`

Default daily mode: route to 1-3 relevant skills only when their trigger conditions are met. Do not auto-run a roundtable.
