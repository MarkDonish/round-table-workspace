# Credits Application Answers

This file contains copy-ready answers for credits, grant, startup, or open-source
program applications that ask for an existing GitHub repository and planned API
usage.

## Short project description

Round Table Workspace is a local-first decision layer for AI coding agents. It
helps Codex, Claude Code, and other CLI agents explore ambiguous questions,
debate risky decisions, and run a ship / revise / reject gate before trusting
AI-generated work.

The project already includes a working CLI, fixture-backed local workflows,
public docs, tests, release notes, and a static GitHub Pages launch surface.

## What problem are you solving?

AI coding agents are fast, but a single confident agent response can skip product
risk, missing evidence, user impact, and claim boundaries. Round Table Workspace
adds a structured review layer before shipping: `/room` for exploration,
`/debate` for decision review, and `ship-check` for a practical pre-ship gate.

## What will you use the credits for?

Credits would be used to move beyond fixture-backed local validation into more
realistic provider-live evaluation lanes while keeping evidence-first claims.
The main uses are:

1. Run provider-live regression tests across representative product and coding
   decision scenarios.
2. Compare model behavior across reviewer roles such as product, engineering,
   risk, and user advocate.
3. Measure whether multi-agent debate improves the quality of ship / revise /
   reject decisions over single-agent answers.
4. Build stronger evaluation artifacts that can be committed back to the repo.
5. Validate optional host-live integrations only when there is clear evidence
   and no over-claiming.

## Why do you need GPT Pro / API credits?

The current repository is intentionally conservative: it proves the local-first
and fixture-backed scope without requiring paid provider setup. GPT Pro or API
credits would let the project test real model behavior at higher volume and with
more realistic prompts, while preserving the current claim boundary.

## What have you already built?

- A working CLI entrypoint: `./rtw`
- `ship-check` for ship / revise / reject decisions
- Fixture-backed `/room` and `/debate` surfaces
- JSON and Markdown output modes
- Release checks and doctor checks
- Public launch copy and a static Pages landing page
- Reviewer-facing application packet
- CI-backed unit tests
- Explicit claim boundary documentation

## How can reviewers verify the repository?

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw doctor --quick
./rtw launch-kit --json
./rtw ship-check "Should we merge this AI-generated feature?"
python3 -m unittest discover -v
```

## Claim boundary

No host-live or provider-live support is claimed by this answer packet. The
currently claimable surface is the checked-in, local-first, fixture-backed
project scope unless separate live validation evidence is produced.

## Links

- GitHub repository: https://github.com/MarkDonish/round-table-workspace
- Application packet: https://github.com/MarkDonish/round-table-workspace/blob/main/docs/application-packet.md
- Reviewer checklist: https://github.com/MarkDonish/round-table-workspace/blob/main/docs/reviewer-checklist.md
- Release notes: https://github.com/MarkDonish/round-table-workspace/releases/tag/v0.2.2-pages-launch-kit
