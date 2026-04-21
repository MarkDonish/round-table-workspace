# /debate Runtime

This directory contains the checked-in debate-side runtime bridge.

It currently does 2 concrete jobs:

- validate `/room -> /debate` handoff packets before `/room` persists acceptance
- build debate launch bundles plus checked-in roundtable/reviewer artifacts for host wiring

It still does not execute a live multi-agent `/debate` run by itself.

## Main Entry

Run:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py --help
```

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_runtime.py --help
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
- `validation-report.json`

## Boundary

This runtime closes 2 specific gaps:

- `/room` no longer relies on a plain-text grep over `debate-roundtable-skill/SKILL.md`
- `/debate` now has a checked-in execution bridge for launch bundle -> roundtable record -> review packet -> review result

It does not close the final live gap:

- a real prompt host still must execute `prompts/debate-roundtable.md`
- a real reviewer still must pass or reject live debate outputs
