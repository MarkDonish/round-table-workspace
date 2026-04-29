# Protocol Spec

> Purpose: provide one testable protocol overview for `/room`, `/debate`, and
> `/room -> /debate` while keeping the detailed architecture documents as the
> source for deeper implementation rules.
>
> Status: active protocol index for v0.2.0-alpha planning.

## Source Documents

This document summarizes and cross-links the current protocol surface. If a
detail appears contradictory, resolve it in the more specific source document
and then update this overview.

Primary sources:

- `docs/room-architecture.md`
- `docs/debate-skill-architecture.md`
- `docs/room-to-debate-handoff.md`
- `docs/room-chat-contract.md`
- `docs/reviewer-protocol.md`
- `docs/decision-quality-rubric.md`
- `docs/release-candidate-scope.md`

Supporting runtime and prompt sources:

- `docs/room-runtime-bridge.md`
- `docs/debate-runtime-bridge.md`
- `docs/room-selection-policy.md`
- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`

## Protocol Goals

The protocol has five jobs:

1. Keep `/room` and `/debate` explicit-only workflows.
2. Preserve room state and debate evidence in portable, repo-relative
   structures.
3. Separate exploratory discussion from formal decision review.
4. Make outputs reviewable through structured fields, not opaque free text.
5. Preserve claim-safe release boundaries around host-live and provider-live
   support.

## Explicit-Only Trigger Rule

`/room` and `/debate` are not default chat modes. A host may suggest that a user
choose one of them for a complex strategic question, but it must not enter the
workflow until the user explicitly starts with `/room`, `/debate`, or continues
inside an already active workflow.

Allowed entry shapes:

```text
/room 我想讨论一个面向大学生的 AI 学习产品
/debate 这个创业方向值不值得做
/upgrade-to-debate
```

Not allowed:

- auto-running `/room` because a question looks broad
- auto-running `/debate` because a decision sounds important
- treating a transcript, fixture, or report as a live host invocation

## /room State Machine

`/room` is a stateful, semi-structured discussion workflow. The orchestrator is
the only writer of room state; prompts consume inputs and return structured
outputs for the orchestrator to validate and write back.

```text
idle
  -> room_full
  -> active_room
  -> room_turn
  -> summary
  -> room_turn
  -> upgrade_ready
  -> handoff_packaged
  -> upgraded_to_debate
```

### States

| State | Meaning | Owner |
|---|---|---|
| `idle` | No active room is loaded. | host/orchestrator |
| `room_full` | Initial topic is parsed, panel is selected, state is created. | orchestrator + room-selection |
| `active_room` | Room state exists and can receive follow-up user inputs. | orchestrator |
| `room_turn` | A follow-up input is routed, speakers are selected, and one Turn is generated. | orchestrator + room-selection + room-chat |
| `summary` | `/summary` extracts consensus, open questions, tension, and next step. | room-summary + orchestrator |
| `upgrade_ready` | An upgrade signal exists or the user explicitly requested upgrade. | orchestrator |
| `handoff_packaged` | `room-upgrade` produced a validated `handoff_packet`. | room-upgrade + orchestrator |
| `upgraded_to_debate` | The packet has been handed to `/debate`; raw room log is not the debate input. | orchestrator |

### Room Transition Rules

- `room_full` initializes persistent room fields and runtime companion fields.
- `room_turn` does not run until speaker selection and `turn_role` assignment
  are complete.
- `/focus` changes `active_focus` and then continues through `room_turn`.
- `/summary` updates only the summary fields defined in the room summary
  contract.
- `/upgrade-to-debate` must package a handoff packet; it must not dump the raw
  room log into `/debate`.

## /debate State Machine

`/debate` is a formal decision review workflow. It may start from a direct
`/debate` topic or from a validated `/room` handoff packet.

```text
idle
  -> identify_issue
  -> classify_task
  -> select_panel
  -> assign_work
  -> collect_arguments
  -> moderator_summary
  -> reviewer_check
  -> final_decision
```

### Debate Steps

| Step | Required Output |
|---|---|
| `identify_issue` | issue text, boundary, what kind of question is being asked |
| `classify_task` | primary task type, optional secondary type, routing rationale |
| `select_panel` | 3-5 agents, moderator, reviewer, selection rationale |
| `assign_work` | each agent's responsibility and non-responsibility |
| `collect_arguments` | visible agent statements with evidence, uncertainty, and concrete advice |
| `moderator_summary` | restated issue, panel duties, consensus, conflict, assumptions, initial recommendation |
| `reviewer_check` | score, red flags, evidence gaps, allow/reject/follow-up outcome |
| `final_decision` | one recommendation, reasons, risks, next action, stop/review condition |

### Debate Transition Rules

- Full `/debate` cannot skip reviewer review.
- `--quick` may reduce review depth only if the quick-mode contract says so; it
  must not imply full reviewer approval.
- If reviewer result is `follow_up_required`, the debate may run one targeted
  supplement before re-review.
- If review still fails, the output is a blocked or temporary conclusion, not a
  polished final decision.

## /room -> /debate Handoff Contract

The handoff exists to compress exploratory room state into a bounded review
input. `/debate` consumes `handoff_packet`, not `conversation_log`.

`schemas/room-to-debate-handoff.schema.json` is the canonical portable handoff
contract, with `examples/fixtures/room-to-debate-handoff.valid.json` as the
minimum valid fixture. Debate sessions may embed the packet in
`handoff_packet`, or use `null` for direct debates.

The legacy runtime packet with `schema_version: "v0.1"` remains a compatibility
artifact for the current checked-in `/room` and `/debate` bridges. It is not the
external contract. Conversion lives in `roundtable_core/protocol/handoff.py`:

- `runtime_packet_to_portable_handoff(...)`
- `portable_handoff_to_runtime_packet(...)`

Room runtime upgrade now writes both the legacy packet and a
`portable-handoff-packet` projection. Debate preflight accepts portable packets
by converting them through the compatibility layer before using the legacy
validator.

Required high-level packet shape:

```json
{
  "schema_version": "0.1.0",
  "source_room_session_id": "room-example-session",
  "decision_question": "",
  "context_summary": "",
  "key_assumptions": [],
  "known_evidence": [],
  "open_questions": [],
  "risk_flags": [],
  "recommended_panel": [],
  "handoff_created_at": "",
  "claim_boundary": {}
}
```

Handoff invariants:

- Original topic is copied, not rewritten.
- Consensus, tension, open questions, candidate solutions, factual claims, and
  uncertainty points are extracted from visible room state and conversation.
- Suggested agents are references only; `/debate` may reselect according to its
  own balance rules.
- Raw `conversation_log`, `silent_rounds`, `turn_count`, and `recent_log` stay
  outside the debate review scope.

## Session State Fields

These fields define the current protocol surface. RTW-006 introduced
`schemas/room-session.schema.json` as the portable `/room` session wrapper, with
`tests/fixtures/room-session.valid.json` as the minimum valid fixture. RTW-007
introduced `schemas/debate-session.schema.json` and
`schemas/debate-result.schema.json`, with
`examples/fixtures/debate-session.valid.json` and
`examples/fixtures/debate-result.valid.json` as minimum valid fixtures. RTW-008
introduced `schemas/room-to-debate-handoff.schema.json` and
`examples/fixtures/room-to-debate-handoff.valid.json`.

### Room Session Fields

| Field | Required | Writer | Notes |
|---|---|---|---|
| `room_id` | yes | orchestrator | Stable room identifier. |
| `title` | yes | orchestrator | Human-readable room title. |
| `mode` | yes | orchestrator | Standard, focused, or upgrading room mode. |
| `original_topic` | yes | orchestrator | User topic copied from initial `/room`. |
| `primary_type` | yes | room-selection via orchestrator | Main task family. |
| `secondary_type` | no | room-selection via orchestrator | Optional secondary task family. |
| `active_focus` | no | orchestrator | Current `/focus` value. |
| `agents` | yes | room-selection via orchestrator | Selected roster. |
| `agent_roles` | yes | room-selection via orchestrator | Long-role map. |
| `conversation_log` | yes | orchestrator | Structured Turns. |
| `consensus_points` | yes | room-summary via orchestrator | Summary field. |
| `open_questions` | yes | room-summary via orchestrator | Summary field. |
| `tension_points` | yes | room-summary via orchestrator | Summary field. |
| `recommended_next_step` | no | room-summary via orchestrator | One concrete next action. |
| `upgrade_signal` | no | orchestrator | Reason and confidence for upgrade. |
| `silent_rounds` | yes | orchestrator | Runtime companion field. |
| `turn_count` | yes | orchestrator | Successful room turns only. |
| `last_stage` | yes | orchestrator | Last selected stage. |
| `recent_log` | yes | orchestrator | Compressed recent turn history. |

### Room Session Schema Mapping

`schemas/room-session.schema.json` uses a local-first wrapper so room sessions
can be saved, resumed, tested, and later handed off without requiring a provider
URL.

| Schema Field | Runtime Mapping | Meaning |
|---|---|---|
| `schema_version` | schema only | Room session schema version, currently `0.1.0`. |
| `session_id` | `room_id` | Stable room identifier. |
| `workflow` | constant | Must be `room`. |
| `user_question` | `original_topic` | Original explicit `/room` user question. |
| `current_focus` | `active_focus` | Current `/focus` value or `null`. |
| `panel` | `agents` + `agent_roles` | Selected roster and long-lived roles. |
| `turns` | `conversation_log` | Visible room turns generated by `room-chat`. |
| `summaries` | summary writebacks | Snapshots of consensus, questions, tension, and next step. |
| `handoff_packet` | room-upgrade output | `null` until `/upgrade-to-debate` creates a packet. |
| `claim_boundary` | release boundary | Local-first, host-live, and provider-live claim status. |
| `created_at` / `updated_at` | host metadata | Session timestamps. |

Validation command:

```bash
./rtw validate --schema schemas/room-session.schema.json --fixture tests/fixtures/room-session.valid.json
```

### Debate Session Fields

| Field | Required | Writer | Notes |
|---|---|---|---|
| `debate_id` | yes | debate runtime | Stable debate identifier. |
| `input_source` | yes | debate runtime | Direct topic or handoff packet. |
| `issue` | yes | debate runtime | Restated issue and boundary. |
| `primary_type` | yes | debate runtime | Main task family. |
| `secondary_type` | no | debate runtime | Optional secondary task family. |
| `selected_panel` | yes | debate runtime | 3-5 participants. |
| `agent_assignments` | yes | debate runtime | Duties and non-duties. |
| `agent_arguments` | yes | participant agents/runtime | Visible argument artifacts. |
| `moderator_summary` | yes | moderator/runtime | Consensus, conflict, assumptions, initial recommendation. |
| `reviewer_result` | yes for full mode | reviewer/runtime | Score and allow/reject/follow-up result. |
| `final_outcome` | yes | debate runtime | `allow`, `reject`, or `follow_up_required`. |
| `final_decision` | conditional | debate runtime | Present only when review allows final decision. |
| `claim_boundary` | yes | runtime/reporting | Support scope and evidence status. |

### Debate Schema Mapping

`schemas/debate-session.schema.json` captures a portable completed `/debate`
session, while `schemas/debate-result.schema.json` captures the final result
envelope that can be stored or passed to another local-first host.

| Schema Field | Runtime Mapping | Meaning |
|---|---|---|
| `schema_version` | schema only | Debate schema version, currently `0.1.0`. |
| `session_id` | `debate_id` | Stable debate identifier. |
| `workflow` | constant | Must be `debate`. |
| `input_source` | `source_kind` | Direct debate or room handoff. |
| `handoff_packet` | handoff schema | Embedded room-to-debate packet when `input_source` is `room_handoff`; `null` for direct debates. |
| `launch_bundle` | `launch/launch-bundle.json` | Routing, selection, and prompt-host inputs. |
| `selected_panel` | `launch_bundle.participants` | Final 3-5 debate participants. |
| `agent_arguments` | `roundtable-record.agent_outputs` | Visible participant outputs. |
| `moderator_summary` | `roundtable-record.moderator_summary` | Consensus, conflicts, assumptions, and preliminary recommendation. |
| `reviewer_result` | `review-result.json` | Reviewer score, gaps, red flags, and follow-up requirements. |
| `final_outcome` | runtime decision | `allow`, `reject`, or `follow_up_required`. |
| `open_questions` | result envelope | Remaining unresolved questions after review. |
| `evidence` | `evidence_buckets` | Facts, inferences, uncertainties, and recommendations. |
| `claim_boundary` | release boundary | Local-first, host-live, and provider-live claim status. |

Validation commands:

```bash
./rtw validate --schema schemas/debate-session.schema.json --fixture examples/fixtures/debate-session.valid.json
./rtw validate --schema schemas/debate-result.schema.json --fixture examples/fixtures/debate-result.valid.json
./rtw validate --schema schemas/room-to-debate-handoff.schema.json --fixture examples/fixtures/room-to-debate-handoff.valid.json
```

## Output Contracts

### Room Outputs

- `room_full` returns a roster, task classification, stage, structural check,
  and initial state inputs.
- `room_turn` returns a selected speaker list and stage decision before
  `room_chat` runs.
- `room_chat` returns exactly one Turn object with 2-4 speakers, roles,
  content, citations, warnings, and metadata.
- `room_summary` returns updated `consensus_points`, `open_questions`,
  `tension_points`, and `recommended_next_step`.
- `room_upgrade` returns a validated `handoff_packet`.

### Debate Outputs

- Launch bundle: issue, task classification, selected panel, assignments, and
  input packet reference when applicable.
- Round-table record: visible agent arguments and moderator summary.
- Reviewer result: score, best/weakest role performance, evidence gaps, logic
  jumps, ignored issues, and allow/reject/follow-up outcome.
- Final decision: exactly one recommendation with reasons, risks, next action,
  stop condition, and review point.

## Failure And Recovery

| Failure | Workflow | Required Recovery |
|---|---|---|
| Missing explicit command | `/room`, `/debate` | Suggest available commands; do not auto-enter. |
| Invalid or vague room topic | `/room` | Ask for a narrower topic; do not create partial room state. |
| Invalid speaker structure | `/room` | Return `invalid_speakers`; rerun selection or repair roster before writing state. |
| Room turn generation failure | `/room` | Do not partially write `conversation_log`; keep prior state. |
| Summary fields all empty | `/room -> /debate` | Refuse upgrade and ask user to run or repair `/summary`. |
| Empty candidate solutions | `/room -> /debate` | Refuse upgrade; ask for a concrete candidate path. |
| Handoff packet invalid | `/room -> /debate` | Do not call `/debate`; report schema/contract issue. |
| Review packet incomplete | `/debate` | Reviewer refuses final decision; run targeted supplement or block. |
| Reviewer score below threshold | `/debate` | Return follow-up or reject outcome, not final decision. |
| Provider env missing | validation | Report provider-live not configured; do not block local mainline. |

Recovery outputs must distinguish facts, inferences, uncertainties, and
recommendations when making multi-agent or multi-perspective claims.

## Claim-Safe Support Boundary

Current release claims are governed by `docs/release-candidate-scope.md` and
the release readiness tooling.

The repository may currently claim:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- checked-in protocol, prompt, skill, runtime bridge, fixture, and validation
  paths within the documented local-first scope

The repository must not claim:

- universal support for every local agent host
- OpenCode, Gemini CLI, Aider, Goose, or Cursor Agent host-live support before
  a matching validation row reports `live_passed`
- provider-live support before valid `.env.room` and `.env.debate` files exist
  and `chat_completions_live_validation.py` passes
- that fixture, mock-provider, wrapper, inventory, or config-readiness evidence
  is equivalent to real host-live or provider-live support

A passing `./rtw doctor` means the checked-in local-first scope is usable on the
machine. It does not mean every third-party CLI, paid account, or external
provider has passed live validation.

## Validation Hooks

Useful validation paths today:

```bash
./rtw doctor --quick
./rtw validate --schema schemas/room-session.schema.json --fixture tests/fixtures/room-session.valid.json
./rtw validate --schema schemas/debate-session.schema.json --fixture examples/fixtures/debate-session.valid.json
./rtw validate --schema schemas/debate-result.schema.json --fixture examples/fixtures/debate-result.valid.json
./rtw evidence
python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical --state-root /tmp/round-table-room-canonical
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py validate-canonical --state-root /tmp/round-table-debate-canonical
```

Schema files:

- `schemas/room-session.schema.json`
- `schemas/debate-session.schema.json`
- `schemas/debate-result.schema.json`
- `schemas/room-to-debate-handoff.schema.json`
