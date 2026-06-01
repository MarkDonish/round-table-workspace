# Contributing

Thanks for considering a contribution to Round Table Workspace.

This project is conservative about support claims. A fixture pass, wrapper
presence, or config preflight is not the same as host-live or provider-live
support. Please keep that boundary intact in code, docs, tests, and examples.

## Good First Contributions

- Improve README examples or demo transcripts.
- Add small CLI UX improvements with tests.
- Add schema fixtures or negative fixtures.
- Improve local-first validation messages.
- Add docs that clarify claim boundaries, setup, or troubleshooting.

## Development Setup

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
python -m pip install -e .
./rtw doctor --quick
python3 -m unittest discover -v
```

## Pull Request Checklist

Before opening a PR, include evidence for the current checkout:

```bash
python3 -m unittest discover -v
./rtw doctor --quick --quiet
./rtw release-check --include-fixtures --quiet
```

For behavior changes:

- Add or update tests first.
- Keep fixture-backed claims separate from live-host/provider claims.
- Update README or docs if the user-facing behavior changes.
- Prefer small PRs with a clear summary and verification section.

## Commit Style

Use conventional commits where possible:

```text
feat: add ship-check decision gate
fix: preserve claim boundary in release check
docs: clarify local-first setup
```

## Claim Boundary Rule

Do not write any of these unless fresh evidence supports them:

- "works with every local agent"
- "provider-live ready"
- "OpenCode/Gemini/Aider/Goose/Cursor host-live support"
- "production-ready on all machines"

Prefer precise language:

- "fixture-backed"
- "local-first"
- "validated on this host"
- "not host-live/provider-live unless evidence exists"
