# /room Runtime Workflow

> Purpose: provide the checked-in runtime playbook behind `/room`, so execution can continue from repository source instead of Windows-only historical context.
> Scope: command routing, state ownership, prompt invocation order, and writeback rules.

---

## Use This File

When `/room` is active, treat this file as the operational workflow companion to `.codex/skills/room-skill/SKILL.md`.

Follow this precedence order:

1. `AGENTS.md`
2. `.codex/skills/room-skill/SKILL.md`
3. this file
4. `docs/room-runtime-bridge.md`
5. `docs/room-architecture.md`
6. `prompts/room-*.md`

If historical reports disagree with this workflow, the checked-in source files win.

---

## Accepted Commands

The `/room` runtime should only handle these explicit commands:

- `/room <topic>`
- `/focus <focus text>`
- `/summary`
- `/upgrade-to-debate`
- `/add <agent>`
- `/remove <agent>`

Everything else should stay in daily mode unless the host has already established an active room context.

---

## State Ownership

Only the host bridge or orchestrator may write room state.

Prompts may read state, but they must not directly mutate it.

The minimum writable state surface is:

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
- `last_summary_turn`

---

## New Room Flow

Use this path only when the user explicitly enters `/room` without an existing active room context.

1. Parse the original topic and explicit constraints.
2. Call `prompts/room-selection.md` in `room_full` mode.
3. Validate the returned roster and structural balance.
4. Create the initial room state.
5. Persist:
   - `room_id`
   - `title`
   - `mode`
   - `original_topic`
   - `primary_type`
   - `secondary_type`
   - `active_focus`
   - `agents`
   - `agent_roles`
   - `silent_rounds`
   - `turn_count = 0`
   - `last_stage`
6. Return the initialized room context.

Recommended host behavior:

- if the product wants a faster first experience, continue immediately into the normal turn flow after state creation
- if not, stop after room creation and wait for the next explicit turn

---

## Normal Turn Flow

Use this path when a room already exists and the user continues the discussion.

1. Load the current room state.
2. Call `prompts/room-selection.md` in `room_turn` mode.
3. Choose the current round speakers from the existing roster.
4. Assign `turn_role` before calling chat.
5. Call `prompts/room-chat.md`.
6. Validate the generated Turn object.
7. Append the Turn to `conversation_log`.
8. Update:
   - `turn_count`
   - `last_stage`
   - `recent_log`
   - `silent_rounds`
9. Persist the new state atomically when the host supports atomic writes.

If Turn validation fails, do not partially write state.

---

## Turn Role Assignment

`turn_role` is assigned by the runtime bridge, not by `prompts/room-chat.md`.

Before chat generation, map the selected speakers into the runtime roles described by `docs/room-architecture.md`:

- `primary`
- `support`
- `challenge`
- `synthesizer`

Minimum rules:

- every turn should have one clear `primary`
- if a defensive or tension-bearing agent is selected, prefer giving one speaker `challenge`
- if 3 or more speakers are selected, assign one `synthesizer`
- if only 2 speakers are selected, keep the role set minimal and avoid fake complexity

The host may tune exact assignment heuristics later, but it must keep role ownership outside the prompt.

---

## Focus Flow

Use this path when the user explicitly narrows or redirects the current room.

1. Load the existing room.
2. Update `active_focus`.
3. Preserve the roster unless a deliberate reselection is required.
4. Continue with the normal turn flow.

Do not rebuild the room from scratch just because focus changed.

---

## Summary Flow

Use this path only for `/summary` or when host rules explicitly trigger a stage summary.

1. Load `conversation_log` and current summary fields.
2. Build `previous_summary` from state.
3. Call `prompts/room-summary.md`.
4. Treat the returned `summary_update` as authoritative.
5. Persist:
   - `consensus_points`
   - `open_questions`
   - `tension_points`
   - `recommended_next_step`
   - `last_summary_turn`

Do not reinterpret the meaning of the summary after the prompt returns.

---

## Upgrade Flow

Use this path only when the host already has a valid reason to consider `/upgrade-to-debate`.

1. Confirm there is an `upgrade_signal`, or that the user explicitly requested upgrade.
2. Load the latest room state and summary fields.
3. Call `prompts/room-upgrade.md`.
4. Validate the returned handoff packet against `docs/room-to-debate-handoff.md`.
5. Confirm at minimum:
   - `field_11_suggested_agents` contains 3-5 agents
   - `field_13_upgrade_reason` is populated
   - structured `consensus_points`, `tension_points`, and `open_questions` exist
6. Mark the room as upgraded or archived according to host behavior.
7. Pass only the packet into `debate-roundtable-skill`.

Never bypass the handoff packet and never pass raw room logs directly into `/debate`.

---

## Roster Patch Flow

Use this path for `/add` and `/remove`.

1. Load the existing room.
2. Call `prompts/room-selection.md` in `roster_patch` mode.
3. Persist the updated roster.
4. Re-run structural balance checks.
5. Preserve the rest of the room state unless the patch explicitly changes it.

Patch operations modify an existing room. They do not create a new room.

---

## Prompt Invocation Contract

The host should call prompts in this order only:

- room creation: `room-selection.md` with `room_full`
- normal progression: `room-selection.md` with `room_turn`, then `room-chat.md`
- summary: `room-summary.md`
- upgrade: `room-upgrade.md`
- roster patch: `room-selection.md` with `roster_patch`

Do not call `room-chat.md` without speaker selection and `turn_role` assignment already completed.

---

## Writeback Invariants

The runtime bridge must preserve these invariants:

1. prompts do not write state directly
2. state writes happen only after validation
3. all runtime reads are repo-relative or host-portable
4. `reports/` is never treated as live runtime input
5. `/room -> /debate` always goes through a validated handoff packet

---

## Failure Handling

On failure, prefer explicit structured errors over silent fallback.

Typical failure cases:

- room not found
- malformed room state
- invalid prompt output
- missing summary before upgrade
- invalid handoff packet
- path references that still assume a Windows-local machine

When failure occurs:

1. stop the current state write
2. return a concrete reason
3. point back to the source contract that was violated

---

## Minimum Validation Checklist

Do not treat `/room` as production-ready unless this sequence works end to end:

1. create a room from a plain topic
2. complete one normal follow-up turn
3. run `/summary`
4. run `/upgrade-to-debate`
5. confirm the packet is accepted by `debate-roundtable-skill`

Success means:

- no prompt directly writes room state
- no machine-local path is required
- no historical report is needed to continue the flow
- the final handoff packet is structurally valid

---

## Current Limitation

This file makes the runtime playbook checked in and portable, but it does not by itself prove that host-side persistence and execution have been validated on Mac.

That final step still requires a live end-to-end run.
