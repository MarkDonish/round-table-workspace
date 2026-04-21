# Session 47: Bulk Archived Room Session Delete

Date: 2026-04-19

## Goal

Take the next smallest batch-management slice after Session 46's stale-catalog repair:

1. add a safe batch cleanup path for archived catalog entries
2. keep single-session delete / purge semantics unchanged
3. reuse the existing search/sort/limit filter surface instead of adding a new retention language

## What Changed

### 1. Added batch catalog-only cleanup for archived room sessions

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--delete-archived-room-sessions --room-session-catalog <room-session-catalog.json>`
- Behavior:
  - batch delete scans only the archived slice of the explicit catalog
  - batch delete applies the existing `--session-search`, `--session-status`, `--session-sort`, `--session-order`, and `--session-limit` filters
  - batch delete removes the matched archived entries from the catalog in one batch
  - batch delete preserves every saved `room-session.json` file on disk

### 2. Batch delete is intentionally safer than batch purge

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Behavior:
  - single-session `--delete-room-session` still removes exactly one archived catalog entry
  - single-session `--purge-room-session` still handles archive-first physical deletion
  - new batch delete does not widen physical deletion semantics
  - no new retention date language or auto-cleanup policy was introduced in this slice

### 3. Wrapper / skill docs were updated to reflect the batch delete surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
  - `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
  - `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- Corrections:
  - README now documents `--delete-archived-room-sessions`
  - README now distinguishes single archived delete from batch archived delete
  - room skill docs now include Session 47's batch delete semantics
  - wrapper documentation assertions now require `--delete-archived-room-sessions`

## Scope Boundary

Implemented now:

- explicit batch delete for archived catalog entries
- reuse of existing catalog search / status / sort / order / limit filters
- guaranteed preservation of saved session files during batch delete
- no rollback of Session 44 delete, Session 45 purge, or Session 46 repair behavior

Still out of scope:

- batch purge of saved session files
- retention windows / age-based cleanup rules
- automatic repair or automatic cleanup policies
- UI session browser / larger persistence rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can bulk-delete archived room sessions from the catalog while preserving saved session files`
- `CLI bulk archived room-session delete is a no-op when no archived sessions match the filters`

### Wrapper / entrypoint coverage

- `/room skill wrapper can bulk-delete archived catalog sessions while preserving the saved session files`
- skill documentation assertions now require:
  - `--delete-archived-room-sessions`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-delete-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-delete-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-delete-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-delete-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `154/154 pass`
- `0 fail`

## Net Effect

`/room` persistence now has a safer first batch-management rung before any future batch purge or retention logic:

1. Session 44 added single archived catalog delete
2. Session 45 added single archive-first purge
3. Session 46 added stale-catalog repair
4. Session 47 adds batch archived catalog delete with reusable filters

The mainline stays cumulative and narrow: save/resume, indexed catalog, discoverability, lifecycle state, single delete, single purge, repair, batch archived delete, and no rollback of the local/provider-safe runtime split.
