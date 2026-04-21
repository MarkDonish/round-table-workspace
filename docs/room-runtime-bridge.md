# Room Runtime Bridge

> Purpose: define the missing checked-in orchestrator bridge behind `/room`, so the repo can move from protocol-complete to runtime-complete without relying on Windows-only historical context.
> Last reviewed: 2026-04-21

---

## Role

This document is the implementation-facing bridge contract for `/room` runtime integration.

It sits between:

- source protocol docs in `docs/`
- prompt contracts in `prompts/`
- the runtime entry described by `.codex/skills/room-skill/SKILL.md`

It does not replace prompt logic. It defines what the missing orchestrator must read, write, and validate.

The minimal checked-in bridge implementation now lives at:

- `.codex/skills/room-skill/runtime/room_runtime.py`
- `.codex/skills/room-skill/runtime/README.md`
- `.codex/skills/room-skill/runtime/fixtures/canonical/`

This document remains the contract layer. The runtime code must stay aligned with it.

---

## What The Bridge Owns

The runtime bridge is responsible for these actions and no others:

1. parse user intent and `/room` commands
2. create and load room state
3. call the correct prompt in the correct mode
4. assign `turn_role` before calling `prompts/room-chat.md`
5. write back room state after each turn
6. trigger `/summary` and persist its output
7. trigger `/upgrade-to-debate` and pass the packet forward
8. keep all runtime reads machine-portable and repo-relative

The bridge is not allowed to:

- invent protocol rules outside `docs/` and `prompts/`
- treat `reports/` as executable source
- let prompts write state directly
- bypass the handoff packet when entering `/debate`

---

## Required Runtime Inputs

A Mac-ready `/room` runtime bridge should consume only these checked-in inputs:

- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `docs/room-chat-contract.md`
- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `.codex/skills/room-skill/SKILL.md`

If runtime code needs anything outside this set, that dependency should be checked in and added here explicitly.

---

## Required Room State Surface

The bridge should own persistence and updates for these room state fields:

- `room_id`
- `title`
- `mode`
- `original_topic`
- `primary_type`
- `secondary_type`
- `active_focus`
- `agents`
- `agent_roles`
- `consensus_points`
- `open_questions`
- `tension_points`
- `recommended_next_step`
- `silent_rounds`
- `turn_count`
- `last_stage`
- `recent_log`
- `conversation_log`
- `upgrade_signal`

Prompts may read from this state surface, but only the bridge may write it.

---

## Command Routing Contract

### 1. `/room`

On first entry:

1. parse the topic and explicit constraints
2. call `prompts/room-selection.md` in `room_full`
3. create initial room state
4. return the first rostered room context

On subsequent turns:

1. load existing room state
2. call `prompts/room-selection.md` in `room_turn`
3. assign `turn_role`
4. call `prompts/room-chat.md`
5. persist the new Turn and derived state updates

### 2. `/focus`

1. update `active_focus`
2. preserve the existing roster unless a prompt-driven re-selection is explicitly intended
3. continue with a normal `room_turn`

### 3. `/summary`

1. collect the current `conversation_log`
2. pass `previous_summary`
3. call `prompts/room-summary.md`
4. overwrite or merge fields exactly as required by the summary contract

### 4. `/upgrade-to-debate`

1. ensure an `upgrade_signal` exists or the user explicitly requested the upgrade path
2. call `prompts/room-upgrade.md`
3. validate the resulting handoff packet
4. pass only the packet into `debate-roundtable-skill`

### 5. `/add` and `/remove`

1. treat them as roster patch operations
2. call `prompts/room-selection.md` in `roster_patch`
3. persist the updated roster and any follow-up structural warnings

---

## Turn Writeback Contract

After each successful `room_turn`, the bridge must update at least:

- `turn_count`
- `last_stage`
- `recent_log`
- `conversation_log`
- `silent_rounds`

The writeback order should be:

1. validate the generated Turn shape
2. append the Turn to `conversation_log`
3. update counters and stage markers
4. rebuild `recent_log`
5. persist the state atomically if the host supports it

If Turn validation fails, the bridge should not partially write state.

---

## Summary Writeback Contract

After `/summary`, the bridge must treat the prompt output as the new state snapshot for:

- `consensus_points`
- `open_questions`
- `tension_points`
- `recommended_next_step`

It should also update:

- `last_summary_turn`

The bridge should not reinterpret the summary semantically after the prompt returns.

---

## Upgrade Handoff Contract

Before passing control to `/debate`, the bridge must verify:

1. the handoff packet matches `docs/room-to-debate-handoff.md`
2. `field_11_suggested_agents` contains 3-5 agents
3. `field_13_upgrade_reason` is populated
4. the packet contains structured `consensus_points`, `tension_points`, and `open_questions`

Then it should:

1. mark the room as upgraded or archived, depending on host behavior
2. pass the packet to `debate-roundtable-skill`
3. avoid mutating the packet after validation

---

## Mac-Ready Requirements

A `/room` bridge is not Mac-ready unless all of the following are true:

- it uses repo-relative or host-portable paths only
- it does not require Windows-local runtime directories
- it does not read `reports/` as live runtime input
- it treats `.codex/skills/room-skill/SKILL.md` as the runtime entry contract
- it can run the same flow on a fresh Mac clone of this repo

The current checked-in bridge satisfies the repo-relative path and state writeback requirements, and it ships with a canonical fixture replay for local validation.

---

## Minimum Validation Flow

Before calling `/room` production-ready, run this sequence end-to-end:

1. create a new room from a plain topic
2. complete one follow-up `room_turn`
3. run `/summary`
4. trigger `/upgrade-to-debate`
5. verify the packet is accepted by `debate-roundtable-skill`

Success means:

- no state field is written by prompts directly
- no machine-local path is required
- no historical report is needed to continue the flow
- the final handoff packet is structurally valid

---

## Non-Goals

- This document does not define UI behavior.
- This document does not replace the prompt files.
- This document does not authorize new repo structure changes by itself.
- This document does not claim that provider-backed live integration is already finished.
