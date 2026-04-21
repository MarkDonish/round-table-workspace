# Debate Runtime Bridge

> Purpose: define the checked-in host bridge for `/debate`, so packet-driven debate execution can be wired from repository source instead of ad hoc session logic.
> Last reviewed: 2026-04-21

---

## Role

The `/debate` runtime bridge is the host-side layer that sits between:

- `/room` handoff packets
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`
- `prompts/debate-followup.md`

It does not replace those prompts.
It prepares and validates the execution artifacts that the prompts alone cannot own.

---

## Responsibilities

The checked-in bridge is responsible for these actions and no others:

1. validate an incoming `/room -> /debate` handoff packet through the checked-in packet preflight
2. reselect the final 3-5 debate agents from the packet candidate pool plus `/debate` default routing rules
3. enforce `/debate` balance constraints:
   - at least 1 defensive
   - at least 1 grounded
   - dominant agents must not exceed half
4. preserve packet continuity by keeping at least 2 agents from `field_11_suggested_agents` when possible
5. build a launch bundle for the debate-side prompt host
6. build or validate reviewer-facing review packets
7. write portable runtime artifacts under `artifacts/runtime/debates/<debate_id>/`

The bridge is not responsible for:

- inventing new debate content
- replacing the moderator
- replacing the reviewer
- reviewing hidden chain-of-thought
- writing final user-facing decisions on its own

---

## Checked-In Inputs

The debate bridge should consume only these checked-in sources:

- `AGENTS.md`
- `docs/debate-runtime-bridge.md`
- `docs/debate-skill-architecture.md`
- `docs/reviewer-protocol.md`
- `docs/red-flags.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`
- `prompts/debate-followup.md`
- `.codex/skills/debate-roundtable-skill/SKILL.md`
- `.codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py`

If a report or generated artifact disagrees with the files above, the checked-in files above win.

---

## Launch Bundle Schema

The checked-in runtime bridge emits a `launch-bundle.json` with this shape:

```json
{
  "schema_version": "v0.1",
  "mode": "debate_launch",
  "source_kind": "room_handoff",
  "debate_id": "debate-...",
  "source_room_id": "room-...",
  "topic": "...",
  "room_title": "...",
  "primary_type": "product",
  "secondary_type": "startup",
  "packet_acceptance": {},
  "packet_materials": {},
  "candidate_pool": {
    "starting_agents": [],
    "final_agents": [],
    "removed_from_suggested": [],
    "added_beyond_suggested": [],
    "minimum_overlap_target": 2,
    "actual_overlap": 2,
    "balance_after_reselection": {},
    "notes": []
  },
  "participants": [],
  "moderator": {},
  "reviewer": {},
  "speaker_order": [],
  "prompt_inputs": {}
}
```

Meaning:

- `packet_acceptance` is the checked-in packet preflight result
- `packet_materials` is the debate-usable subset of the handoff packet
- `candidate_pool` records how `/debate` reselected its final roster
- `participants` records local skill ids, responsibilities, and guardrails
- `prompt_inputs` is the prompt-host-ready structured input for roundtable, reviewer, and follow-up stages

---

## Review Packet Schema

The checked-in bridge also defines a runtime-facing `review-packet.json` for reviewer validation:

```json
{
  "schema_version": "v0.1",
  "source_kind": "room_handoff",
  "source_room_id": "room-...",
  "topic_restatement": "...",
  "primary_type": "product",
  "secondary_type": "startup",
  "quick_mode": false,
  "participants": [],
  "agent_outputs": [],
  "moderator_summary": {},
  "evidence_buckets": {
    "facts": [],
    "inferences": [],
    "uncertainties": [],
    "recommendations": []
  },
  "review_boundaries": {
    "conversation_log_reviewable": false,
    "review_only_visible_outputs": true,
    "followup_cap": 1
  }
}
```

This schema exists so the host can validate reviewer inputs against `docs/reviewer-protocol.md` before asking the reviewer prompt to pass or reject the roundtable.

---

## Output Location

Runtime outputs should be written under:

`artifacts/runtime/debates/<debate_id>/`

Typical files:

- `launch/launch-bundle.json`
- `review/review-template.json`
- `review/review-packet.validation.json`
- `validation-report.json`

These are generated runtime artifacts, not source of truth.

---

## Boundary

This bridge closes the gap between packet acceptance and debate-side host wiring.

It still does not prove:

- a real prompt host has executed `prompts/debate-roundtable.md`
- a real reviewer run has passed or rejected a live roundtable
- a real follow-up loop has completed end to end

Those remain separate live validation steps.
