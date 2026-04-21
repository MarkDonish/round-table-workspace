# Round Table /room Takeover Readthrough

Date: 2026-04-16
Reader: Codex
Source folder: `D:\圆桌会议`
Runtime workspace: `C:\Users\CLH`

## Scope Read

- Current `D:\圆桌会议` file count: 47 files.
- Core files read: `NEXT-STEPS.md`, `DEVELOPMENT-BOARD-PRIORITY-PROGRESS-2026-04-16-CORRECTED.md`, `FULL-FOLDER-READTHROUGH-AND-MAINLINE-AUDIT-2026-04-16.md`, `DECISIONS-LOCKED.md`, `HANDOFF.md`, `PROJECT-STRUCTURE.md`, `SESSION-22-LOCAL-SUBAGENT-DISPATCH-CONTRACT-REPORT.md`, `SESSION-23-LOCAL-SEQUENTIAL-DISPATCH-RUNTIME-REPORT.md`.
- Code paths inspected: `C:\Users\CLH\tools\room-orchestrator-harness\src`, `C:\Users\CLH\tools\room-orchestrator-harness\test`, `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`, `C:\Users\CLH\agent-registry\registry.json`.

## Current Mainline

The corrected `/room` mainline is local skill / local Agent orchestration, not provider/API setup.

Correct runtime shape:

```text
user /room input
  -> room-skill orchestrator
  -> room-selection chooses speakers
  -> registry/profile resolves local agents
  -> room-chat.md builds speaker task contract
  -> local_sequential current-agent execution, or host subagent execution when explicitly supported
  -> orchestrator assembles Turn
  -> state reducer writes conversation_log
  -> summary / upgrade chain continues
```

Provider wrappers, env-file support, HTTP wrappers, Chat Completions wrappers, and external executors are optional harness/CI/dry-run adapters only. They must not block local `/room` runtime work and must not require user API keys.

## Latest Implemented State

Session 23 completed the local sequential dispatch runtime foundation.

Implemented:

- `src/local-dispatch.js`
- `test/local-dispatch.test.js`
- `runDryRunWithLocalDispatch()` in `src/dry-run.js`
- local dispatch dry-run integration test
- README scope correction: provider wrappers are optional, not the `/room` mainline

Current test baseline:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

Observed result on 2026-04-16:

```text
tests 57
pass 57
fail 0
```

## Next Development Step

Start at P1:

```text
host/current-agent speaker executor adapter
```

Required behavior:

- Input: `room_speaker_task`.
- Read local profile, room context, turn role, recent log, and user input.
- Generate one speaker content fragment in current-agent local sequential mode.
- Return:
  - `content: non-empty string`
  - `cited_agents: []`
  - `warnings: []`
  - optional `status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`
- Speaker task must not write `room_state`.
- Only orchestrator assembles Turn and writes `conversation_log`.

Tests to add next:

- executor normal output
- single speaker `BLOCKED`
- warnings aggregation
- executor exception does not destroy diagnostics for other speakers

## Hard Constraints

- Do not modify `/debate` behavior or boundaries.
- Do not use provider/API setup as the product mainline.
- Do not treat `room-chat.md` as the only intelligence source; it is a task contract/template.
- Do not call Codex `spawn_agent` unless the user explicitly authorizes subagents. Continue with `local_sequential` by default.
- Do not start UI, persistent room storage, full command parser, Phase 6 skill mode upgrades, or Phase 7 scanner yet.
- Continue TDD for behavior changes: RED, GREEN, full regression.

## Practical Entry Points

- Main implementation target: `C:\Users\CLH\tools\room-orchestrator-harness\src\local-dispatch.js`
- Current seam: `runLocalSequentialChatTurn(chatInput, speakerExecutor, options)`
- Current task builder: `buildLocalSpeakerTask(chatInput, speaker, resolvedSpeaker, options)`
- Current validation: `validateChatTurnOutput()`
- Integration path: `runDryRunWithLocalDispatch()`

## Notes

`C:\Users\CLH` has a noisy root git state with many untracked files and permission warnings. Do not use root `git status` as a clean project signal. Work from exact paths and test results.

