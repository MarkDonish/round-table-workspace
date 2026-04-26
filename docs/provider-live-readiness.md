# Provider Live Readiness

This document is the source of truth for the Chat Completions-compatible provider fallback lane.

## Boundary

The provider lane is a fallback and regression lane. It is not the local mainline.

The URL in this document is not a meeting room URL and not the place where local
agents meet. It is only an optional HTTP endpoint for testing an external
Chat Completions-compatible provider.

For local-first `/room` and `/debate`, use the checked-in local Codex mainline
instead. No provider URL is required for that path.

Do not report provider live validation as passed unless the real wrapper runs against non-mock `.env.room` and `.env.debate` files and the final report returns `live_run_passed: true`.

## When Not To Fill A URL

Do not fill `ROOM_CHAT_COMPLETIONS_URL` or `DEBATE_CHAT_COMPLETIONS_URL` when:

- you only want to use the local `/room` skill flow
- you only want to use the local `/debate` skill flow
- you are validating the Codex local mainline
- you are validating the generic local agent adapter with fixture or local CLI
  agents

Use provider URLs only when the specific task is to prove the optional external
provider-live lane.

## Three Different Checks

| Check | Command | What It Proves | What It Does Not Prove |
|---|---|---|---|
| Config readiness | `python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py` | Required env files exist and do not contain template placeholders | Provider endpoint actually responds or follows prompt contracts |
| Mock regression | `python3 .codex/skills/room-skill/runtime/chat_completions_regression.py` | Provider-compatible wiring works locally with checked-in mock servers | A real external provider works |
| Real live validation | `python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py --room-env-file .env.room --debate-env-file .env.debate --state-root /tmp/round-table-chat-completions-live` | Real provider executes `/room -> /debate` | Nothing beyond the tested provider/config/run |

## Readiness

Run:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py \
  --output-json /tmp/round-table-chat-completions-readiness.json
```

Use strict mode in automation:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py --strict
```

Strict mode exits non-zero unless both provider scopes are ready for a real live run.

For a cross-lane support-claim summary that also includes local agent host
evidence, run:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

This report does not send provider requests. It records provider live as
`blocked_or_not_configured` until `.env.room` and `.env.debate` are ready.

## Required Local Files

The real live lane expects local, untracked files:

```text
.env.room
.env.debate
```

Use the checked-in templates only as examples:

```text
.env.room.example
.env.debate.example
```

Do not commit real provider tokens.

## Room Env

Required:

```text
ROOM_CHAT_COMPLETIONS_URL=https://...
ROOM_CHAT_COMPLETIONS_MODEL=...
```

Optional:

```text
ROOM_PROVIDER_AUTH_BEARER=...
ROOM_PROVIDER_API_KEY=...
ROOM_PROVIDER_TIMEOUT_SECONDS=60
OPENAI_API_KEY=...
```

## Debate Env

Required:

```text
DEBATE_CHAT_COMPLETIONS_URL=https://...
DEBATE_CHAT_COMPLETIONS_MODEL=...
```

Optional:

```text
DEBATE_PROVIDER_AUTH_BEARER=...
DEBATE_PROVIDER_API_KEY=...
DEBATE_PROVIDER_TIMEOUT_SECONDS=60
OPENAI_API_KEY=...
```

`DEBATE_*` values are preferred for `/debate`. The checked-in config reader can fall back to `ROOM_*` for debate scope, but production validation should keep both scopes explicit.

## Real Live Run

After readiness passes:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

The wrapper first checks both env files, then runs the full `/room -> /debate` integration flow through `--executor chat_completions`.

## Current Status

- Mock provider regression is checked in and validated.
- Real provider readiness now has a checked-in config-only preflight.
- Real provider live validation remains unproven until real `.env.room` and `.env.debate` files are supplied locally.
