# Session 54: Preview Batch Room Session Lifecycle

Date: 2026-04-19

## Goal

Ship the next smallest safe follow-up after Session 53 batch lifecycle toggles:

1. add preview-only batch archive for the currently listed live catalog slice
2. add preview-only batch unarchive for the currently listed archived catalog slice
3. keep the selector contract, pagination semantics, and lifecycle mutation boundaries unchanged

## What Changed

### 1. Added preview-only batch lifecycle commands

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flags:
  - `--preview-archive-room-sessions`
  - `--preview-unarchive-room-sessions`
- Behavior:
  - `--preview-archive-room-sessions` targets only the currently selected live slice
  - `--preview-unarchive-room-sessions` targets only the currently selected archived slice
  - both commands return the would-be lifecycle result for the matched slice without mutating the catalog

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

### 3. Kept preview semantics read-only and aligned with the existing cleanup surfaces

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Safety boundary:
  - preview batch archive/unarchive never writes catalog state
  - preview outputs show the would-be lifecycle result for the selected slice
  - Session 44 delete, Session 45 purge, Session 46 repair, Session 47 batch delete, Session 48 batch purge, Session 50 retention preview, Session 51 retention apply, Session 52 pagination, and Session 53 batch lifecycle toggles remain unchanged

## Scope Boundary

Implemented now:

- preview-only batch archive for the current live slice
- preview-only batch unarchive for the current archived slice
- reuse of the existing list/search/sort/limit/offset selector surface
- no rollback of existing lifecycle, cleanup, retention, or pagination semantics

Still out of scope:

- automatic lifecycle policy scheduling
- cursor-based pagination
- UI session browser
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can preview bulk-archive for a live catalog slice without mutating the catalog`
- `CLI can preview bulk-unarchive for an archived catalog slice without mutating the catalog`

### Wrapper / entrypoint coverage

- `/room skill wrapper can preview bulk-archive and bulk-unarchive catalog slices without mutating the catalog`
- skill documentation assertions now require:
  - `--preview-archive-room-sessions`
  - `--preview-unarchive-room-sessions`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-preview-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-preview-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-preview-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-bulk-lifecycle-preview-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `178/178 pass`
- `0 fail`

## Net Effect

`/room` persistence now has preview-first batch lifecycle ergonomics that match the rest of the CLI-first mainline:

1. operators can inspect a paged live slice before batch archiving it
2. operators can inspect a paged archived slice before batch unarchiving it
3. lifecycle preview now lines up with the existing preview surfaces for delete, purge, and retention without introducing UI or a separate management DSL
