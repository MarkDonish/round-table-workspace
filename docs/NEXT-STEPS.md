# NEXT STEPS

> Purpose: active source-of-truth task queue for the next local agent or developer continuing this repository.
> Last updated: 2026-04-25

This file is not a historical report. It must reflect the current checked-in
state from `README.md`, `docs/release-readiness.md`,
`docs/source-truth-map.md`, and the runtime validators.

## Start Here

Before changing code or docs, run:

```bash
git status -sb
git log --oneline -5
git remote -v

python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --include-fixture-runs \
  --strict-git-clean \
  --output-json /tmp/round-table-release-readiness.json
```

Then read:

- `AGENTS.md`
- `README.md`
- `docs/development-sync-protocol.md`
- `docs/source-truth-map.md`
- `docs/release-readiness.md`
- `docs/local-agent-host-recipes.md`
- `docs/provider-live-readiness.md`

Do not use `reports/` or `artifacts/` as implementation source.

## Current Status

The current launchable scope is the Codex local mainline:

- `/room`
- `/debate`
- `/room -> /debate`
- checked-in prompts, runtime bridges, validation harnesses
- generic local agent adapter contract with fixture validation
- Claude Code project-skill discovery layer
- provider fallback tooling with mock regression

This does not mean every real local agent host or provider has been
live-validated.

## Priority Queue

| Priority | Task | Status | Why Now | Completion Standard |
|---|---|---|---|---|
| P0 | Codex local mainline blocker | None known | The strict release gate currently reports no P0 blockers | Keep `release_readiness_check.py --include-fixture-runs --strict-git-clean` green |
| P1 | Improve third-party local agent validation matrix usability | Open | The matrix classifies hosts, but generated wrapper commands are hard to reuse when nested quoting is involved | Matrix output exposes copy-safe argv/run command evidence and fixture validation still passes |
| P1 | Retry real Claude Code default CLI live validation | Externally blocked | The wrapper now separates preflight, smoke, and full integration; the last real smoke hit Claude-side `503 No available accounts` | Full default wrapper reports `claimable_as_default_claude_code_host_live=true` |
| P1 | Keep current source-of-truth docs aligned after each runtime change | Ongoing | Future agents start from `docs/`, not old session reports | `README.md`, `docs/NEXT-STEPS.md`, release docs, and relevant adapter docs agree |
| P2 | Run real Chat Completions-compatible provider live validation | Not configured | Provider lane is optional fallback, but still part of full multi-provider readiness | `.env.room` and `.env.debate` are locally ready and `chat_completions_live_validation.py` passes |
| P2 | Validate additional real local agent hosts | Not started on this Mac | Gemini/OpenCode/Aider/Goose/Cursor Agent CLIs are not installed here | Each installed host either reaches `matrix_status=live_passed` or is explicitly documented as skipped/blocked |
| P3 | Reduce historical-material ambiguity | Ongoing | Old reports and artifacts are useful but can mislead if treated as current source | `source_boundary_audit.py` remains green and docs clearly point to active sources |

## Recommended Next Task

Work on P1: improve the local agent host validation matrix so third-party agent
users get copy-safe, machine-readable validation commands and clearer evidence
about what was actually run.

Suggested implementation direction:

1. Add a structured `recommended_validation_argv` field next to the rendered
   shell command.
2. Keep `recommended_validation_command` for human copy/paste.
3. Ensure the matrix report still classifies missing, blocked, pending,
   live-passed, and live-failed lanes without forcing live execution by default.
4. Validate with `local_agent_host_validation_matrix.py`,
   `host_recipes_consistency_check.py`, and the strict release gate.

## Guardrails

- Do not claim fixture validation as real host-live support.
- Do not require provider URLs for the local mainline.
- Do not fork the `/room` or `/debate` protocol into `.claude/skills/`.
- Do not mutate `reports/` or `artifacts/` to fix active behavior.
- Commit and push each verified milestone to `origin/main`.
