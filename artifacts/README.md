# Artifacts

This directory stores generated or captured outputs rather than source-of-truth design files.

- `runtime/`: live run bundles and execution outputs
- `fixtures/`: JSON fixtures and test packets
- `rendered/`: exported HTML and PDF files

These files are useful for validation and historical reference, but they are not the primary place to edit system behavior.

## How To Use This Directory

Use `artifacts/` for:

- runtime evidence
- replay fixtures
- rendered exports
- generated validation outputs

Do not use files in this directory as:

- current protocol definitions
- current prompt source
- runtime implementation source
- release-scope authority
- proof of live support unless the matching validation report says the live lane
  passed

Generated runtime output should normally stay uncommitted. Commit an artifact
only when it is intentionally promoted into a durable fixture, rendered export,
or human-reviewed evidence file.

## Current Source-Of-Truth Pointers

Before editing behavior, start from:

- `AGENTS.md`
- `README.md`
- `docs/source-truth-map.md`
- `.codex/skills/room-skill/runtime/README.md`
- `.codex/skills/debate-roundtable-skill/runtime/README.md`

If an artifact reveals a real behavior change, update the active source files
and validation commands. Do not patch the artifact as the fix.

## Boundary Audit

If an artifact name overlaps with an active source file, keep the artifact as
runtime evidence or fixture material and run:

```bash
python3 .codex/skills/room-skill/runtime/source_boundary_audit.py --output-json /tmp/round-table-source-boundary-audit.json
```

See `docs/historical-materials-audit.md` for interpretation rules.
