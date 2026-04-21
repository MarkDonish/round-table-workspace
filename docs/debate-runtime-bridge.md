# Debate Runtime Bridge

> Purpose: define the checked-in host bridge for `/debate`, so packet-driven debate execution can be wired from repository source instead of ad hoc session logic.
> Last reviewed: 2026-04-22

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
6. validate roundtable records produced from that launch bundle
7. build or validate reviewer-facing review packets
8. validate reviewer results against the checked-in reviewer decision contract
9. validate follow-up records against a rejected reviewer result
10. build reviewer-facing re-review packets after one checked-in follow-up round
11. write portable runtime artifacts under `artifacts/runtime/debates/<debate_id>/`

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
- `docs/debate-e2e-validation.md`
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
- `.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py`
- `.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py`
- `.codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py`
- `.codex/skills/debate-roundtable-skill/runtime/fixtures/canonical/`

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

## Roundtable Record Schema

The checked-in bridge also validates a `roundtable-record.json` that captures the visible outputs of the debate itself:

```json
{
  "schema_version": "v0.1",
  "mode": "debate_roundtable_record",
  "source_kind": "room_handoff",
  "debate_id": "debate-...",
  "source_room_id": "room-...",
  "topic_restatement": "...",
  "primary_type": "product",
  "secondary_type": "startup",
  "quick_mode": false,
  "participants": [],
  "speaker_order": [],
  "agent_outputs": [],
  "moderator_summary": {},
  "evidence_buckets": {},
  "review_status": {
    "review_required": true,
    "followup_allowed": true,
    "max_followup_rounds": 1
  }
}
```

This schema exists so the host can keep `/debate` visible outputs auditable before they are transformed into a reviewer packet.

---

## Review Result Schema

The bridge also validates a `review-result.json` after the reviewer prompt runs:

```json
{
  "schema_version": "v0.1",
  "mode": "debate_review_result",
  "source_kind": "room_handoff",
  "debate_id": "debate-...",
  "source_room_id": "room-...",
  "topic_restatement": "...",
  "quick_mode": false,
  "review_applicable": true,
  "overall_score": 8,
  "best_agent": "munger",
  "weak_agents": [],
  "evidence_gaps": [],
  "logic_gaps": [],
  "overlooked_issues": [],
  "severe_red_flags": [],
  "allow_final_decision": true,
  "required_followups": [],
  "rationale": "..."
}
```

This schema exists so the host can decide whether `/debate` may emit a final decision or must enter one follow-up loop.

`required_followups.agent_id` may target:

- one of the debate participants
- `moderator` when the reviewer explicitly requires a moderator-side补充汇总

---

## Followup Record Schema

When the first review rejects the debate, the checked-in bridge validates a `followup-record.json` with this shape:

```json
{
  "schema_version": "v0.1",
  "mode": "debate_followup_record",
  "source_kind": "room_handoff",
  "debate_id": "debate-...",
  "source_room_id": "room-...",
  "topic_restatement": "...",
  "quick_mode": false,
  "followup_round": 1,
  "rejection_summary": [],
  "required_followups": [],
  "agent_followups": [],
  "moderator_followup": {},
  "rereview_status": {
    "rereview_required": true,
    "max_followup_rounds": 1,
    "return_to_reviewer": true
  }
}
```

This schema exists so the host can validate the single allowed full-mode补充轮，不会把 reviewer 点名缺口 silently drop 掉。

---

## Re-Review Packet Shape

After a valid follow-up record exists, the checked-in bridge can build a reviewer-facing re-review packet.

It reuses the original `review-packet.json` structure and adds:

- `followup_context`
- targeted `agent_outputs[].followup_update`
- `moderator_summary.followup_update`
- updated evidence / recommendation buckets for the second review

This keeps the re-review payload structurally compatible with the reviewer contract while preserving the follow-up delta as explicit visible output.

---

## Output Location

Runtime outputs should be written under:

`artifacts/runtime/debates/<debate_id>/`

Typical files:

- `launch/launch-bundle.json`
- `roundtable/roundtable-record.json`
- `roundtable/roundtable.validation.json`
- `review/review-template.json`
- `review/review-packet.json`
- `review/review-packet.validation.json`
- `review/review-result.json`
- `review/review-result.validation.json`
- `review/review-result.reject.json`
- `review/review-result.reject.validation.json`
- `followup/followup-record.json`
- `followup/followup.validation.json`
- `followup/rereview-packet.json`
- `followup/rereview-packet.validation.json`
- `followup/review-result.allow.json`
- `followup/review-result.allow.validation.json`
- `validation-report.json`

These are generated runtime artifacts, not source of truth.

---

## Boundary

This bridge closes the gap between packet acceptance and debate-side host wiring.

It still does not prove:

- a real prompt host has executed `prompts/debate-roundtable.md`
- a real reviewer run has passed or rejected a live roundtable through an external model host
- a real prompt host has executed `prompts/debate-followup.md`
- a real follow-up loop has completed end to end through an external model host

Those remain separate live validation steps.

The checked-in E2E runner and local mock provider now prove the prompt-call wiring locally.
They do not change the external live-validation boundary above.
