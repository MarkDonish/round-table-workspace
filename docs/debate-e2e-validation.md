# Debate End-to-End Validation

> Purpose: define the first production-style validation flow for `/debate`, so the project can move from bridge completeness to prompt-host execution confidence.
> Last reviewed: 2026-04-23

---

## When To Use This

Run this validation after:

- `/debate` source files are aligned
- the checked-in launch / review / followup bridge is stable
- the prompt host can access checked-in prompt files

This file is source validation guidance, not a historical report.

---

## Checked-In Entry

Use the checked-in runner in `.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py`.

By default it starts from the checked-in canonical `/room` upgrade fixture.
If you already have a persisted `/room` handoff packet, pass `--packet-json` to validate the real handoff directly.

Local Codex child-agent path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor local_codex \
  --local-codex-model gpt-5.3-codex-spark \
  --local-codex-timeout-seconds 240 \
  --scenario allow \
  --state-root /tmp/round-table-debate-local-codex-allow

python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor local_codex \
  --local-codex-model gpt-5.3-codex-spark \
  --local-codex-timeout-seconds 240 \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-local-codex-followup

python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor local_codex \
  --local-codex-model gpt-5.3-codex-spark \
  --local-codex-timeout-seconds 240 \
  --scenario reject_followup \
  --state-root /tmp/round-table-room-debate-local-codex
```

This is the current mainline host path for `/debate`.
It proves the checked-in prompts can be executed through local child-agent tasks and that `/debate` can consume a real persisted `/room` packet in one command.

Fixture-backed smoke path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor fixture \
  --scenario allow \
  --state-root /tmp/round-table-debate-e2e-allow

python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor fixture \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-e2e-followup
```

This path validates the checked-in orchestration and writeback chain.
It does not count as a live provider pass.

Local mock provider fallback path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py --port 32124

DEBATE_CHAT_COMPLETIONS_URL=http://127.0.0.1:32124/v1/chat/completions \
DEBATE_CHAT_COMPLETIONS_MODEL=mock-debate-model \
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor chat_completions \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-mock-followup
```

This path proves the checked-in Chat Completions-compatible `/debate` prompt-call chain.
It still does not count as a real external provider pass.

Checked-in provider fallback regression path:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py \
  --state-root /tmp/round-table-chat-completions-regression
```

This is the shortest checked-in fallback regression command for the provider-backed lane. It boots local mock providers for both `/room` and `/debate`, validates standalone `/debate allow`, standalone `/debate reject_followup`, and the integrated `/room -> /debate` handoff path, then writes one shared regression report.

External-provider `/room -> /debate` handoff path:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor chat_completions \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --scenario reject_followup \
  --state-root /tmp/round-table-room-debate-live
```

This is the first checked-in one-command path that can consume a real `/room` packet instead of reusing only canonical packet material.

External provider path:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --provider-scope debate \
  --env-file .env.debate \
  --check-provider-config

python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor chat_completions \
  --env-file .env.debate \
  --scenario reject_followup
```

The current `/debate` runner reuses the checked-in Chat Completions adapter, but now has an independent `DEBATE_*` provider config surface.

---

## Validation Goal

Prove that the following `/debate` chains work on a portable host setup:

1. handoff packet -> launch bundle -> roundtable -> reviewer allow
2. handoff packet -> launch bundle -> roundtable -> reviewer reject -> followup -> rereview allow

The handoff packet may come from either:

- the checked-in canonical `/room` upgrade fixture
- a persisted `/room` runtime packet passed through `--packet-json`

Success means `/debate` is no longer only bridge-complete.
It means the checked-in prompt-call workflow is executable in practice.

---

## Preconditions

Before starting, confirm all of the following:

- `README.md`, `AGENTS.md`, and `.codex/skills/debate-roundtable-skill/SKILL.md` agree on `/debate` semantics
- `docs/debate-runtime-bridge.md` is treated as the bridge contract
- `docs/reviewer-protocol.md` and `prompts/debate-followup.md` are aligned on the single allowed follow-up round
- `prompts/debate-roundtable.md`, `prompts/debate-reviewer.md`, and `prompts/debate-followup.md` are available to the host
- no step depends on `reports/` as runtime input
- no step depends on Windows-local absolute paths

If any of the above is false, stop and fix source before validation.

---

## Required Evidence

A successful validation run should leave behind evidence that can be checked without hand-waving:

- a persisted `launch-bundle.json`
- a persisted `roundtable-record.json`
- a persisted `review-packet.json`
- a persisted reviewer result
- for reject-followup scenario: a persisted `followup-record.json` and `rereview-packet.json`
- prompt-call input/output snapshots under `prompt-calls/`

If one of these is missing, the run is incomplete.

---

## Pass Criteria

Mark the validation as passed only if all of the following are true:

1. the launch bundle persists cleanly
2. the roundtable record passes checked-in validation
3. the review packet passes checked-in validation
4. the reviewer result passes checked-in validation
5. for reject-followup scenario, the follow-up record and re-review packet also pass checked-in validation
6. no Windows-local path is required at any point

---

## Boundary

This runner closes an important local gap:

- `/debate` prompt calls can now be exercised through fixture replay or a local Chat Completions-compatible mock provider
- `/debate` can now start directly from a persisted `/room` handoff packet, not only the canonical upgrade fixture

It still does not prove:

- a real external provider has executed the prompt chain
- a real host has passed user-provided live debate content through this chain
- the reviewer quality itself is good enough for production use

Those remain separate live validation steps.
