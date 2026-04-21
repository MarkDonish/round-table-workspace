# Session 51: Retention Apply Execution

Date: 2026-04-19

## Goal

Ship the smallest safe follow-up after Session 50's preview-first retention policy:

1. add an explicit retention execution surface for saved room sessions
2. reuse the existing retention filter contract instead of inventing a broader policy DSL
3. keep delete / purge / repair / preview semantics unchanged and audit-friendly

## What Changed

### 1. Added an explicit retention apply surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--apply-room-session-retention --room-session-catalog <room-session-catalog.json> --session-updated-before <iso-datetime>`
- Behavior:
  - retention apply scans the explicit session catalog with `includeArchived: true`
  - older live sessions are archived in place
  - older archived sessions with an existing saved session file are purged
  - the command stays explicit and does not introduce automatic retention execution

### 2. Retention apply reuses the existing retention filter surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Supported filters:
  - `--session-search <text>`
  - `--session-status <active|upgraded>`
  - `--session-sort <updated|name|status>`
  - `--session-order <asc|desc>`
  - `--session-limit <n>`
  - `--session-updated-before <iso-datetime>`
- Behavior:
  - apply follows the same matched slice the preview already exposed
  - this keeps retention narrow, explicit, and aligned with the existing catalog-discoverability contract

### 3. Retention apply is archive-first and all-or-nothing for blocked purge candidates

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Validation:
  - `--apply-room-session-retention` requires `--room-session-catalog`
  - `--apply-room-session-retention` also requires `--session-updated-before`
- Safety boundary:
  - before mutation, apply preflights every matched archived session that would be purged
  - if any matched archived session is blocked because its saved session file is missing, the whole run aborts
  - live sessions are not archived first and then half-completed; the command fails before mutation

## Scope Boundary

Implemented now:

- explicit retention execution surface
- retention apply reusing the existing search / status / sort / order / limit / updated-before filters
- archive older live sessions + purge older archived sessions in one explicit run
- all-or-nothing blocked-purge safety boundary for missing saved session files
- no rollback of save/resume, catalog, lifecycle, cleanup-v1, cleanup preview, or retention preview semantics

Still out of scope:

- automatic retention daemons or background cleanup
- broader retention DSLs or schedulers
- pagination / session browser UI
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can apply a room-session retention policy by archiving live matches and purging archived matches`
- `CLI room-session retention apply aborts before mutation when any matched archived session is blocked for purge`
- `CLI rejects room-session retention apply without an explicit updated-before cutoff`

### Wrapper / entrypoint coverage

- `/room skill wrapper can apply retention by archiving live sessions and purging archived saved files`
- skill documentation assertions now require:
  - `--apply-room-session-retention`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-apply-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-apply-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-apply-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-apply-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `169/169 pass`
- `0 fail`

## Net Effect

`/room` persistence now has a full explicit retention-policy v1 instead of only a preview layer:

1. Session 50 added preview-first retention inspection across live and archived saved sessions
2. Session 51 adds apply/execution for that same matched slice
3. the mainline still keeps cleanup semantics split and explicit: delete is catalog-only, purge is archive-first physical cleanup, repair is stale metadata cleanup, and preview surfaces remain read-only

The runtime mainline remains cumulative and narrow: save/resume, indexed catalog, discoverability, lifecycle state, delete/purge split, repair, cleanup-v1 filters, cleanup previews, retention preview, retention apply, and no rollback of the local/provider-safe runtime split.
