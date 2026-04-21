# Session 49: Session Id Decoupling And Cleanup Preview

Date: 2026-04-19

## Goal

Ship the smallest safe follow-up after Session 48's cleanup-v1 slice:

1. decouple fresh saved `session_id` values from deterministic raw-room `room_id`
2. add read-only preview surfaces for archived batch delete and archived batch purge
3. keep existing resume, catalog, delete, purge, and provider/local runtime semantics unchanged

## What Changed

### 1. Fresh saved room sessions now get an independent stable `session_id`

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- Behavior:
  - fresh saved sessions now generate `session_id` values as `room-session-<uuid>`
  - resumed sessions still preserve their existing `session_id`
  - `room_state.room_id` remains unchanged and can stay deterministic for raw `/room` bootstrap
  - catalog identity is no longer coupled to deterministic fresh room ids

### 2. Added preview-only archived batch delete

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--preview-delete-archived-room-sessions --room-session-catalog <room-session-catalog.json>`
- Behavior:
  - preview delete reuses the existing archived batch filter surface
  - preview delete returns the matched archived catalog entries
  - preview delete never mutates the catalog
  - preview delete never deletes any saved `room-session.json` file

### 3. Added preview-only archived batch purge with blocker visibility

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--preview-purge-archived-room-sessions --room-session-catalog <room-session-catalog.json>`
- Behavior:
  - preview purge reuses the archived batch filter surface
  - preview purge shows matched archived catalog entries
  - preview purge surfaces blocked candidates whose saved session file is missing
  - preview purge returns warnings and blocked-session counts without mutating the catalog or files

## Scope Boundary

Implemented now:

- fresh saved-session identity decoupling from deterministic raw-room ids
- explicit preview surfaces for archived batch delete and archived batch purge
- preview visibility into missing-file blockers for batch purge
- no rollback of existing save/resume, catalog, lifecycle, or runtime surfaces

Still out of scope:

- automatic retention windows or background cleanup
- larger retention DSLs or policy engines
- pagination / session browser UI
- larger persistence architecture rewrites

## New Coverage Added

### CLI regression coverage

- `CLI fresh saved room sessions get a session_id distinct from room_state.room_id and preserve it on resume`
- `CLI can preview archived room-session delete matches without mutating the catalog or files`
- `CLI can preview archived room-session purge matches and surface missing session files without mutating the catalog`

### Wrapper / entrypoint coverage

- `/room skill wrapper can preview archived batch delete and keep catalog files untouched`
- skill documentation assertions now require:
  - `--preview-delete-archived-room-sessions`
  - `--preview-purge-archived-room-sessions`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-identity-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-cleanup-preview-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-cleanup-preview-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-identity-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-cleanup-preview-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-cleanup-preview-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `162/162 pass`
- `0 fail`

## Net Effect

`/room` persistence is now much less brittle for the finishing stretch:

1. Session 48 added explicit cleanup-v1 filtering and archived batch purge
2. Session 49 decouples catalog `session_id` from deterministic raw-room `room_id`
3. Session 49 adds preview-only archived delete/purge surfaces so batch cleanup can be inspected before mutation

The mainline stays cumulative and narrow: save/resume, indexed catalog, discoverability, lifecycle state, delete/purge split, repair, cleanup-v1 filters, batch purge, identity decoupling, preview-only cleanup inspection, and no rollback of the local/provider-safe runtime split.
