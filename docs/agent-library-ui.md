# Agent Library UI Notes

The UI is a later phase. This document records the intended data contract so
backend work does not drift.

## Views

- Agent Library: list agents from `config/agent-registry.json`.
- Agent Builder: create or import candidate bundles.
- Meeting Setup: choose `auto`, `manual_pool`, or `forced` selection mode.
- Meeting Room: display runtime session output after selection is complete.

## Backend Contract

The UI should call local APIs or CLI wrappers that ultimately use:

- `schemas/agent-manifest.schema.json`
- `schemas/agent-registry.schema.json`
- `schemas/agent-selection-request.schema.json`
- `.codex/skills/agent-builder-skill/runtime/agent_registry.py`

UI state should map to selection semantics:

| UI state | Selection meaning |
|---|---|
| unchecked | not in candidate pool |
| checked | candidate pool member |
| locked | pinned agent |
| excluded | excluded agent |

## Boundary

The UI must not treat a generated profile as meeting participation. Selection
and runtime validation still decide who enters `/room` or `/debate`.
