# Demo Recording Guide

Use this guide to record a short visual demo for X, LinkedIn, newsletters, or a
repository README update.

For copy-ready 30-second and 60-second scripts, captions, and channel variants,
use `docs/short-video-script-kit.md`.

The goal is to show the workflow in motion: an AI-generated change looks
plausible, Round Table Workspace reviews it, and the output becomes
`ship`, `revise`, or `reject`.

## Recommended Format

| Channel | Length | Shape | Primary link |
|---|---:|---|---|
| X / Twitter | 30-45 seconds | terminal clip plus one caption | GitHub repo |
| LinkedIn | 45-60 seconds | terminal clip plus short context | Pages overview |
| Newsletter | 20-30 second GIF | one command and result | one-minute demo |
| README | static screenshot or short GIF | final `ship-check` output | GitHub repo |

## 45-Second Storyboard

| Time | Visual | Voiceover or caption |
|---:|---|---|
| 0-5s | Show the repo title or terminal in the checkout | "AI coding agents are fast. Sometimes too fast." |
| 5-12s | Run `./rtw ship-check "Should we merge this AI-generated feature?"` | "Before trusting generated work, run a quick review gate." |
| 12-25s | Show panel votes and the `revise` decision | "Product, engineering, risk, and user views make the hidden gaps visible." |
| 25-35s | Highlight risks / next actions | "The output is not more hype. It tells you what is missing." |
| 35-45s | Show repo URL or Pages overview | "Use it before the next generated feature ships." |

## Terminal Commands

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

For a deterministic demo path without provider setup:

```bash
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
```

## On-Screen Text

Keep the text sparse:

- "AI-generated work should not skip review"
- "`ship-check` returns ship / revise / reject"
- "Local-first demo path, no provider key required"
- "GitHub: MarkDonish/round-table-workspace"

## What To Show

Show:

- the command being run
- the decision line
- panel votes or named reviewer perspectives
- one concrete risk or missing evidence item
- the GitHub repo link

Avoid:

- claiming live host or provider support without fresh evidence
- implying the workflow guarantees correctness
- showing private tokens, `.env` files, local account details, or logs
- using a long scrolling transcript that viewers cannot read

## Caption Draft

```text
AI coding agents can produce a confident answer before the decision is ready.

Round Table Workspace adds a local review step:
/room explores
/debate reviews
ship-check returns ship / revise / reject

Repo: https://github.com/MarkDonish/round-table-workspace
```

## Claim Boundary

This guide is for recording a public demo of the fixture-backed local workflow.
It does not add host-live or provider-live support claims. Current support claims
must come from fresh repository evidence.
