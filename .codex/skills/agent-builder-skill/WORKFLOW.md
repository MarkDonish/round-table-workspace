# Agent Builder Workflow

## Current Phase

Phase 1 implements the backend registry foundation:

1. Validate `agent.manifest.json`.
2. Validate `roundtable-profile.md`.
3. Register a manifest into `config/agent-registry.json`.
4. List, validate, enable, and disable registry entries.

It does not yet import Nuwa output automatically, run live Nuwa generation, or
wire custom agents into `/debate --pool`.

## Bundle Lifecycle

1. A candidate skill is created or imported.
2. Agent Builder produces a lightweight `roundtable-profile.md`.
3. Agent Builder produces `agent.manifest.json`.
4. `validate_agent_bundle.py` validates manifest and profile shape.
5. `agent_registry.py register` writes the manifest to `config/agent-registry.json`
   with status `registered`.
6. `agent_registry.py enable` moves the agent into the enabled candidate pool
   only when its local skill directory exists.
7. Later selection phases may consume enabled registry entries.

## Validation Rules

Before an agent can be enabled:

- manifest schema must pass
- profile required sections must exist
- `agent_id` must be unique in the registry
- `skill_name` should exist under `.codex/skills/` or `.claude/skills/`
- `style_rule`, `bias_risk`, and `counterweights` must be present
- `task_types`, `stage_fit`, `structural_role`, `expression`, and `strength`
  must stay inside controlled enums

## Claim Boundary

This workflow validates metadata and local files. It is not live Nuwa execution,
host-live execution, or provider-live execution.
