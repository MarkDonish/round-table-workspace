# Session 48: Batch Archived Purge And Updated-Before Filter

Date: 2026-04-19

## Goal

Ship the first explicit cleanup-v1 slice after Session 47's batch archived catalog delete:

1. add a shared explicit age filter for catalog listing and batch cleanup flows
2. add a batch archive-first physical purge path for archived sessions
3. keep single delete / single purge semantics unchanged

## What Changed

### 1. Added an explicit updated-before filter for cataloged room sessions

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--session-updated-before <iso-datetime>`
- Behavior:
  - `--list-room-sessions` now accepts `--session-updated-before`
  - the cutoff is explicit and matches sessions whose `updated_at` is strictly older than the provided timestamp
  - the same filter composes with existing `--session-search`, `--session-status`, `--session-sort`, `--session-order`, and `--session-limit`
  - this is a filter surface, not an automatic retention policy

### 2. Added batch archive-first physical purge for archived room sessions

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--purge-archived-room-sessions --room-session-catalog <room-session-catalog.json>`
- Behavior:
  - batch purge targets the archived slice only
  - batch purge reuses `--session-search`, `--session-status`, `--session-sort`, `--session-order`, `--session-limit`, and `--session-updated-before`
  - batch purge preflights every matched saved session file before mutation
  - if any matched file is missing, the command fails before deleting any catalog entry or any other saved session file
  - once preflight succeeds, batch purge deletes both the matched archived catalog entries and their `room-session.json` files

### 3. Single-session cleanup boundaries remain unchanged

- `--delete-room-session` remains catalog-only
- `--delete-archived-room-sessions` remains batch catalog-only
- `--purge-room-session` remains single-session archive-first physical cleanup
- `--repair-room-session-catalog` remains stale-metadata-only cleanup

## Scope Boundary

Implemented now:

- explicit `--session-updated-before` filter for catalog listing and archived batch cleanup
- explicit `--purge-archived-room-sessions` batch physical cleanup path
- archive-first preflight semantics for batch purge
- no rollback of local/provider runtime split or existing parser / persistence surfaces

Still out of scope:

- automatic retention windows or background cleanup
- session identity decoupling from deterministic fresh room ids
- richer pagination / session browser UI
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can bulk-purge archived room sessions from the catalog and delete the saved session files`
- `CLI bulk archived room-session purge aborts before mutation when a matched saved session file is missing`
- `CLI list-room-sessions can filter catalog entries by --session-updated-before`

### Wrapper / entrypoint coverage

- `/room skill wrapper can bulk-purge archived catalog sessions and delete the saved session files`
- skill documentation assertions now require:
  - `--session-updated-before`
  - `--purge-archived-room-sessions`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-purge-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-purge-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-updated-before-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-purge-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-purge-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-updated-before-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `158/158 pass`
- `0 fail`

## Net Effect

`/room` persistence now has a usable cleanup v1 instead of only fragmented lifecycle primitives:

1. Session 47 added batch archived catalog delete
2. Session 48 adds explicit age filtering via `--session-updated-before`
3. Session 48 adds batch archived physical purge with archive-first preflight semantics

The mainline stays cumulative and narrow: save/resume, indexed catalog, discoverability, lifecycle state, single delete, single purge, repair, batch archived delete, batch archived purge, and no rollback of the local/provider-safe runtime split.
