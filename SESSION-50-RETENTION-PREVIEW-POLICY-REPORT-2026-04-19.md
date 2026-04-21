# Session 50: Retention Preview Policy

Date: 2026-04-19

## Goal

Ship the smallest safe follow-up after Session 49's identity decoupling and cleanup previews:

1. add a preview-first explicit retention policy surface for saved room sessions
2. require an explicit age cutoff instead of introducing implicit whole-catalog cleanup
3. keep existing archive/delete/purge/repair semantics unchanged

## What Changed

### 1. Added a preview-first retention policy surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--preview-room-session-retention --room-session-catalog <room-session-catalog.json> --session-updated-before <iso-datetime>`
- Behavior:
  - retention preview scans the explicit session catalog with `includeArchived: true`
  - older live sessions are surfaced as `archive` candidates
  - older archived sessions with an existing saved session file are surfaced as `purge` candidates
  - older archived sessions whose saved session file is already missing are surfaced as `blocked_purge` candidates
  - the preview is read-only and never mutates the catalog or any saved session file

### 2. Retention preview reuses the existing filter surface

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
  - the same filter contract already used by catalog listing and archived batch cleanup now shapes retention preview
  - retention preview is explicit and narrow; it does not add an automatic retention daemon or a broader policy DSL

### 3. Retention preview requires an explicit cutoff

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Validation:
  - `--preview-room-session-retention` requires `--room-session-catalog`
  - `--preview-room-session-retention` also requires `--session-updated-before`
- Rationale:
  - this keeps retention preview from silently turning into a whole-catalog cleanup view
  - the command stays preview-first, age-scoped, and audit-friendly

## Scope Boundary

Implemented now:

- explicit preview-only retention policy surface
- explicit age-scoped retention preview contract
- archive / purge / blocked-purge split for matched saved sessions
- no rollback of save/resume, catalog, lifecycle, cleanup-v1, or Session 49 preview surfaces

Still out of scope:

- automatic retention execution or background cleanup
- broader retention DSLs or policy schedulers
- pagination / session browser UI
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can preview a room-session retention policy without mutating the catalog or files`
- `CLI rejects room-session retention preview without an explicit updated-before cutoff`

### Wrapper / entrypoint coverage

- `/room skill wrapper can preview a retention policy and keep catalog files untouched`
- skill documentation assertions now require:
  - `--preview-room-session-retention`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `165/165 pass`
- `0 fail`

## Net Effect

`/room` persistence now has an explicit retention-policy observation layer instead of only raw cleanup primitives:

1. Session 48 added cleanup-v1 filtering and archived batch purge
2. Session 49 added cleanup previews and decoupled saved-session identity
3. Session 50 adds preview-first retention policy inspection across live and archived saved sessions

The mainline stays cumulative and narrow: save/resume, indexed catalog, discoverability, lifecycle state, delete/purge split, repair, cleanup-v1 filters, preview-only cleanup inspection, identity decoupling, retention preview, and no rollback of the local/provider-safe runtime split.
