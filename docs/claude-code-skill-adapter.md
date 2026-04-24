# Claude Code Skill Adapter

This document is the source of truth for the repository's Claude Code project-skill compatibility layer.

## Goal

Claude Code users should be able to clone this repository and have native project-skill entry points for `/room` and `/debate`, without treating Codex-specific `.codex/skills/` paths as the only discoverable skill surface.

## Project Skills

| Skill | Claude Code path | Canonical source |
|---|---|---|
| `/room` | `.claude/skills/room/SKILL.md` | `.codex/skills/room-skill/SKILL.md` |
| `/debate` | `.claude/skills/debate/SKILL.md` | `.codex/skills/debate-roundtable-skill/SKILL.md` |

The `.claude/skills/` files are adapters. They must stay small and point back to the canonical docs, prompts, and runtime bridges.

## Validation

For the full clone-friendly consumer self-check, including Claude Code project
skill structure validation without a subscription, run:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

Run this offline validation without a Claude subscription:

```bash
python3 .claude/scripts/validate_project_skills.py
```

This checks:

- project skill files exist
- frontmatter has the expected `name` and non-empty `description`
- required canonical source references are present
- key guardrails are present
- referenced canonical source files exist

Run adapter-route validation without a Claude subscription:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

Run real Claude Code host-live validation only when the local account has Claude Code entitlement:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

If the wrapper reports `claude_code_not_logged_in`, the adapter remains prepared but the host-live lane is blocked by account entitlement/authentication.

## Boundary

- `.claude/skills/` is a discovery and invocation layer for Claude Code.
- `.codex/skills/`, `docs/`, `prompts/`, and runtime files remain canonical implementation source.
- The Claude Code adapter must not drift into a forked protocol.
- Reports and artifacts are evidence, not active source.
