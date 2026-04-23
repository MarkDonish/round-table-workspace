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

For the checked-in `/room -> /debate` integration runner:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py --help
```

For the checked-in local child-agent executor:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py --help
```

For the checked-in local mainline regression runner:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py --help
```

For the checked-in Chat Completions fallback regression runner:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py --help
```

For the checked-in Chat Completions live validation wrapper:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py --help
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

Run a local child-agent smoke test:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py \
  --check-local-exec \
  --preset gpt54_family
```

Run the checked-in local host preflight before starting the local mainline:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py \
  --check-host-preflight \
  --preset gpt54_family
```

Run the checked-in full local mainline regression suite:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

Run the checked-in full Chat Completions fallback regression suite with local mock providers:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py \
  --state-root /tmp/round-table-chat-completions-regression
```

Run the checked-in real-provider live wrapper after filling `.env.room` and `.env.debate`:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

Run the checked-in E2E validation flow through local child-agent tasks:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor local_codex \
  --state-root /tmp/round-table-room-local-codex
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

Run the checked-in `/room -> /debate` integration flow through canonical fixtures:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-debate-e2e
```

Run the checked-in `/room -> /debate` integration flow through local child-agent tasks:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor local_codex \
  --local-codex-model gpt-5.4 \
  --local-codex-fallback-models gpt-5.4-mini \
  --local-codex-reasoning-effort low \
  --local-codex-timeout-seconds 240 \
  --local-codex-timeout-retries 1 \
  --scenario reject_followup \
  --state-root /tmp/round-table-room-debate-local-codex
```

Run the checked-in `/room -> /debate` integration flow against real providers:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor chat_completions \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-room-debate-live
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

This bridge is intentionally host-agnostic.

It assumes some host or operator already called:

- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

The bridge then validates those JSON outputs and performs the state writeback that only the host is allowed to perform.

`local_codex_executor.py` is the checked-in local child-agent adapter. It reuses the local Codex host to run one prompt as one nested child task, normalizes the resulting JSON back into the runtime contracts, and now exposes explicit child-task reasoning control so `/room` and `/debate` do not blindly inherit the host's global `xhigh` profile.

It also exposes a checked-in `gpt54_family` preset. That preset freezes the currently validated Mac-local lane: `gpt-5.4` primary child-task model, `gpt-5.4-mini` same-family fallback, `low` reasoning effort, and bounded timeouts.

It now also exposes `--check-host-preflight`, which verifies the local `~/.codex` storage prerequisites that nested child tasks depend on, then runs the same checked-in smoke probe. This makes the host-side failure boundary explicit before `/room` or `/debate` work starts.

The runner-level mainline now defaults to that preset. In practice, `room_e2e_validation.py`, `room_debate_e2e_validation.py`, and `local_codex_regression.py` all use `gpt54_family` unless you explicitly override the local child-task settings.

It also hardens two real local-host failure modes that showed up during Mac validation:

- recover the final child message from `stdout.jsonl` when `--output-last-message` is truncated
- repair truncated JSON when a string loses its closing quote either at EOF or right before the next structural delimiter such as `},{"text": ...`
- normalize object-style evidence buckets like `{text, source}` back into the string lists expected by the runtime validators

`local_codex_regression.py` is the checked-in local mainline regression runner. It now runs the host preflight first, then sequences `/room`, `/debate allow`, `/debate reject_followup`, and `/room -> /debate` integration into one evidence bundle. It defaults to the `gpt54_family` preset, so a bare regression command already lands on the validated Mac-local lane and persists a checked-in `host-preflight.json` alongside the regression report.

`chat_completions_regression.py` is the checked-in provider fallback regression runner. It boots one local `/room` mock provider plus one local `/debate` mock provider, writes checked-in `.env.room.mock` and `.env.debate.mock` files into the evidence bundle, runs provider preflight for both scopes, then sequences `/room`, `/debate allow`, `/debate reject_followup`, and `/room -> /debate` integration through `--executor chat_completions`.

`chat_completions_live_validation.py` is the checked-in real-provider wrapper for the remaining unproven external lane. It first validates `.env.room` and `.env.debate` through the same checked-in provider-config reader, persists both preflight results, then launches the full `/room -> /debate` integration flow through `--executor chat_completions`. It also writes a failure report when env files are missing or still using template placeholder values.

Because nested child tasks persist session and state data under `~/.codex/`, the `local_codex` mainline should be run from a normal local terminal or any host environment that permits writing `~/.codex/sessions` and the local Codex state DB. A tighter sandbox can make the chain fail before prompt execution even starts.

`room_e2e_validation.py` is a checked-in validation harness above that bridge. It can drive the same flow through canonical fixtures, local child-agent execution, or a real Chat Completions-compatible provider, then persist evidence bundles for review.

When `/upgrade-to-debate` is explicitly user-forced and the checked-in upgrade prompt still returns `room_too_fresh`, the host bridge now packages a legal handoff packet from persisted room state. That fallback is intentionally narrow: it only applies to `user_explicit_request`, still writes the required `user_forced_early_upgrade` warning into the packet, and keeps extra host-debug detail only in `packaging_meta.warnings`.

`room_debate_e2e_validation.py` is the checked-in orchestration layer above both runtime bridges. It first runs `/room`, then forwards the persisted handoff packet into `/debate`, so the full handoff chain can be exercised with one command.

`mock_chat_completions_server.py` is a local-only fallback validation aid. It serves the checked-in canonical fixtures behind a Chat Completions-compatible HTTP endpoint so the provider-backed path can be regression-checked without relying on external credentials.

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
