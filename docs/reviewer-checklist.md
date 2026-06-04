# Reviewer Checklist

A compact review path for credits, grant, startup, or open-source program reviewers who need to decide whether this repository is real, runnable, and relevant.

## 2-minute review path

1. Open the public launch page:
   https://markdonish.github.io/round-table-workspace/
2. Inspect the repository:
   https://github.com/MarkDonish/round-table-workspace
3. Read the application packet:
   docs/application-packet.md
4. Read the copy-ready credits answers:
   docs/credits-application-answers.md
5. Run the local verification commands below.

## Local verification commands

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw doctor --quick
./rtw launch-kit --json
./rtw ship-check "Should we merge this AI-generated feature?"
python3 -m unittest discover -v
```

## Evidence matrix

| Reviewer question | Where to check | Expected evidence |
| --- | --- | --- |
| Is this an existing public repository? | GitHub repository | Public repo with CLI, docs, tests, and release notes |
| Is there a public surface? | `docs/index.html` and GitHub Pages | Static launch page served from `main` `/docs` |
| Can it run without paid provider setup? | `./rtw doctor --quick` and tests | Fixture-backed local validation succeeds |
| Is there a concrete workflow? | `./rtw ship-check ...` | ship / revise / reject decision gate output |
| Is the application copy prepared? | `docs/credits-application-answers.md` | Copy-ready answers for credits forms |
| Are claims bounded? | Application packet and checklist | No host-live or provider-live over-claiming |

## What is already built

- Working CLI entrypoint: `./rtw`
- Local-first `/room`, `/debate`, and `ship-check` flows
- JSON and Markdown output modes
- GitHub Pages launch surface
- Browser-friendly visual demo
- Reviewer-facing application packet
- Credits application answer packet
- CI-backed unit tests
- Conservative claim boundaries

## What credits would unlock

Credits would fund provider-live evaluation work that the repository intentionally does not claim yet:

1. Run model-backed regression tests on representative product and coding decisions.
2. Compare single-agent answers against structured round-table reviews.
3. Measure decision quality across product, engineering, risk, and user-advocate roles.
4. Commit evaluation artifacts and claim evidence back to the repository.
5. Validate optional host-live integrations only after evidence exists.

## Claim boundary

No host-live or provider-live support is claimed by this checklist. The currently claimable surface is the checked-in, local-first, fixture-backed project scope unless separate live validation evidence is produced.
