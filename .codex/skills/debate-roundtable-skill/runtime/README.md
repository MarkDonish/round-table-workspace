# /debate Runtime

This directory contains the checked-in debate-side runtime bridge.

It currently does 5 concrete jobs:

- validate `/room -> /debate` handoff packets before `/room` persists acceptance
- build debate launch bundles plus checked-in roundtable/reviewer artifacts for host wiring
- validate one checked-in reject -> followup -> re-review loop for debate-side host wiring
- run one fixture-backed `/debate` prompt-host E2E validation flow
- run one Chat Completions-compatible `/debate` prompt-host E2E validation flow against a local or external provider

It still does not execute a live multi-agent `/debate` run by itself.

## Main Entry

Run:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py --help
```

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py --help
```

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py --help
```

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py --help
```

Validate one persisted handoff packet:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py \
  --packet-json artifacts/runtime/rooms/<room_id>/handoff/packet-turn-002.json
```

Build a launch bundle from that packet:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  build-launch-bundle \
  --packet-json artifacts/runtime/rooms/<room_id>/handoff/packet-turn-002.json
```

Build a reviewer template from a launch bundle:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  build-review-template \
  --launch-bundle-json artifacts/runtime/debates/<debate_id>/launch/launch-bundle.json
```

Validate one completed roundtable record against a launch bundle:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-roundtable-record \
  --roundtable-json artifacts/runtime/debates/<debate_id>/roundtable/roundtable-record.json \
  --launch-bundle-json artifacts/runtime/debates/<debate_id>/launch/launch-bundle.json
```

Build a reviewer packet from a validated roundtable record:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  build-review-packet \
  --roundtable-json artifacts/runtime/debates/<debate_id>/roundtable/roundtable-record.json \
  --launch-bundle-json artifacts/runtime/debates/<debate_id>/launch/launch-bundle.json
```

Validate one reviewer result against a reviewer packet:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-review-result \
  --review-result-json artifacts/runtime/debates/<debate_id>/review/review-result.json \
  --review-packet-json artifacts/runtime/debates/<debate_id>/review/review-packet.json
```

Validate one followup record against a rejected reviewer result:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-followup-record \
  --followup-json artifacts/runtime/debates/<debate_id>/followup/followup-record.json \
  --review-result-json artifacts/runtime/debates/<debate_id>/review/review-result.reject.json \
  --review-packet-json artifacts/runtime/debates/<debate_id>/review/review-packet.json
```

Build a re-review packet after one checked-in followup round:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  build-rereview-packet \
  --followup-json artifacts/runtime/debates/<debate_id>/followup/followup-record.json \
  --review-result-json artifacts/runtime/debates/<debate_id>/review/review-result.reject.json \
  --review-packet-json artifacts/runtime/debates/<debate_id>/review/review-packet.json
```

Validate the checked-in canonical debate-side bridge:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-canonical \
  --state-root /tmp/round-table-debate-runtime
```

Validate the checked-in canonical execution chain:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-canonical-execution \
  --state-root /tmp/round-table-debate-execution
```

Validate the checked-in canonical reject-followup-rereview chain:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py \
  validate-canonical-followup \
  --state-root /tmp/round-table-debate-followup
```

Run the fixture-backed `/debate` E2E allow path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor fixture \
  --scenario allow \
  --state-root /tmp/round-table-debate-e2e-allow
```

Run the fixture-backed `/debate` E2E reject-followup path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor fixture \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-e2e-followup
```

Run the local mock-provider `/debate` E2E path:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py --port 32124

DEBATE_CHAT_COMPLETIONS_URL=http://127.0.0.1:32124/v1/chat/completions \
DEBATE_CHAT_COMPLETIONS_MODEL=mock-debate-model \
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor chat_completions \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-mock-followup
```

Run the real provider path:

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

## Output Shape

The packet validator prints a JSON acceptance object with:

- `accepted`
- `checked_against`
- `reason`
- `starting_agents`
- `default_agents_for_type`
- `packet_balance`
- `debate_reselection_required`
- `warnings`

`/room` persists that acceptance object to:

`artifacts/runtime/rooms/<room_id>/handoff/debate-acceptance.json`

The debate runtime writes debate-side artifacts under:

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
- `followup/followup-record.json`
- `followup/followup.validation.json`
- `followup/rereview-packet.json`
- `followup/rereview-packet.validation.json`
- `followup/review-result.allow.json`
- `followup/review-result.allow.validation.json`
- `prompt-calls/*.input.json`
- `prompt-calls/*.output.json`
- `prompt-calls/*.meta.json`
- `validation-report.json`

## Boundary

This runtime closes 3 specific gaps:

- `/room` no longer relies on a plain-text grep over `debate-roundtable-skill/SKILL.md`
- `/debate` now has a checked-in execution bridge for launch bundle -> roundtable record -> review packet -> review result -> followup record -> rereview packet -> final review result
- `/debate` now has a checked-in prompt-host E2E runner plus a local mock provider for provider-backed regression

It does not close the final live gap:

- a real prompt host still must execute `prompts/debate-roundtable.md`
- a real reviewer still must pass or reject live debate outputs
- a real prompt host still must execute `prompts/debate-followup.md` and feed the second review back into a live reviewer

The local mock-provider path proves the host wiring.
It does not count as a real external provider pass.
