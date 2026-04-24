---
name: room
description: Explicit-only /room stateful round-table dispatcher for this repository. Use only when the user invokes /room, /focus, /summary, /upgrade-to-debate, /add, or /remove, or is already continuing an active room.
---

# /room Project Skill Adapter

This is the Claude Code project-skill entry for `/room`.

It is an adapter, not the canonical implementation source. The canonical `/room` sources remain:

- `AGENTS.md`
- `.codex/skills/room-skill/SKILL.md`
- `.codex/skills/room-skill/WORKFLOW.md`
- `.codex/skills/room-skill/runtime/README.md`
- `docs/room-runtime-status.md`
- `docs/room-runtime-bridge.md`
- `docs/host-adapter-architecture.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-chat-contract.md`
- `docs/agent-registry.md`
- `docs/room-to-debate-handoff.md`
- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

If this file conflicts with those sources, follow those sources and report the mismatch.

## Trigger Boundary

Use this skill only for explicit room mode:

- `/room <topic>`
- `/focus <focus text>`
- `/summary`
- `/upgrade-to-debate`
- `/add <agent>`
- `/remove <agent>`
- continuation inside an already active `/room` context

Do not use this skill for ordinary chat, single-agent advice, or `/debate` unless `/room` is explicitly handing off through a packet.

## Operating Rules

1. Treat `/room` as a stateful orchestrator, not as a personality.
2. Keep the runtime bridge as the only state writer.
3. Do not let prompt files mutate room state directly.
4. Do not use `reports/` or `artifacts/` as active implementation source.
5. Do not require provider URLs for the local mainline.
6. Prefer repo-relative paths over machine-local absolute paths.
7. If the user wants to upgrade, pass only a valid handoff packet into `/debate`.

## Runtime Entry Points

For deterministic validation:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-e2e
```

For Claude Code adapter-route validation without a Claude subscription:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

For real Claude Code host-live validation, only if the local Claude Code account is entitled:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

If the live wrapper reports `claude_code_not_logged_in`, do not mark the lane as passed.
