---
name: agent-builder-skill
description: |
  Local-first Agent Factory adapter for converting Nuwa-style generated skills into round-table-ready manifests, profiles, and registry entries.
---

# Agent Builder Skill

Agent Builder connects Nuwa-style generated skills to the Round Table Workspace
agent ecosystem.

It does not run `/room` or `/debate` by itself. It prepares candidate agents so
the selection layer can later decide whether they should enter a meeting.

## Explicit Commands

- `/agent-create <person or topic>`
- `/agent-import <skill-path>`
- `/agent-validate <agent-id or manifest-path>`
- `/agent-register <manifest-path>`
- `/agent-enable <agent-id>`
- `/agent-disable <agent-id>`

In the current backend slice, live Nuwa creation is not claimed. Use manifest,
profile, and registry validation paths first.

## Source Of Truth

- `docs/agent-factory-architecture.md`
- `config/agent-registry.json`
- `schemas/agent-manifest.schema.json`
- `schemas/agent-registry.schema.json`
- `schemas/agent-selection-request.schema.json`
- `.codex/skills/agent-builder-skill/WORKFLOW.md`
- `.codex/skills/agent-builder-skill/runtime/`
- `examples/agent-factory/`

The existing built-in runtime pool remains `agents/registry.json`. Agent
Factory's `config/agent-registry.json` is the custom/candidate library for new
or imported participants.

## Hard Boundaries

1. Do not claim live Nuwa execution unless a future runtime command actually
   runs and persists that evidence.
2. Do not inject a full persona `SKILL.md` into round-table context.
3. Round-table meetings should consume `roundtable-profile.md` and
   `agent.manifest.json` metadata.
4. People-like labels are cognitive lenses, not voice-imitation instructions.
5. New agents must not enter automatic selection until explicitly enabled.
6. Fixture and metadata validation are not host-live or provider-live support.

## Runtime Entry

Use:

```bash
python3 .codex/skills/agent-builder-skill/runtime/validate_agent_bundle.py ...
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py ...
```

The unified CLI also exposes:

```bash
./rtw agent list
./rtw agent validate
./rtw agent register <manifest>
./rtw agent enable <agent-id>
./rtw agent disable <agent-id>
```
