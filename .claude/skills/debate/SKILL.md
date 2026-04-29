---
name: debate
description: Explicit-only /debate round-table dispatcher for this repository. Use only when the user invokes /debate or when /room hands off a valid debate packet.
---

# /debate Project Skill Adapter

This is the Claude Code project-skill entry for `/debate`.

It is an adapter, not the canonical implementation source. The canonical `/debate` sources remain:

- `AGENTS.md`
- `.codex/skills/debate-roundtable-skill/SKILL.md`
- `.codex/skills/debate-roundtable-skill/runtime/README.md`
- `docs/debate-runtime-bridge.md`
- `docs/host-adapter-architecture.md`
- `docs/debate-skill-architecture.md`
- `docs/agent-role-map.md`
- `docs/reviewer-protocol.md`
- `docs/red-flags.md`
- `docs/room-to-debate-handoff.md`
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`
- `prompts/debate-followup.md`

If this file conflicts with those sources, follow those sources and report the mismatch.

## Trigger Boundary

Use this skill only for explicit debate mode:

- `/debate <topic>`
- `/debate --with ... <topic>`
- `/debate --without ... <topic>`
- `/debate --quick <topic>`
- a valid `/room` handoff packet accepted by the checked-in packet preflight

Do not use this skill for ordinary chat, `/room` exploration before upgrade, or single-agent advice.

## Operating Rules

1. Treat `/debate` as a round-table dispatcher and reviewer workflow, not as a personality.
2. Do not let participants modify runtime state directly.
3. Keep `/room` handoff one-way through the packet contract.
4. Do not consume historical `reports/` as current handoff input.
5. Do not use old Windows paths as runtime entry points.
6. Separate facts, inferences, uncertainty, and recommendations.
7. Do not fabricate reviewer approval. If review fails, return a blocked or follow-up state.

## Runtime Entry Points

For deterministic validation:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py \
  --executor fixture \
  --scenario reject_followup \
  --state-root /tmp/round-table-debate-e2e-followup
```

For Claude Code adapter-route validation without a Claude subscription:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --scenario reject_followup \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

For real Claude Code host-live validation, only if the local Claude Code account is entitled:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --preflight-only \
  --state-root /tmp/round-table-claude-code-live-preflight

python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --smoke-only \
  --state-root /tmp/round-table-claude-code-live-smoke

python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

If the live wrapper reports `claude_code_not_logged_in`, do not mark the lane as passed. A `--smoke-only` pass proves local CLI execution only; claim the default Claude Code lane only when the full wrapper reports `claimable_as_default_claude_code_host_live=true`.

<!-- rtw:generated-skill-summary:start -->

## Generated Skill Summary

- Skill id: `debate`
- Source schema: `0.1.0`
- Entry commands: `/debate <topic>`, `/debate --with Jobs,Taleb <topic>`, `/debate --quick <topic>`
- Shared rules: `explicit-only`, `local-first`, `claim-safe`, `do-not-use-reports-as-source`, `do-not-claim-fixture-as-live`, `cognitive-lens-not-voice-imitation`
- Claim boundary: fixture/checker passes are not host-live and not provider-live evidence.

Canonical refs:
- `AGENTS.md`
- `docs/protocol-spec.md`
- `docs/debate-skill-architecture.md`
- `docs/reviewer-protocol.md`
- `docs/decision-quality-rubric.md`
- `docs/room-to-debate-handoff.md`
- `schemas/debate-session.schema.json`
- `schemas/debate-result.schema.json`
- `schemas/room-to-debate-handoff.schema.json`
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`
- `prompts/debate-followup.md`

Host-specific notes:
- `codex`: Canonical checked-in debate runtime and skill entrypoint.
- `claude`: Project-skill adapter that points back to canonical Codex/docs sources.

<!-- rtw:generated-skill-summary:end -->
