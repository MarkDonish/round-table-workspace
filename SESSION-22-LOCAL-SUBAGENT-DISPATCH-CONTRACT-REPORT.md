# SESSION 22 - Local Subagent Dispatch Contract Correction

Date: 2026-04-16

## Context

User clarified the core architecture: `/room` and `/debate` are local skill / local Agent workflows. The mainline must follow the local `gstack` workflow skill pattern, not require a real provider API.

## Technical Decision

Provider / external executor support remains an optional harness, CI, and dry-run adapter only.
It is not the `/room` runtime mainline and must not be required before local `/room` can run.

Mainline correction:

1. `/room` skill is the orchestrator, similar to gstack workflow skills.
2. `room-selection.md` selects speakers and stage only.
3. `room-chat.md` is a speaker task prompt/template, not a replacement for local Agent execution.
4. Each selected speaker must be executed through local Agent / local skill context.
5. Claude-like runtimes may express this with `Task(...)`.
6. Codex-like runtimes may express this with `spawn_agent(...)`, or degrade to `execution_mode: local_sequential` when parallel subagents are not available.
7. The room skill remains the only state writer.

## Files Changed

- `C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
  - Added `本地 Agent 调用契约（参考 gstack）`.
  - Reframed prompts as contracts/templates rather than the intelligence source.
  - Clarified provider/external executor is not the `/room` mainline dependency.
  - Updated Flow E to call room-chat speaker tasks through the local Agent contract.

- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js`
  - Added a contract test that prevents future drift back to provider-first architecture.

## TDD Evidence

Red test:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js'
```

Initial result: failed on missing `本地 Agent 调用契约`.

Green test:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-local-dispatch-contract.test.js'
```

Result: 1 test passed, 0 failed.

Full regression:

```powershell
node --test 'C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js'
```

Result: 52 tests passed, 0 failed.

## Updated Priority

P0 is now corrected to:

`/room` local subagent / local skill dispatch contract and runtime implementation.

Provider config / env-file work is reclassified as optional harness infrastructure, not product mainline.

## Next Development Step

Implement an executable local dispatch layer that turns the markdown contract into runtime behavior:

1. Resolve selected speaker to local skill/profile path.
2. Build per-speaker prompt from `room-chat.md` + room state.
3. Execute each speaker through local sequential mode first.
4. Add optional parallel subagent mode only where the host runtime explicitly supports it.
5. Add tests for `local_sequential` turn assembly and warnings.
