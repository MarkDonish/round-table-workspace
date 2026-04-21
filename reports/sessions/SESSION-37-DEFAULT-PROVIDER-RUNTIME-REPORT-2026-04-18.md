# Session 37: Default Provider-Backed `/room` Command-Flow Runtime

Date: 2026-04-18

## Goal

Promote provider-backed execution from an explicit `--prompt-executor`-only path into the default `/room` command-flow runtime when chat-completions provider config is present, while preserving an explicit local fallback for regression and debugging.

## What Changed

### 1. `--command-flow-fixture` now auto-defaults to provider-backed when provider config is ready

- File: `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- Added CLI-side runtime resolution for command-flow:
  - `--execution-mode` override wins first
  - fixture `execution_mode` wins second
  - explicit `--prompt-executor` still promotes provider-backed execution
  - otherwise, configured `ROOM_CHAT_COMPLETIONS_URL` + `ROOM_CHAT_COMPLETIONS_MODEL` now auto-select the built-in `chat-completions-wrapper.js`
  - if none of the above apply, command-flow stays on `local_sequential`

### 2. Added an explicit local fallback

- File: `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- New flag:
  - `--execution-mode local_sequential`
  - `--execution-mode provider_backed`
- This lets us force the old local runtime even when:
  - provider env is configured
  - or a fixture defaults to `provider_backed`

### 3. Kept explicit executor bridging intact

- Existing `--prompt-executor` support remains unchanged.
- `provider_backed` command-flow can still be driven by any external executor command, not only by the built-in chat-completions wrapper.

### 4. Test suite now isolates local command-flow coverage from ambient provider env

- Files:
  - `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
  - `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- Local command-flow tests now clear provider env explicitly so future machine-level provider config will not silently flip local regressions into provider-backed runs.

## New Coverage Added

### CLI regression coverage

- `CLI can force local_sequential command-flow even when the fixture requests provider_backed`
- `CLI command-flow auto-defaults to chat-completions-wrapper when provider config is ready`

### Existing coverage preserved

- raw `/room` bootstrap
- multi-turn command-flow
- full parser command surface
- provider-backed explicit executor bridge
- skill-side wrapper bridge

## Files Changed

- `C:\Users\CLH\tools\room-orchestrator-harness\src\cli.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-cli.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`
- `C:\Users\CLH\tools\room-orchestrator-harness\README.md`

## Backup / Rollback

- Backup root:
  - `C:\Users\CLH\tmp\room-default-provider-runtime-20260418\backup-originals`

## Verification

Targeted verification:

- `node --test C:\Users\CLH\tools\room-orchestrator-harness\test\cli.test.js`
- `node --test C:\Users\CLH\tools\room-orchestrator-harness\test\chat-completions-cli.test.js`
- `node --test C:\Users\CLH\tools\room-orchestrator-harness\test\room-skill-entrypoint.test.js`

Full verification:

- `node --test C:\Users\CLH\tools\room-orchestrator-harness\test\*.test.js`

Result:

- `116/116 pass`
- `0 fail`

## Net Effect

The `/room` command-flow runtime is now effectively:

1. auto-provider-backed when provider config exists
2. still explicitly forceable to local
3. still compatible with custom external executors

This moves provider-backed execution from an optional side path toward the practical default runtime, without deleting the existing local regression-safe path.
