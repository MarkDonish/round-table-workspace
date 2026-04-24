# Claude Code Project Layer

This directory provides Claude Code native project-skill discovery for the round-table repository.

It is not a fork of the implementation source.

Canonical sources remain:

- `AGENTS.md`
- `docs/`
- `prompts/`
- `.codex/skills/room-skill/`
- `.codex/skills/debate-roundtable-skill/`

Validate this layer without a Claude subscription:

```bash
python3 .claude/scripts/validate_project_skills.py
```

If this layer conflicts with canonical sources, fix the adapter layer and keep canonical sources authoritative.
