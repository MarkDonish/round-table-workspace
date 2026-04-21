# Session 59: Stable Session Created-At And Created Sort

Date: 2026-04-21

## Goal

Ship the next smallest stronger-navigation slice after Session 58 name-invariant hardening:

1. add stable `created_at` metadata to saved room sessions and catalog entries
2. preserve that first-persisted timestamp across resume and rename/writeback flows
3. expose `--session-sort created` on the existing catalog selector surface

## What Changed

### 1. Added stable `created_at` metadata to saved room sessions

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- Behavior:
  - new saved sessions now get `created_at` when the session file is first built
  - resumed sessions preserve the original `created_at` instead of drifting with later writebacks
  - same-session catalog upserts preserve the first-known `created_at`, including older catalogs that may already have it even if the session file does not

### 2. Added catalog-level `created` sorting

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Behavior:
  - `--session-sort created` is now supported anywhere the existing selector surface accepts `--session-sort`
  - this includes `--list-room-sessions` and the existing paged batch lifecycle / cleanup / retention flows because they already reuse the same selector contract
  - default sorting remains `updated`, so no existing command flow changes behavior unless the operator opts in

### 3. Kept created order distinct from updated order

- Semantics:
  - `created_at` tracks when a session first entered explicit persistence
  - `updated_at` continues to track the latest catalog mutation/writeback
  - operators can now choose between “what was created first” and “what changed most recently” without rewriting the catalog model

## Scope Boundary

Implemented now:

- stable `created_at` metadata in session files and catalog entries
- `--session-sort created` on the existing selector surface
- created-at stability across resume/writeback flows

Still out of scope:

- `created_before` / `created_after` filters
- separate retention policy based on `created_at`
- cursor pagination
- UI session browser

## New Coverage Added

### CLI regression coverage

- `CLI fresh saved room sessions get a session_id distinct from room_state.room_id and preserve it on resume`
  - now also verifies stable `created_at` in both the session file and catalog
- `CLI list-room-sessions can sort by created timestamp ascending`

### Wrapper / entrypoint coverage

- `/room skill wrapper can sort room sessions by created timestamp ascending`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-identity-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-sorting-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-sorting-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-identity-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-sorting-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-sorting-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `194/194 pass`
- `0 fail`

## Net Effect

`/room` session catalogs now have a cleaner navigation model:

1. each saved session keeps a stable first-persisted timestamp
2. resume/writeback no longer blur “when this started” with “when this last changed”
3. operators can page and scan catalogs by `created` order without disturbing any existing `updated`-based workflow
