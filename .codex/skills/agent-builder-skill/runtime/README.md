# Agent Builder Runtime

This runtime provides the first backend slice for Agent Factory.

It is local-first and does not call Nuwa, a host agent, or an external provider.
It validates metadata, profile shape, and registry state so later phases can
import generated skills and feed a selection engine.

## Commands

Validate a bundle:

```bash
python3 .codex/skills/agent-builder-skill/runtime/validate_agent_bundle.py \
  examples/agent-factory/duan-yongping.agent.manifest.json \
  --profile examples/agent-factory/duan-yongping.roundtable-profile.md
```

List the Agent Factory registry:

```bash
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py list
```

Validate the Agent Factory registry:

```bash
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py validate
```

Register a manifest into a temporary registry:

```bash
python3 .codex/skills/agent-builder-skill/runtime/agent_registry.py \
  --registry /tmp/agent-registry.json \
  register examples/agent-factory/duan-yongping.agent.manifest.json
```

## Boundary

This runtime validates Agent Factory metadata only. It does not claim live Nuwa
execution, host-live execution, provider-live execution, or automatic admission
into `/room` or `/debate`.
