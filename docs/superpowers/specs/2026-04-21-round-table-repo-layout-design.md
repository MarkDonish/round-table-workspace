# Round Table Repo Layout Design

**Date:** 2026-04-21

## Goal

Turn this repository into a long-term source-of-truth workspace that is usable from Windows, Mac, and Codex Cloud without depending on machine-specific home-directory layout.

## Approved layout

- Root keeps only repository entrypoints and active source directories.
- `docs/` keeps architecture, routing, protocol, and design documents.
- `prompts/` keeps system prompt files.
- `examples/` keeps examples.
- `.codex/skills/` keeps round-table skill files and agent roundtable profiles.
- `reports/` keeps historical handoff, validation, progress, session, and setup records.
- `artifacts/` keeps runtime outputs, fixtures, and rendered exports.

## Move rules

### Root should keep

- `README.md`
- `AGENTS.md`
- `.gitignore`
- `.codex/`
- `docs/`
- `prompts/`
- `examples/`
- `reports/`
- `artifacts/`

### Move into `reports/`

- historical handoff / next-step / progress / validation / round-table reports
- `SESSION-*.md`
- setup and discovery notes

### Move into `artifacts/`

- runtime JSON bundles
- fixture JSON files
- rendered HTML / PDF outputs

## Compatibility rule

Project-facing docs should use repo-relative paths and repo-local skill references instead of `C:\Users\CLH\...` style absolute paths whenever practical.
