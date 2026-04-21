# /room Runtime Bridge

This directory contains the checked-in host bridge behind `/room`.

It does not replace the prompts. Instead, it does the host-side work that the prompts are not allowed to do:

- validate prompt JSON outputs
- assign `turn_role`
- persist room state
- update `silent_rounds`, `turn_count`, `last_stage`, and `recent_log`
- persist summary snapshots
- validate and persist `/room -> /debate` handoff packets
- call the checked-in `/debate` packet preflight before persisting handoff acceptance

## Main Entry

Run:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py --help
```

For the checked-in end-to-end validation runner:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py --help
```

For the checked-in local mock Chat Completions provider:

```bash
python3 .codex/skills/room-skill/runtime/mock_chat_completions_server.py --help
```

For live prompt calls against a Chat Completions-compatible provider:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py --help
```

For the checked-in `/debate` packet preflight:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py --help
```

## Most Useful Commands

Replay the checked-in canonical flow:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical
```

Run the checked-in E2E validation flow through canonical fixtures:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-e2e
```

Check live provider config from an explicit env file:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --env-file .env.room \
  --check-provider-config
```

Call one checked-in prompt through a Chat Completions-compatible endpoint:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --env-file .env.room \
  --prompt-file prompts/room-selection.md \
  --input-json path/to/selection-input.json \
  --output-json path/to/selection-output.json
```

Run the checked-in E2E validation flow against a real Chat Completions-compatible provider:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --env-file .env.room
```

Run the same provider-backed path locally without external credentials:

```bash
python3 .codex/skills/room-skill/runtime/mock_chat_completions_server.py --port 32123

ROOM_CHAT_COMPLETIONS_URL=http://127.0.0.1:32123/v1/chat/completions \
ROOM_CHAT_COMPLETIONS_MODEL=mock-room-model \
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --state-root /tmp/round-table-room-mock-provider
```

Create a room from `room_full` and optionally continue into the first turn:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py start-room \
  --topic "我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。" \
  --selection-json path/to/room_full.json \
  --initial-turn-selection-json path/to/turn_selection.json \
  --initial-turn-chat-json path/to/turn_chat.json
```

Apply a follow-up turn:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-turn \
  --room-id room-1234abcd \
  --user-input "/focus 先只盯最小可验证切口" \
  --selection-json path/to/turn_selection.json \
  --chat-json path/to/turn_chat.json
```

Apply `/summary`:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-summary \
  --room-id room-1234abcd \
  --summary-json path/to/summary.json
```

Apply `/upgrade-to-debate`:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-upgrade \
  --room-id room-1234abcd \
  --upgrade-json path/to/upgrade.json \
  --explicit-user-request
```

Apply `/add` or `/remove` after a `roster_patch` prompt result:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py patch-roster \
  --room-id room-1234abcd \
  --action add \
  --selection-json path/to/roster_patch.json
```

## Output Location

Runtime state and evidence bundles are written under:

`artifacts/runtime/rooms/<room_id>/`

Typical files:

- `state.json`
- `prompt-calls/001-room_full-selection.input.json`
- `prompt-calls/001-room_full-selection.output.json`
- `turns/turn-001.selection.json`
- `turns/turn-001.chat.json`
- `turns/turn-001.turn.json`
- `summary/summary-turn-002.json`
- `handoff/packet-turn-002.json`
- `handoff/debate-acceptance.json`
- `validation-report.json`

## Scope Boundary

This bridge is intentionally provider-agnostic.

It assumes some host or operator already called:

- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

The bridge then validates those JSON outputs and performs the state writeback that only the host is allowed to perform.

`room_e2e_validation.py` is a checked-in validation harness above that bridge. It can drive the same flow through either canonical fixtures or a real Chat Completions-compatible provider, then persist evidence bundles for review.

`mock_chat_completions_server.py` is a local-only validation aid. It serves the checked-in canonical fixtures behind a Chat Completions-compatible HTTP endpoint so the provider-backed path can be regression-checked without relying on external credentials.

`debate_packet_validator.py` is a checked-in `/debate`-side preflight. `/room` calls it before writing `handoff/debate-acceptance.json`, so handoff acceptance is no longer just a plain-text skill-entry check.

## Live Provider Config

The checked-in example env file is:

`/.env.room.example`

Required variables:

- `ROOM_CHAT_COMPLETIONS_URL`
- `ROOM_CHAT_COMPLETIONS_MODEL`

Optional variables:

- `ROOM_PROVIDER_AUTH_BEARER`
- `ROOM_PROVIDER_TIMEOUT_SECONDS`
