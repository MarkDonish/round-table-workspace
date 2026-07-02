# AI Failure Modes This Catches

Round Table Workspace is easiest to understand through the failure modes it is
meant to slow down.

It does not guarantee correctness. It gives a local review step before a
confident AI answer becomes trusted work.

## Fast Map

| Failure mode | What it looks like | RTW surface to try | Better outcome |
|---|---|---|---|
| Confident but untested code | The patch compiles in the answer, but no real test path is named | `ship-check` | `revise` until tests, fixtures, or manual checks are clear |
| Product decision hidden inside code | The agent starts building before the product question is settled | `/room` | identify the smallest useful decision before implementation |
| Launch claim too broad | Copy says support exists without fresh evidence | `/debate` or `ship-check` | narrow the wording to verified evidence |
| Refactor with no second use case | The abstraction sounds clean but creates maintenance drag | `/debate` | name migration cost, rollback path, and proof needed |
| Chat transcript as evidence | The only record is a long chat nobody wants to audit | `ship-check --output-json` | local JSON / Markdown artifacts tied to the decision |
| Missing user or risk perspective | The answer optimizes for implementation speed only | `/room` then `/debate` | product, engineering, risk, and user-advocate views are visible |

## Example Prompts

Use these when you want to test whether the workflow fits your own project.

```bash
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw debate "Is this launch claim backed by current evidence?"
./rtw room "What is the smallest useful MVP before we build?"
./rtw debate "Should we introduce this adapter layer now?"
```

## What The Review Should Force

A useful round-table review should force the output to name:

- what is already verified
- what is still missing
- what risk matters most
- what next action is small enough to do now
- whether the decision is `ship`, `revise`, or `reject`

If the answer is still vague after that, the right result is usually `revise`.

## What This Does Not Replace

This workflow does not replace:

- unit tests
- static analysis
- human code review
- production monitoring
- security review for sensitive systems

It sits before those checks when the question is: "Should we trust this
AI-assisted work yet?"

## Claim Boundary

This guide does not add host-live or provider-live support claims. Fixture-backed
demos, wrappers, and config checks are not live host or provider validation.
Current support claims must come from fresh repository evidence.
