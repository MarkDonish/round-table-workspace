# NEXT STEPS

> Purpose: active source-of-truth task queue for the next local agent or developer continuing this repository.
> Last updated: 2026-04-28

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

python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence

python3 .codex/skills/room-skill/runtime/github_release_publication_check.py \
  --state-root /tmp/round-table-github-release-publication
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

Latest tagged release target: `v0.1.3`.

Current `main` is intended to match the `v0.1.3` local-first launch scope once
the tag is pushed. Do not assume any later post-`v0.1.3` changes are included in
that tag unless a later tag is cut.

Latest checked-in Claude Code host-live evidence:

- `reports/CLAUDE_CODE_HOST_LIVE_VALIDATION_2026-04-27.md`
- `claimable_as_default_claude_code_host_live=true`
- The claim remains machine/account-scoped; every new machine/account must rerun
  `claude_code_live_validation.py` before claiming Claude Code host-live support.

## Priority Queue

| Priority | Task | Status | Why Now | Completion Standard |
|---|---|---|---|---|
| P0 | Codex local mainline blocker | None known | The strict release gate currently reports no P0 blockers | Keep `release_readiness_check.py --include-fixture-runs --strict-git-clean` green |
| P1 | Publish `v0.1.3` GitHub Release page | Completed | GitHub Actions run `25049260899` published the release page at `2026-04-28T11:06:45Z` | `gh release view v0.1.3 --repo MarkDonish/round-table-workspace` reports non-draft, non-prerelease, published |
| P1 | Promote `v0.1.3` patch release | Completed | Current `main` has final P2 launch-boundary evidence not present in `v0.1.2` | Release notes/changelog point to v0.1.3, strict release gate passes from clean Git tree, tag is pushed, release page is published |
| P1 | Publish `v0.1.2` GitHub Release page | Completed | GitHub Actions run `25040681309` published the release page at `2026-04-28T07:49:56Z` | `gh release view v0.1.2 --repo MarkDonish/round-table-workspace` reports non-draft, non-prerelease, published |
| P1 | Promote `v0.1.2` patch release | Completed | Current `main` has release-scope changes not present in `v0.1.1` | Release notes/changelog point to v0.1.2, strict release gate passes from clean Git tree, tag is pushed, release page is published |
| P1 | Publish `v0.1.1` GitHub Release page | Completed | The tag is pushed, authenticated `gh release view` confirmed `v0.1.1` is published, and the previous Actions failure was caused by an unsupported `isLatest` JSON field | Historical release page remains available |
| P1 | Promote `v0.1.1` patch release | Completed | `v0.1.0` predates post-release consumer audit and live lane evidence report tooling | Release notes/changelog point to v0.1.1, strict release gate passes from clean Git tree, tag is pushed |
| P1 | Add host/provider live lane evidence report | Completed | Launch communication needs one claim-safe entry that separates claimable, missing, blocked, pending, and provider-not-configured lanes | `live_lane_evidence_report.py` writes JSON/Markdown and docs point to it |
| P1 | Add post-release consumer audit | Completed | Tagged releases need a fresh-checkout proof path, not just current-worktree validation | `post_release_consumer_audit.py --ref v0.1.3` passes after the tag is pushed and docs point to it |
| P1 | Promote `v0.1.0-rc4` to `v0.1.0` | Completed | rc4 was the final launch-prep candidate and did not require widening the support claim | Final release notes/changelog point to v0.1.0, strict release gate passes from clean Git tree, tag is pushed |
| P1 | Cut `v0.1.0-rc4` release candidate | Completed | `v0.1.0-rc3` predates Claude Code host-live evidence and repo-local checkpoints | Release notes/changelog point to rc4, strict release gate passes from clean Git tree, tag is pushed |
| P1 | Improve third-party local agent validation matrix usability | Completed | The matrix now exposes both rendered shell commands and canonical argv for each selectable host command | Matrix output exposes copy-safe argv/run command evidence and fixture validation still passes |
| P1 | Retry real Claude Code default CLI live validation | Completed and refreshed on this Mac | The default wrapper passed preflight, smoke, and full `/room -> /debate` integration on 2026-04-27 | Full default wrapper reported `claimable_as_default_claude_code_host_live=true`; future machines still need their own live validation |
| P1 | Keep checked-in Claude Code evidence discovery fresh | Completed | Release/readiness tools now need to follow the latest valid report, not a hard-coded dated report | `release_readiness_check.py`, `release_candidate_report.py`, and `live_lane_evidence_report.py` point to `reports/CLAUDE_CODE_HOST_LIVE_VALIDATION_2026-04-27.md` |
| P1 | Keep current source-of-truth docs aligned after each runtime change | Ongoing | Future agents start from `docs/`, not old session reports | `README.md`, `docs/NEXT-STEPS.md`, release docs, and relevant adapter docs agree |
| P2 | Use repo-local development checkpoints when host memory is read-only | Available | Host-level memory may be readable but not writable; cross-session continuity should not depend on chat history only | `development_checkpoint.py` writes Markdown/JSON under `reports/checkpoints/generated/` and docs keep reports as historical |
| P2 | Run real Chat Completions-compatible provider live validation | Externally blocked on real provider config | Provider lane is optional fallback, but still part of full multi-provider readiness; this Mac's `.env.room` and `.env.debate` currently have no real provider URLs | A real local `.env.room` and `.env.debate` are supplied intentionally, `chat_completions_readiness.py` reports `ready_for_live_run=true`, and `chat_completions_live_validation.py` passes |
| P2 | Validate additional real local agent hosts | OpenCode direct smoke passes, but this Mac's full OpenCode live matrix still fails inside OpenCode's local SQLite/WAL/upstream execution path | Gemini/Aider/Goose/Cursor Agent CLIs are not installed here; OpenCode is installed but not claimable until the host matrix passes | OpenCode reaches `matrix_status=live_passed`, or the host remains explicitly non-claimable with saved failure evidence; unavailable hosts are documented with `--skip-host HOST_ID=REASON` |
| P3 | Reduce historical-material ambiguity | Ongoing | Old reports and artifacts are useful but can mislead if treated as current source | `source_boundary_audit.py` remains green and docs clearly point to active sources |

## Recommended Next Task

There are no known P0/P1 release blockers for the Codex local mainline. The
remaining active work is P2 evidence expansion and must not delay launch unless
the launch claim is widened beyond the current scope.

Keep `v0.1.3` release publication evidence current if the release body is edited
again. The checked-in GitHub Actions release publisher has already run
successfully for `v0.1.2`; `v0.1.3` should use the same workflow after its tag
is pushed. Verify publication with:

```bash
python3 .codex/skills/room-skill/runtime/github_release_publication_check.py \
  --tag v0.1.3 \
  --release-draft docs/releases/v0.1.3-github-release.md \
  --strict-published \
  --state-root /tmp/round-table-github-release-publication
```

If the current host has authenticated `gh`, the checker confirms the private
repository release page through `gh release view`; unauthenticated API `404`
alone is not treated as authoritative. If the current host has no `gh` or
token, that checker can still verify the local tag, draft, and workflow source,
but workflow run status and release page publication will remain
`unknown_auth_required` / `unknown_requires_authenticated_check`.

If another real third-party local agent is available on the target machine, run
P2 real host validation with the matrix output, then regenerate the live lane
evidence report before claiming support. On this Mac, OpenCode is installed and
has a checked-in wrapper. After backing up the OpenCode state DB, confirming
`PRAGMA integrity_check;` returned `ok`, running
`PRAGMA wal_checkpoint(TRUNCATE);`, and passing a direct `opencode run` smoke,
the latest forced OpenCode live matrix still failed inside the wrapped OpenCode
process. It is not claimable:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-installed \
  --force-host opencode \
  --state-root /tmp/round-table-local-agent-host-validation-matrix

python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

See `reports/OPENCODE_HOST_LIVE_ATTEMPT_2026-04-28.md` and
`reports/P2_PROVIDER_OPENCODE_LIVE_LANES_2026-04-28.md` for the historical
attempt records. Treat OpenCode as P2 non-claimable until the matrix returns
`matrix_status=live_passed`; this does not block the Codex local mainline.

If a host is intentionally unavailable on the current machine, record that as
an explicit non-claim instead of leaving it as ambiguous missing work:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --skip-host 'gemini_cli=not installed on this machine; not claimed' \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

If no additional real host is available or entitled, keep that lane
blocked/pending and continue with source-of-truth alignment. Run P2 provider
live validation only when `.env.room` and `.env.debate` are intentionally
configured with real provider URLs/models/tokens. The current Mac provider
readiness result is not ready for live run because both
`ROOM_CHAT_COMPLETIONS_URL` and `DEBATE_CHAT_COMPLETIONS_URL` are missing.

After tagging a release, audit the fresh consumer path:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.3 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

## Guardrails

- Do not claim fixture validation as real host-live support.
- Do not require provider URLs for the local mainline.
- Do not fork the `/room` or `/debate` protocol into `.claude/skills/`.
- Do not mutate `reports/` or `artifacts/` to fix active behavior.
- Commit and push each verified milestone to `origin/main`.
