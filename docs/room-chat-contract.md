# Room Chat Contract

> Purpose: provide a clean source-of-truth bridge for `/room` turn generation while `prompts/room-chat.md` is being repaired.
> Status: active fallback contract
> Last reviewed: 2026-04-21

---

## Scope

This document does not replace `docs/room-architecture.md`.

It exists to lock the executable contract for the `/room` chat step until `prompts/room-chat.md` is fully repaired.

If there is any conflict:

1. `docs/room-architecture.md`
2. this document
3. the currently corrupted body of `prompts/room-chat.md`

---

## Responsibility Boundary

`room-chat` is the utterance generator for one room turn.

It is not:

- the speaker selector
- the room-state owner
- the role assigner
- the upgrade judge

The orchestrator remains the single writer of room state.

`room-chat` only consumes input and returns one Turn object.

---

## Required Inputs

The minimum input contract is:

```text
mode: room_chat
turn_id: <integer>
stage: <explore | simulate | stress_test | converge | decision>
active_focus: <string | null>
primary_type: <task_type>
secondary_type: <task_type | null>
user_input: <string>
agents:
  - { id, short_name, structural_role, long_role }
speakers:
  - { id, short_name, turn_role, long_role, structural_role, total_score }
recent_log: <string>
conversation_history:
  - { turn_id, stage, speakers: [{ id, short_name, role, content_summary }] }
```

---

## Hard Invariants

### 1. turn_role is pre-assigned

`room-chat` must consume `speakers[i].turn_role`.

It must not reassign:

- `primary`
- `support`
- `challenge`
- `synthesizer`

If the input role set is structurally invalid, return `invalid_speakers`.

### 2. Valid speaker count

The supported range is 2-4 speakers.

If speakers are outside that range, return `invalid_speakers`.

### 3. Citation depth

Cross-agent citation is allowed, but nested citation depth must not exceed 2 hops.

`cited_agents` is built from the union of all explicit current-turn references.

For a single utterance, the current speaker does not count as a cited agent.

### 4. Length policy

Each speaker utterance should target:

- soft: 80-180 Chinese characters
- hard: 220 Chinese characters

If the generated content exceeds the hard cap, the orchestrator may truncate and record a warning.

### 5. State ownership

`room-chat` does not update:

- `silent_rounds`
- `last_stage`
- `turn_count`
- `recent_log`
- `conversation_log`
- `upgrade_signal`

All of those belong to the orchestrator.

---

## Role Semantics

### primary

`primary` leads with the current turn's main positive claim.

If the user is clearly following up on a previous disagreement, `primary` may absorb that challenge, but it must still open with a fresh claim rather than a pure rebuttal.

### support

`support` strengthens `primary` from a distinct angle.

It should add evidence, implementation detail, market grounding, or clarifying structure rather than repeating the same sentence in different words.

### challenge

`challenge` applies the strongest unresolved objection to the current turn's core claim.

It should surface downside, fragility, hidden assumptions, or structural conflict.

### synthesizer

`synthesizer` compresses the room into a forward-moving next step.

It should spend its budget on only three things:

1. what to keep from `primary`
2. what to absorb from `challenge`
3. the concrete next step

---

## Speaker Role Sanity

The role pattern should match the architecture addendum:

- 2 speakers: `primary + challenge` if structurally opposite, otherwise `primary + support`
- 3 speakers: `primary + challenge + synthesizer` if an opposite structural-role speaker exists, otherwise `primary + support + synthesizer`
- 4 speakers: `primary` fixed; `challenge` is the strongest opposite structural-role speaker, or fallback lowest-scoring remaining speaker; the rest become `support` and `synthesizer`

Again: this assignment is done by the orchestrator, not by `room-chat`.

`room-chat` only validates the inputs against the expected pattern.

---

## Output Schema

The output is one Turn JSON object:

```json
{
  "turn_id": 0,
  "stage": "",
  "active_focus": null,
  "user_input": "",
  "speakers": [
    {
      "agent_id": "",
      "short_name": "",
      "role": "primary|support|challenge|synthesizer",
      "content": ""
    }
  ],
  "cited_agents": [],
  "warnings": [],
  "meta": {
    "generated_at_turn": 0,
    "prompt_version": "room-chat contract bridge v0.1",
    "tokens_used_estimate": 0
  }
}
```

---

## Warning Codes

Valid warning examples include:

- `nested_citation_exceeded`
- `citation_out_of_roster`
- `length_exceeded_<speaker_id>`
- `persona_drift_<speaker_id>`

Warnings are allowed, but schema breakage is not.

---

## Failure Modes

Return a strict error object on invalid input:

```json
{
  "error": "<code>",
  "detail": "<one-line explanation>",
  "suggestion": "<how the orchestrator should fix the input>"
}
```

Supported error codes:

- `invalid_speakers`
- `invalid_input`
- `agent_not_in_pool`

---

## Integration Notes

The orchestrator should treat this contract as the clean fallback when maintaining or repairing `prompts/room-chat.md`.

This document is intended to reduce ambiguity, not to duplicate every stylistic instruction from the final prompt body.
