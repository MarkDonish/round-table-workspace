# OpenCode Host-Live Attempt - 2026-04-28

This is a historical report. It records the OpenCode host-live attempt from this Mac and is not the source of truth for implementation behavior. Current source-of-truth entry points remain `README.md`, `docs/`, `prompts/`, `examples/`, and `.codex/skills/`.

## Scope

- Host lane: OpenCode local CLI.
- Runtime lane: generic local-agent adapter for `/room -> /debate`.
- Launch impact: does not block the Codex local mainline.
- Claim boundary: OpenCode is not claimable as host-live support from this attempt.

## Completed

- Added `.codex/skills/room-skill/runtime/opencode_agent_wrapper.py` as the checked-in OpenCode non-interactive wrapper.
- Registered the wrapper in `.codex/skills/room-skill/runtime/agent_host_inventory.py`.
- Added the wrapper to `.codex/skills/room-skill/runtime/release_readiness_check.py` required runtime files.
- Updated runtime/docs recipes so OpenCode uses the checked-in wrapper through `generic_agent_json_wrapper.py`.
- Hardened `room-upgrade` handling so `handoff_packet.generated_at_turn` can only be normalized from placeholder `0` or `None` when the prompt input and sibling metadata agree on the same positive turn.

## Validation

Passed:

```bash
PYTHONPYCACHEPREFIX=/tmp/round-table-pycache python3 -m py_compile \
  .codex/skills/room-skill/runtime/opencode_agent_wrapper.py \
  .codex/skills/room-skill/runtime/local_codex_executor.py \
  .codex/skills/room-skill/runtime/agent_host_inventory.py \
  .codex/skills/room-skill/runtime/release_readiness_check.py
```

```bash
python3 .codex/skills/room-skill/runtime/opencode_agent_wrapper.py --help
```

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py --timeout-seconds 30
```

```bash
python3 .codex/skills/room-skill/runtime/host_recipes_consistency_check.py \
  --output-json /tmp/round-table-host-recipes-consistency.json
```

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical \
  --state-root /tmp/round-table-canonical-validation
```

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-e2e-fixture-validation
```

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-debate-fixture-validation
```

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py \
  --output-json /tmp/round-table-generic-agent-json-wrapper-validation.json
```

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --output-json /tmp/round-table-release-readiness.json
```

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --skip-host 'gemini_cli=not installed on this Mac; not claimed' \
  --skip-host 'aider=not installed on this Mac; not claimed' \
  --skip-host 'goose=not installed on this Mac; not claimed' \
  --skip-host 'cursor_agent=not installed on this Mac; not claimed' \
  --state-root /tmp/round-table-live-lane-evidence-opencode-current
```

Focused normalization check passed against the prior OpenCode output that copied a `generated_at_turn: 0` placeholder:

- Packet turn normalized to `2`.
- `meta.generated_at_turn` remained `2`.
- Warning recorded: `host_normalized_placeholder_generated_at_turn`.

## Failed Host-Live Attempt

Command:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-installed \
  --force-host opencode \
  --skip-host 'gemini_cli=not installed on this Mac; not claimed' \
  --skip-host 'aider=not installed on this Mac; not claimed' \
  --skip-host 'goose=not installed on this Mac; not claimed' \
  --skip-host 'cursor_agent=not installed on this Mac; not claimed' \
  --state-root /tmp/round-table-opencode-host-validation-retry \
  --agent-timeout-seconds 1800
```

Result:

- `opencode` returned `matrix_status=live_failed`.
- The wrapper retried after a transient OpenCode local failure.
- Final failure remained inside OpenCode's local state store:
  `Failed to run the query 'PRAGMA wal_checkpoint(PASSIVE)'`.
- Persisted matrix artifacts:
  `/tmp/round-table-opencode-host-validation-retry/local-agent-host-validation-matrix.json`
  and `/tmp/round-table-opencode-host-validation-retry/local-agent-host-validation-matrix.md`.
- Persisted adapter report:
  `/tmp/round-table-opencode-host-validation-retry/opencode/generic-agent-adapter-validation-report.json`.

## Isolated State Diagnostic

An isolated `XDG_DATA_HOME` smoke was attempted as a diagnostic because OpenCode's global state store showed WAL/checkpoint instability. That path performed first-run migration and then hung for more than two minutes, so the process was killed. It is not evidence of host-live support.

## Current Decision

- Codex local mainline remains launchable.
- Claude Code host-live remains claimable only for the validated machine/account evidence already checked in.
- OpenCode is installed and has a checked-in wrapper, but OpenCode host-live support is not claimable until the host matrix returns `matrix_status=live_passed`.
- Provider live remains optional fallback infrastructure and is not required for local `/room` or `/debate`.

## Next Action

Keep OpenCode as P2. Revisit after the local OpenCode state store is stable or after OpenCode can run the full matrix from a clean, non-hanging state. Do not widen launch claims based on fixture, wrapper, inventory, or direct smoke evidence alone.
