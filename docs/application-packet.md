# Application Packet

This packet is a compact reviewer-facing summary for grant, credit, startup,
or open-source program applications that ask for an existing GitHub repository.

## Project

- Name: Round Table Workspace
- GitHub repository: https://github.com/MarkDonish/round-table-workspace
- Public demo: https://markdonish.github.io/round-table-workspace/
- Current release: v0.2.2-pages-launch-kit
- Primary positioning: Make your AI agents argue before they ship.

## What It Does

Round Table Workspace is a local-first decision layer for AI coding agents. It
turns ambiguous work into a structured review flow:

1. Explore a question with `/room`.
2. Escalate mature or risky decisions with `/debate`.
3. Run `ship-check` before trusting AI-generated work.
4. Preserve claim boundaries so the project does not overstate provider-live or
   host-live support.

## What reviewers can verify

Reviewers can inspect the repository and run the project without paid provider
setup for the local-first scope:

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw doctor --quick
./rtw launch-kit --json
./rtw ship-check "Should we merge this AI-generated feature?"
python3 -m unittest discover -v
```

Expected evidence:

- `docs/index.html` provides a static GitHub Pages launch surface.
- `docs/launch-copy.md` contains public launch copy.
- `docs/demo.html` provides a browser-friendly visual demo.
- `./rtw launch-kit --json` returns structured repo, demo, topics, and asset
  metadata.
- `./rtw release-check --include-fixtures` verifies the release-scope local
  checks.
- `tests/test_launch_surface.py` locks the public launch surface and packet
  into CI.

## Why It Is Relevant For Credits / Startup Programs

This repository is not an empty application shell. It already includes:

- a working CLI entrypoint (`./rtw`),
- a tested local-first workflow,
- public documentation,
- release notes,
- a demo-ready static landing page,
- CI-backed tests,
- explicit claim boundaries.

Credits would be used to move from fixture-backed local validation toward more
provider-live and host-live evaluation lanes, while preserving evidence-first
claims.

## Claim Boundary

No host-live or provider-live support is claimed by this packet. The currently
claimable surface is the checked-in, local-first, fixture-backed project scope
unless separate live validation evidence is produced.

## Reviewer Links

- Repository: https://github.com/MarkDonish/round-table-workspace
- Public demo target: https://markdonish.github.io/round-table-workspace/
- Release notes: https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.2.2-pages-launch-kit
