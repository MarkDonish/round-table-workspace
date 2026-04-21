# Session 60: Session Created-Before Filter

Date: 2026-04-21

## Goal

Ship the next smallest stronger-navigation slice after Session 59 created metadata:

1. add `--session-created-before <iso-datetime>` to the existing catalog selector surface
2. keep that cutoff based on stable `created_at`, not `updated_at`
3. propagate the same filter through list, batch lifecycle, archived cleanup, and retention flows without creating a parallel selector DSL

## What Changed

### 1. Added created-before filtering to the shared room-session selector

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- Behavior:
  - catalog listing now supports filtering sessions whose `created_at` is strictly older than an explicit cutoff
  - the filter is evaluated against stable first-persisted metadata instead of last-write metadata
  - selector reuse means the same cutoff now works across live-slice lifecycle actions, archived cleanup, and retention flows

### 2. Exposed `--session-created-before` on the CLI surface

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Behavior:
  - `parseArgs` now accepts `--session-created-before <iso-datetime>`
  - CLI validation normalizes and rejects invalid created-before timestamps explicitly
  - selector-backed outputs now surface `session_created_before` inside the returned `filters` payload
  - help text / usage lines now document created-before anywhere the shared selector contract is available

### 3. Kept created-before distinct from updated-before

- Semantics:
  - `--session-created-before` matches on stable `created_at`
  - `--session-updated-before` continues to match on mutable `updated_at`
  - retention still requires explicit `--session-updated-before` for its age policy, but can now be narrowed further by `--session-created-before`

## Scope Boundary

Implemented now:

- `--session-created-before` on the catalog selector surface
- propagation through list / batch lifecycle / archived cleanup / retention
- wrapper coverage through the room skill entrypoint

Still out of scope:

- `--session-created-after`
- separate retention policy keyed only on `created_at`
- cursor pagination
- UI session browser

## New Coverage Added

### CLI regression coverage

- `CLI list-room-sessions can filter catalog entries by --session-created-before`
- `CLI retention preview can further filter matched sessions by --session-created-before`

### Wrapper / entrypoint coverage

- `/room skill wrapper can filter room sessions by created timestamp before a cutoff`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-session-store.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-updated-before-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-created-before-wrapper.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`
- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Verification

Targeted verification:

- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-updated-before-cli.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-created-before-wrapper.test.js"`
- `node --test "C:\Users\CLH\tools\room-orchestrator-harness\test\room-session-retention-preview-cli.test.js"`

Full verification:

- `node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'`

Result:

- `197/197 pass`
- `0 fail`

## Net Effect

`/room` catalog navigation now distinguishes two explicit time filters cleanly:

1. `created_at` answers “when did this session first enter explicit persistence?”
2. `updated_at` answers “when did this catalog entry last change?”
3. operators can now filter and sort on the created-time axis without weakening any existing updated-time workflow
