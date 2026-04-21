# Session 53: Bulk Room Session Lifecycle Toggles

Date: 2026-04-19

## Goal

Ship the next smallest safe follow-up after Session 52 pagination v1:

1. add batch archive for the currently listed live catalog slice
2. add batch unarchive for the currently listed archived catalog slice
3. keep the existing selector contract, pagination semantics, and lifecycle safety boundaries unchanged

## What Changed

### 1. Added batch archive / unarchive commands for paged catalog slices

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flags:
  - `--archive-room-sessions`
  - `--unarchive-room-sessions`
- Behavior:
  - `--archive-room-sessions` targets only the currently selected live slice
  - `--unarchive-room-sessions` targets only the currently selected archived slice
  - both commands update the matched catalog entries in place and return the updated slice in CLI output

### 2. Reused the existing selector and pagination contract

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Reused filters:
  - `--session-search`
  - `--session-status`
  - `--session-sort`
  - `--session-order`
  - `--session-limit`
  - `--session-offset`
  - `--session-updated-before`
- Shared output metadata:
  - `total_matching`
  - `offset`
  - `has_more`
  - `next_offset`

### 3. Preserved lifecycle boundaries instead of widening cleanup semantics

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Safety boundary:
  - batch archive only flips lifecycle state for matched live entries
  - batch unarchive only flips lifecycle state for matched archived entries
  - no saved `room-session.json` file is deleted by these commands
  - Session 44 delete, Session 45 purge, Session 46 repair, Session 47 batch delete, Session 48 batch purge, Session 50 retention preview, Session 51 retention apply, and Session 52 pagination semantics remain unchanged

## Scope Boundary

Implemented now:

- batch archive for the current live slice
- batch unarchive for the current archived slice
- reuse of the existing list/search/sort/limit/offset selector surface
- no rollback of single-session lifecycle commands, cleanup flows, retention flows, or pagination v1

Still out of scope:

- preview variants for batch archive / unarchive
- automatic lifecycle policy scheduling
- UI session browser
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can bulk-archive a live catalog slice starting from --session-offset`
- `CLI can bulk-unarchive an archived catalog slice starting from --session-offset`

### Wrapper / entrypoint coverage

- `/room skill wrapper can bulk-archive and bulk-unarchive catalog slices through the harness CLI`
- skill documentation assertions now require:
  - `--archive-room-sessions`
  - `--unarchive-room-sessions`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `175/175 pass`
- `0 fail`

## Net Effect

`/room` persistence now has a symmetric batch lifecycle toggle that fits the existing CLI-first mainline:

1. operators can page through a catalog and archive one live slice at a time
2. archived slices can be restored in the same paged, explicit way
3. lifecycle mutation stays aligned with the same selector surface already used by listing, cleanup, and retention, without adding UI or a new batch-management DSL
