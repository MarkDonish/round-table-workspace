# /debate Runtime Preflight

This directory contains the checked-in executable preflight for `/room -> /debate` handoff packets.

It does not execute a live multi-agent `/debate` run.
Its job is narrower:

- validate the `docs/room-to-debate-handoff.md` packet shape
- validate the suggested candidate pool against `docs/agent-registry.md`
- surface balance warnings that `/debate` must respect during reselection
- provide a checked-in runtime acceptance artifact that `/room` can call before persisting a handoff

## Main Entry

Run:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py --help
```

Validate one persisted handoff packet:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py \
  --packet-json artifacts/runtime/rooms/<room_id>/handoff/packet-turn-002.json
```

## Output Shape

The validator prints a JSON acceptance object with:

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

## Boundary

This runtime closes one specific gap:

- `/room` no longer relies on a plain-text grep over `debate-roundtable-skill/SKILL.md`

It does not close the final live gap:

- a real multi-agent `/debate` execution chain is still a separate validation target
