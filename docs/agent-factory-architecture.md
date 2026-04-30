# Agent Factory Architecture

Agent Factory is the backend path for adding new round-table participants
without turning the existing `/room` and `/debate` runtime into a prompt dump.

## Position

The intended pipeline is:

```text
Nuwa-style skill output
-> Agent Builder Adapter
-> agent.manifest.json
-> roundtable-profile.md
-> config/agent-registry.json
-> selection engine
-> /room or /debate runtime
```

This phase implements the registry foundation only. It does not claim live Nuwa
execution, provider-live execution, or automatic participation in meetings.

## Registry Split

There are now two registry layers:

- `agents/registry.json`: checked-in built-in runtime pool currently consumed by
  existing `/room` and `/debate` bridges.
- `config/agent-registry.json`: Agent Factory custom/candidate library for
  Nuwa-style or imported participants.

The split keeps the existing runtime stable while making generated candidates
reviewable before they enter selection.

## Agent Bundle

A round-table-ready agent bundle has:

```text
agent.manifest.json
roundtable-profile.md
SKILL.md
references/
```

The meeting runtime should use `agent.manifest.json` plus
`roundtable-profile.md`, not the full `SKILL.md` body.

## Status Lifecycle

| Status | Meaning |
|---|---|
| `draft` | Candidate exists but is not registry-ready. |
| `registered` | Manifest/profile validation passed and the candidate is in the library. |
| `enabled` | Candidate may enter selection; local skill directory must exist. |
| `disabled` | Candidate remains stored but cannot be selected. |

New Agent Factory entries should normally start as `registered`. They should
only become `enabled` after explicit user or CLI action.

## Current Runtime Commands

Validate an agent bundle:

```bash
python3 .codex/skills/agent-builder-skill/runtime/validate_agent_bundle.py \
  examples/agent-factory/duan-yongping.agent.manifest.json \
  --profile examples/agent-factory/duan-yongping.roundtable-profile.md
```

List and validate the Agent Factory registry:

```bash
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py list
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py validate
```

The unified CLI mirrors the same local metadata operations:

```bash
./rtw agent list
./rtw agent validate
./rtw agent register examples/agent-factory/duan-yongping.agent.manifest.json --replace
```

## MVP Boundary

Supported now:

- manifest schema validation
- profile required-section validation
- registry list/validate/register/enable/disable
- sample Duan Yongping lens manifest and profile
- local CLI bridge under `./rtw agent`

Not supported yet:

- live Nuwa creation
- automatic import from arbitrary Nuwa output
- dynamic `/debate --pool`
- `/room /add` lookup through the custom registry
- local web UI

Fixture, metadata, and registry validation must not be described as host-live or
provider-live support.
