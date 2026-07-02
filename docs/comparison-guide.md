# Comparison Guide

Use this page when someone asks what Round Table Workspace replaces, what it
does not replace, and when it is worth adding to an AI coding workflow.

## Short Answer

Round Table Workspace is not a full agent runtime, model SDK, IDE plugin, or CI
system.

It is a local-first review layer that sits before you trust generated work. It
turns one confident AI answer into a small decision panel, then gives you a
`ship`, `revise`, or `reject` result with risks and next steps.

## What It Is Best Compared To

| Alternative | What it is good at | Where Round Table Workspace fits |
|---|---|---|
| One direct AI agent answer | Fast generation, coding, drafting, and iteration | Adds a review step before the answer becomes trusted work |
| Manual code review checklist | Human judgment and project context | Produces a structured first-pass decision record before review |
| Multi-agent framework | Building or orchestrating agent systems | Keeps the scope narrower: decide whether work is ready |
| CI / test suite | Proving code still passes known checks | Surfaces product, risk, evidence, and claim-boundary gaps |
| Chat transcript | Flexible exploration | Creates local JSON / Markdown artifacts that can be audited |

## Use Round Table Workspace When

- an AI coding agent produced work that sounds plausible but needs review
- a product or engineering question is still vague
- a launch claim needs evidence before it goes public
- a team wants a repeatable pre-merge decision gate
- a maintainer wants local artifacts instead of a long chat transcript

The fastest local check is:

```bash
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

## Do Not Use It When

- you only need an agent to write or edit code as fast as possible
- a standard unit test or linter already answers the question
- you need hosted production orchestration across many accounts
- you need verified live support for a host or provider that is not currently
  marked as live-passed in the repository evidence

## The Decision Boundary

The project is designed around one narrow question:

```text
Should this AI-assisted work be trusted yet?
```

The answer should be practical:

- `ship`: enough evidence exists to proceed
- `revise`: the direction is useful, but risks or evidence gaps remain
- `reject`: the current work should stop or be reframed

That is different from asking an agent to generate more output. Round Table
Workspace is useful when the next step should be judgment, not more text.

## How To Explain It In One Sentence

Round Table Workspace makes AI coding agents argue before they ship, then leaves
you a local decision record.

## Claim Boundary

This guide does not add any host-live or provider-live support claim. Fixture
demos, wrappers, and config checks are not described as live host or live
provider validation. Current support claims must come from fresh repository
evidence.
