# Session 26: Local Room-Turn CLI Fixture Report

Date: 2026-04-16
Workspace: `C:\Users\CLH\tools\room-orchestrator-harness`
Handoff directory: `D:\圆桌会议`

## Goal

Continue the corrected local `/room` mainline after the current-agent executor and room runtime adapter:

```text
room_state + selected_speakers + user_input fixture
  -> CLI
  -> deterministic current-agent speaker outputs
  -> runRoomTurnWithLocalDispatch()
  -> state reducer
```

This creates a runnable local room-turn fixture path without provider/API configuration and without pretending that the full `/room` command parser exists.

## Files Added

- `D:\圆桌会议\SESSION-25-ROOM-TURN-LOCAL-RUNTIME-FIXTURE.json`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-runtime.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-runtime.js`

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\dry-run.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## Implemented

### Local room-turn fixture

Added `SESSION-25-ROOM-TURN-LOCAL-RUNTIME-FIXTURE.json` with:

- `initial_room_state`
- `user_input`
- `stage`
- `selected_speakers`
- deterministic `speaker_outputs`

The fixture intentionally uses no provider settings.

### CLI entrypoint

Added:

```powershell
node C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js --room-turn-fixture D:\圆桌会议\SESSION-25-ROOM-TURN-LOCAL-RUNTIME-FIXTURE.json
```

The CLI path:

1. Reads the room-turn fixture.
2. Builds a deterministic current-agent speaker executor from `speaker_outputs`.
3. Calls `runRoomTurnWithLocalDispatch()`.
4. Prints JSON output.
5. Exits non-zero only if local runtime validation fails.

### Tests

Added CLI coverage that clears provider env vars and verifies:

- `mode = room_turn_local_runtime`
- `execution_mode = local_sequential`
- `pass = true`
- turn roles are assigned by the orchestrator
- `DONE_WITH_CONCERNS` and `BLOCKED` speaker statuses survive
- warnings survive aggregation

## TDD Evidence

RED:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js'
```

Observed failure:

```text
unknown argument: --room-turn-fixture
```

GREEN:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js'
```

Result:

```text
tests 10
pass 10
fail 0
```

Full regression:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

Result:

```text
tests 65
pass 65
fail 0
```

## Current Mainline State

Completed local-mainline slices:

1. P0 local sequential dispatch foundation.
2. P1 current-agent speaker executor adapter.
3. P2/P3 current-agent diagnostics through local dry-run and state reduction.
4. P4 slice: runtime-facing local room-turn adapter.
5. Session 26: CLI fixture path for one local room turn.

Still not implemented:

- Full `/room` command parser.
- Actual selection prompt execution in CLI/runtime.
- Real host subagent spawning.
- Persistent storage.
- UI.

## Next Recommended Priority

P4 continuation:

1. Update `room-skill` instructions/tests to name `runRoomTurnWithLocalDispatch()` as the executable harness contract for Flow E local runtime.
2. Add a selection-output-to-runtime fixture once a stable selection output fixture exists.
3. Then move to low-priority protocol debts F11/F16/F17/F18 + selection §13.6.

Do not resume provider/API work as a mainline prerequisite.
