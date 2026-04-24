# Room End-to-End Validation

> Purpose: define the first production-style validation flow for `/room`, so the project can move from source alignment to runtime confidence.
> Last reviewed: 2026-04-23

---

## When To Use This

Run this validation after:

- `/room` source files are aligned
- the host or orchestrator has wired the checked-in workflow
- active prompts no longer depend on machine-local paths

This file is not a historical report. It is the source validation checklist for the first live `/room` run.

---

## Checked-In Entry

Use the checked-in runner in `.codex/skills/room-skill/runtime/room_e2e_validation.py`.

If you want the first checked-in `/room -> /debate` full-chain validation instead of `/room` alone, use `.codex/skills/room-skill/runtime/room_debate_e2e_validation.py`.

Local Codex child-agent path:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py \
  --check-host-preflight \
  --preset gpt54_family

python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor local_codex \
  --state-root /tmp/round-table-room-local-codex

python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor local_codex \
  --scenario reject_followup \
  --state-root /tmp/round-table-room-debate-local-codex
```

This is the current mainline host path for the repo.
It proves the checked-in prompts can be executed directly by local child-agent tasks without going through an external provider URL.
The checked-in runners now default to the validated `gpt54_family` preset, so the shortest local command path no longer needs explicit model flags unless you are deliberately overriding the child-task lane.

That preset is now stepwise: selection keeps the primary `gpt-5.4` lane but uses a shorter timeout, `room-chat` keeps the heavier lane with a longer window, and narrower structured steps like `room-summary` / `room-upgrade` move onto a lighter same-family lane.

Generic local agent CLI path:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_executor.py \
  --check-agent-exec \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py"

python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor generic_cli \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-room-debate-generic-cli
```

This is the portability adapter path for Claude Code and other local agent CLIs. The checked-in fixture agent validates the adapter contract; each real third-party CLI still needs a live host validation run.

Fixture-backed smoke path:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-e2e
```

External provider fallback path:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --env-file .env.room \
  --check-provider-config

python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --env-file .env.room
```

Full `/room -> /debate` checked-in path:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor chat_completions \
  --room-env-file .env.room \
  --debate-env-file .env.debate
```

Checked-in real-provider live wrapper:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

This is the shortest checked-in entry for the real external-provider lane. It first runs room/debate provider preflight, treats template placeholder values as not-configured, then launches the one-command `/room -> /debate` integration flow only when both scopes are ready.

The fixture path validates the checked-in orchestration and writeback chain.
It does not count as a local child-agent or external provider pass.

Local mock provider path:

```bash
python3 .codex/skills/room-skill/runtime/mock_chat_completions_server.py --port 32123

ROOM_CHAT_COMPLETIONS_URL=http://127.0.0.1:32123/v1/chat/completions \
ROOM_CHAT_COMPLETIONS_MODEL=mock-room-model \
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --state-root /tmp/round-table-room-mock-provider
```

This path proves the checked-in Chat Completions-compatible execution chain.
It still does not count as a real external provider pass, and it is no longer the mainline runtime path.

Checked-in provider fallback regression path:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py \
  --state-root /tmp/round-table-chat-completions-regression
```

This is the shortest checked-in fallback regression command. It boots local mock providers for both `/room` and `/debate`, runs provider preflight for both scopes, then validates room, debate, and full integration in one evidence bundle.

---

## Validation Goal

Prove that the following chain works on a portable host setup:

1. `/room`
2. one normal follow-up turn
3. `/summary`
4. `/upgrade-to-debate`
5. handoff acceptance by `debate-roundtable-skill`

Success means the repo is no longer only protocol-complete. It means the checked-in workflow is executable in practice.

---

## Preconditions

Before starting, confirm all of the following:

- `README.md`, `AGENTS.md`, `.codex/skills/room-skill/SKILL.md`, and `.codex/skills/room-skill/WORKFLOW.md` agree on `/room` semantics
- `docs/room-runtime-bridge.md` is treated as the bridge contract
- `prompts/room-selection.md`, `prompts/room-chat.md`, `prompts/room-summary.md`, and `prompts/room-upgrade.md` are available to the host
- no step depends on `reports/` as live runtime input
- no step depends on Windows-local absolute paths

If any of the above is false, stop and fix source before validation.

---

## Canonical Test Topic

Use one stable topic for the first full run so results are easy to compare across machines:

`/room 我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。`

This topic is good because it naturally exercises:

- `startup`
- `product`
- `risk`
- focus narrowing
- summary extraction
- possible upgrade tension

---

## Test Flow

### Step 1. Create A Room

Input:

`/room 我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。`

Expected checks:

- a new `room_id` is created
- `original_topic` is preserved verbatim
- `primary_type` and `secondary_type` are set
- `agents` and `agent_roles` are populated
- `turn_count` is initialized correctly
- no state field is written by the prompt directly

Blocking failures:

- no roster returned
- malformed room state
- machine-local path requirement

### Step 2. Run One Follow-Up Turn

Input:

`/focus 先只盯最小可验证切口`

Expected checks:

- the same room is reused, not replaced
- `active_focus` changes to the new focus
- `room_turn` selection happens from the existing roster
- `turn_role` is assigned by the host bridge, not by chat prompt
- a new Turn is appended to `conversation_log`
- `recent_log`, `last_stage`, `turn_count`, and `silent_rounds` are updated

Blocking failures:

- room is recreated instead of continued
- prompt tries to own state writes
- `conversation_log` writeback is partial or malformed

### Step 3. Run Summary

Input:

`/summary`

Expected checks:

- `consensus_points` contains only content traceable to conversation
- `open_questions` reflects current unresolved questions
- `tension_points` captures actual unresolved disagreement
- `recommended_next_step` is specific and actionable
- `last_summary_turn` is updated

Blocking failures:

- summary invents claims not in log
- summary fields remain empty despite meaningful discussion
- host fails to persist summary output cleanly

### Step 4. Trigger Upgrade

Input:

`/upgrade-to-debate`

Expected checks:

- a valid `upgrade_signal` exists or explicit request path is accepted
- a handoff packet is produced
- the packet includes structured:
  - original topic
  - sub problems
  - consensus points
  - tension points
  - open questions
  - candidate solutions
  - suggested agents
  - upgrade reason

Blocking failures:

- packet missing `field_11_suggested_agents`
- packet missing `field_13_upgrade_reason`
- packet built from raw room log without schema packaging

### Step 5. Pass Packet To Debate

Expected checks:

- `debate-roundtable-skill` accepts the handoff context
- the checked-in `/debate` packet preflight accepts the packet shape
- `/debate` does not fall back to historical reports
- `/debate` treats the packet as the authoritative room handoff

Blocking failures:

- `/debate` ignores packet fields
- `/debate` reverts to Windows-local assumptions
- packet is accepted but structurally inconsistent with `docs/room-to-debate-handoff.md`

---

## Required Evidence

A successful validation run should leave behind evidence that can be checked without hand-waving:

- a created room state snapshot
- at least 2 turns in `conversation_log`
- a persisted summary snapshot
- a generated handoff packet
- proof that the checked-in `/debate` packet preflight accepted the packet shape
- for `local_codex`, a persisted `prompt-calls/*.child-trace.json` per prompt call
- for `generic_cli` or `claude_code`, a persisted `prompt-calls/*.agent-trace.json` per prompt call
- for failed `local_codex` runs, a persisted `prompt-calls/*.error.json` plus failed `prompt-calls/*.meta.json`

If one of these is missing, the run is incomplete.

For the local child-agent mainline, `prompt-calls/*.child-trace.json` is now the first debugging stop. It records per-attempt model choice, timeout / retry behavior, the applied `task_policy_key`, and a structured `failure_category` such as `timeout`, `invalid_model`, `invalid_json_output`, or `host_permission_or_sandbox_denied`.

For the generic local CLI adapter, `prompt-calls/*.agent-trace.json` records the command, response source, host name, timeout, and failure category. This is the first debugging stop for Claude Code or other local agent CLI integration failures.

---

## Pass Criteria

Mark the validation as passed only if all of the following are true:

1. `/room` creates and updates a stable state object
2. prompts do not directly write room state
3. `turn_role` assignment happens outside `room-chat.md`
4. `/summary` persists usable structured state
5. `/upgrade-to-debate` emits a valid handoff packet
6. `/debate` accepts the packet without needing historical reports
7. no Windows-local path is required at any point

---

## Fail Classification

### Source Failure

Use this label when the problem is in checked-in docs, prompts, or workflow definitions.

Examples:

- prompt contract mismatch
- missing required field in source schema
- contradictory routing instructions

### Host Failure

Use this label when the source is adequate but the host execution layer is not.

Examples:

- state not persisted correctly
- room context lost between turns
- handoff packet not forwarded correctly

### Environment Failure

Use this label when the workflow is blocked by local machine setup.

Examples:

- local Git not authenticated
- required runtime host unavailable
- path assumptions not portable

---

## Current Known Blockers

As of 2026-04-21, the main blockers before this validation can fully pass are:

- the checked-in E2E runner and mock provider now exist, but a real external `--executor chat_completions --env-file .env.room` run is still missing
- `/debate` handoff is now checked by a checked-in executable preflight, but not yet by a real live `/debate` execution chain
- generic CLI and Claude Code adapter routes are fixture-validated, but real Claude Code / third-party local agent live runs are still separate validation tasks
- local terminal Git access on this Mac still depends on GitHub trust for the generated SSH key

---

## Next Action After Pass

Once this validation passes:

1. mark `/room` as host-validated in `docs/room-runtime-status.md`
2. begin deeper runtime implementation or product-level development
3. treat `/room` as a usable development surface instead of a protocol-only design layer
