# Reports

This directory stores historical project records rather than active source-of-truth files.

- `checkpoints/`: milestone notes, progress snapshots, handoff docs, validation summaries
- `sessions/`: session-by-session development reports
- `setup/`: repository setup and source-discovery notes

If a file is needed to run or evolve the system directly, it should probably live in `docs/`, `prompts/`, `examples/`, or `.codex/skills/` instead.

## How To Use This Directory

Use `reports/` for archaeology, evidence lookup, and old decision context.

Do not use files in this directory as:

- runtime entrypoints
- current protocol definitions
- current prompt source
- release-scope authority
- proof of live support without a matching checked-in validation command

If a historical report contains a still-valid rule, promote the rule into an
active source file first. The active source file should then be cited instead of
the report.

## Current Source-Of-Truth Pointers

Start from these files before using any report:

- `AGENTS.md`
- `README.md`
- `docs/source-truth-map.md`
- `docs/development-sync-protocol.md`
- `docs/release-readiness.md`
- `docs/release-candidate-scope.md`
- `docs/room-runtime-status.md`

Reports can support investigation, but they must not override those files.

## Boundary Audit

If a report name overlaps with an active source file, keep the report as
historical evidence and run:

```bash
python3 .codex/skills/room-skill/runtime/source_boundary_audit.py --output-json /tmp/round-table-source-boundary-audit.json
```

See `docs/historical-materials-audit.md` for interpretation rules.
