# Skill Generation

> Purpose: explain how Codex and Claude skill entrypoints stay aligned without
> turning host adapters into separate protocol sources.

## Source Files

Skill summary source lives under `skills_src/`:

- `skills_src/shared_rules.json`
- `skills_src/room.skill.json`
- `skills_src/debate.skill.json`

These files are strict JSON so the generator can run with only the Python
standard library. If an old `.yaml` manifest remains in `skills_src/`, the
generator reports a migration warning instead of silently treating it as source.

## Commands

Preview generated sections:

```bash
python3 scripts/generate_skills.py dry-run
```

Update generated summary sections:

```bash
python3 scripts/generate_skills.py generate
```

Check drift:

```bash
python3 scripts/generate_skills.py check
python3 scripts/check_skill_drift.py
```

## Boundary

The generator owns only the normalized generated summary section between:

```text
<!-- rtw:generated-skill-summary:start -->
<!-- rtw:generated-skill-summary:end -->
```

It does not replace the full `SKILL.md` body. Host-specific sections remain
manual until the adapter contracts are stable enough to generate completely.

Fixture/checker passes are not host-live or provider-live evidence.
