# Session 45: Room Session Archive-First Purge

Date: 2026-04-19

## Goal

Take the next smallest lifecycle slice after Session 44's catalog-only delete:

1. add a physical purge path for saved room sessions
2. keep Session 44 delete semantics unchanged
3. make purge strict enough that it cannot half-complete silently

## What Changed

### 1. Added explicit archive-first purge for saved room sessions

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New CLI flag:
  - `--purge-room-session <session-id|room-session.json>`
- Behavior:
  - purge resolves the target from the explicit catalog by `session_id` or saved session path
  - purge deletes the saved `room-session.json` from disk
  - purge removes the same archived entry from the catalog
  - purge returns `session_file_deleted: true` on success

### 2. Purge is intentionally stricter than delete

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Behavior:
  - `--delete-room-session` remains catalog-only and preserves the saved session file
  - `--purge-room-session` requires the target to already be archived
  - live catalog sessions cannot be purged directly
  - the lifecycle command surface is still mutually exclusive: archive / unarchive / delete / purge

### 3. Purge now rejects missing-file half-completion

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Behavior:
  - if the archived catalog entry points at a session file that is already missing, purge fails
  - the catalog stays unchanged in that case
  - this keeps physical cleanup auditable and avoids silently drifting the lifecycle boundary

### 4. Wrapper / skill docs were updated to reflect the purge surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
  - `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
  - `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- Corrections:
  - README now documents `--purge-room-session`
  - README now distinguishes catalog-only delete from physical purge
  - room skill docs now include Session 45's purge semantics
  - wrapper documentation assertions now require `--purge-room-session`

## Scope Boundary

Implemented now:

- explicit physical purge surface
- archive-first purge guardrail
- missing-file purge rejection
- delete vs purge lifecycle split

Still out of scope:

- bulk purge across many sessions
- cleanup policies / retention windows
- stale catalog auto-repair
- UI session browser / larger persistence rewrites

## New Coverage Added

### CLI regression coverage

- `CLI can purge an archived room session from the catalog and delete the saved session file`
- `CLI rejects purging a live room session before it is archived`
- `CLI rejects purging an archived room session when the saved session file is already missing`

### Wrapper / entrypoint coverage

- `/room skill wrapper can purge an archived catalog session and remove the saved session file`
- skill documentation assertions now require:
  - `--purge-room-session`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-cli.test.js" "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-purge-wrapper.test.js" "C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `148/148 pass`
- `0 fail`

## Net Effect

`/room` persistence now has a clear two-step cleanup ladder:

1. Session 44 added catalog-only delete for archived sessions
2. Session 45 adds strict archive-first purge for physically removing saved session files

The mainline stays explicit and cumulative: save/resume, indexed catalog, discoverability, lifecycle state, catalog-only delete, archive-first purge, and no rollback of the local/provider-safe runtime split.
