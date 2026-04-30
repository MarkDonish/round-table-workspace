# Agent Builder Workflow

This document describes the Agent Factory backend workflow.

## Phase 1 Workflow

1. Create or receive an `agent.manifest.json`.
2. Create or receive a matching `roundtable-profile.md`.
3. Run bundle validation.
4. Register the manifest in `config/agent-registry.json`.
5. Keep the candidate `registered` until explicitly enabled.

## Commands

```bash
python3 .codex/skills/agent-builder-skill/runtime/validate_agent_bundle.py \
  examples/agent-factory/duan-yongping.agent.manifest.json \
  --profile examples/agent-factory/duan-yongping.roundtable-profile.md

python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py list
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py validate
```

Equivalent CLI wrappers:

```bash
./rtw agent list
./rtw agent validate
./rtw agent register examples/agent-factory/duan-yongping.agent.manifest.json --replace
```

## Next Phase

Phase 2 should add `agent_builder.py` to import an existing Nuwa-generated skill
directory and deterministically produce the manifest/profile pair.
