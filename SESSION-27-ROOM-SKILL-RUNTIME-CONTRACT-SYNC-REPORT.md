# Session 27: Room Skill Runtime Contract Sync Report

Date: 2026-04-16
Workspace: `C:\Users\CLH\tools\room-orchestrator-harness`
Skill file: `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

## Goal

Continue P4 by syncing the executable local runtime contract back into `room-skill`, so `/room` instructions do not remain purely abstract after `runRoomTurnWithLocalDispatch()` and `--room-turn-fixture` became available.

## Files Changed

- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`

## Implemented

### room-skill contract sync

Added a `可执行 harness 契约（Session 26）` section to `room-skill/SKILL.md` documenting:

- `C:\Users\CLH\tools\room-orchestrator-harness\src\room-runtime.js`
- `runRoomTurnWithLocalDispatch(options)`
- CLI `--room-turn-fixture`
- `D:\圆桌会议\SESSION-25-ROOM-TURN-LOCAL-RUNTIME-FIXTURE.json`
- the local execution chain:

```text
roomState + userInput + selectedSpeakers + speakerExecutor
  -> buildChatInput()
  -> runLocalSequentialChatTurn()
  -> applyChatTurn()
  -> final_state
```

The section explicitly says this is not a full `/room` parser and not real selection prompt execution.

### contract regression test

Extended `room-skill-local-dispatch-contract.test.js` so it fails if `room-skill` stops mentioning:

- `runRoomTurnWithLocalDispatch`
- `--room-turn-fixture`
- `SESSION-25-ROOM-TURN-LOCAL-RUNTIME-FIXTURE`

### CLI output compacting

Added CLI compaction for `--room-turn-fixture` output:

- strips full `room_chat_contract`
- strips `profile_text`
- preserves mode, validation, speakers, statuses, warnings, final state, and task metadata

This keeps CLI output useful without dumping the full `room-chat.md` prompt and roundtable profiles.

## TDD Evidence

RED:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js'
```

Observed failure:

```text
The input did not match the regular expression /runRoomTurnWithLocalDispatch/
```

GREEN:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js'
```

Result:

```text
tests 1
pass 1
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

## Current State

P4 now has both:

1. executable harness/runtime code, and
2. `room-skill` documentation pointing to that executable contract.

Remaining local-mainline gap:

- no stable selection-output-to-runtime fixture yet.
- full `/room` command parsing is still intentionally out of scope.

## Next Recommended Priority

1. Add a selection-output-to-runtime fixture once selection output is stable enough.
2. Then process low-priority protocol debts F11/F16/F17/F18 + selection §13.6.
3. Keep provider/API work optional, not mainline.
