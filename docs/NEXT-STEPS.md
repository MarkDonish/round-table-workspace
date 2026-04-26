# NEXT STEPS

> Purpose: active source-of-truth task queue for the next local agent or developer continuing this repository.
> Last updated: 2026-04-26

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

Current release target: `v0.1.0`.

## Priority Queue

| Priority | Task | Status | Why Now | Completion Standard |
|---|---|---|---|---|
| P0 | Codex local mainline blocker | None known | The strict release gate currently reports no P0 blockers | Keep `release_readiness_check.py --include-fixture-runs --strict-git-clean` green |
| P1 | Add post-release consumer audit | Completed | `v0.1.0` is tagged; new users need a fresh-checkout proof path, not just current-worktree validation | `post_release_consumer_audit.py --ref v0.1.0` passes and docs point to it |
| P1 | Promote `v0.1.0-rc4` to `v0.1.0` | Completed | rc4 was the final launch-prep candidate and did not require widening the support claim | Final release notes/changelog point to v0.1.0, strict release gate passes from clean Git tree, tag is pushed |
| P1 | Cut `v0.1.0-rc4` release candidate | Completed | `v0.1.0-rc3` predates Claude Code host-live evidence and repo-local checkpoints | Release notes/changelog point to rc4, strict release gate passes from clean Git tree, tag is pushed |
| P1 | Improve third-party local agent validation matrix usability | Completed | The matrix now exposes both rendered shell commands and canonical argv for each selectable host command | Matrix output exposes copy-safe argv/run command evidence and fixture validation still passes |
| P1 | Retry real Claude Code default CLI live validation | Completed on this Mac | The default wrapper passed preflight, smoke, and full `/room -> /debate` integration on 2026-04-26 | Full default wrapper reported `claimable_as_default_claude_code_host_live=true`; future machines still need their own live validation |
| P1 | Keep current source-of-truth docs aligned after each runtime change | Ongoing | Future agents start from `docs/`, not old session reports | `README.md`, `docs/NEXT-STEPS.md`, release docs, and relevant adapter docs agree |
| P2 | Use repo-local development checkpoints when host memory is read-only | Available | Host-level memory may be readable but not writable; cross-session continuity should not depend on chat history only | `development_checkpoint.py` writes Markdown/JSON under `reports/checkpoints/generated/` and docs keep reports as historical |
| P2 | Run real Chat Completions-compatible provider live validation | Not configured | Provider lane is optional fallback, but still part of full multi-provider readiness | `.env.room` and `.env.debate` are locally ready and `chat_completions_live_validation.py` passes |
| P2 | Validate additional real local agent hosts | Not started on this Mac | Gemini/OpenCode/Aider/Goose/Cursor Agent CLIs are not installed here | Each installed host either reaches `matrix_status=live_passed` or is explicitly documented as skipped/blocked |
| P3 | Reduce historical-material ambiguity | Ongoing | Old reports and artifacts are useful but can mislead if treated as current source | `source_boundary_audit.py` remains green and docs clearly point to active sources |

## Recommended Next Task

If another real third-party local agent is available on the target machine, run
P2 real host validation with the matrix output:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-live-ready \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

If no additional real host is available or entitled, keep that lane
blocked/pending and continue with source-of-truth alignment or P2 provider live validation only
when `.env.room` and `.env.debate` are intentionally configured.

After tagging a release, audit the fresh consumer path:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.0 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

## Guardrails

- Do not claim fixture validation as real host-live support.
- Do not require provider URLs for the local mainline.
- Do not fork the `/room` or `/debate` protocol into `.claude/skills/`.
- Do not mutate `reports/` or `artifacts/` to fix active behavior.
- Commit and push each verified milestone to `origin/main`.
