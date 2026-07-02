# One-Minute Demo

This is a fixture-backed local transcript for quickly understanding what Round
Table Workspace adds to an AI coding workflow. It is not host-live or
provider-live validation evidence.

## The Moment

An AI coding agent produced a feature that looks plausible. Before merging, run
one local decision gate:

```bash
./rtw ship-check "Should we merge this AI-generated feature?"
```

## What Comes Back

```text
Decision: revise
Confidence: medium

Panel:
- product: revise
- engineering: ship
- risk: revise
- user-advocate: revise

Summary:
Useful enough to continue, but revise positioning, evidence, and user-facing
examples before claiming it is launch-ready.
```

## Screenshot-Friendly Card

Use the Pages version when you need a clean screenshot for a launch post,
newsletter, README update, or team chat:

<https://markdonish.github.io/round-table-workspace/one-minute-demo.html>

The screenshot card keeps four things visible at once:

- the exact `ship-check` command
- the `Decision: revise` badge
- the product, engineering, risk, and user-advocate votes
- the GitHub repository URL and fixture-backed claim boundary

It is designed for a quick visual explanation, not as provider-live proof.

## Why Each Reviewer Voted That Way

| Reviewer | Vote | Reason |
|---|---|---|
| Product | `revise` | The user value should be stated as an observable outcome before shipping. |
| Engineering | `ship` | The change is small enough to ship when tests and local validation pass. |
| Risk | `revise` | Claim boundaries and rollback notes should be explicit before launch copy is promoted. |
| User advocate | `revise` | The public README should show a concrete before/after example, not only architecture language. |

## What It Catches

- Overclaiming host-live or provider-live behavior without fresh validation
  evidence.
- README positioning that stays too abstract for first-time visitors.
- A single-agent answer that misses product, risk, and user-readiness tradeoffs.

## What To Do Next

```text
1. Run ./rtw doctor --quick and the unit test suite.
2. Add one concrete demo transcript or screenshot to the README.
3. Keep public claims local-first unless host-live/provider-live evidence exists.
```

## What This Proves

This proves the shape of the local review gate:

- a single question enters the workflow
- multiple reviewer roles respond
- the output becomes `ship`, `revise`, or `reject`
- missing evidence and next actions are named directly

It does not prove that every generated feature is correct. It gives the team a
repeatable pre-merge review step before trusting a confident AI answer.
