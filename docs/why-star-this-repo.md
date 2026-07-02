# Why Star This Repo

Round Table Workspace is for people who use AI coding agents and still want a
real review step before trusting the output.

## The Problem

AI coding agents can produce a polished answer before the decision has been
tested.

That is useful, but it creates a failure mode:

- the answer sounds confident
- the risks are not surfaced
- the evidence is scattered in a chat transcript
- the next action is vague
- the work moves forward because it looks complete

Round Table Workspace adds a local review protocol before that happens.

## What It Adds

The repository provides three linked surfaces:

| Surface | Use it when | What you get |
|---|---|---|
| `/room` | The question is still ambiguous | selected roles, structured exploration, summary, handoff packet |
| `/debate` | A decision needs review | round-table discussion, reviewer checks, allow/reject/follow-up result |
| `ship-check` | You need a fast pre-merge gate | `ship`, `revise`, or `reject` with risks and next steps |

The default path is local-first and fixture-backed. You can try the demo without
provider keys.

The plain-English mechanism:

1. Create reviewer candidates for the topic or AI-generated change.
2. Keep the reviewers that add useful signal.
3. Bring them into a round-table debate.
4. Return `ship`, `revise`, or `reject` with risks, missing evidence, and next steps.

## A 60-Second Trial

From a fresh clone:

```bash
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

If that flow matches a problem you have, star the repo and try it before your
next AI-generated feature, launch note, architecture change, or agent-written
document ships.

## What This Repo Is Not Claiming

This project is intentionally conservative about support claims.

It does not claim universal host-live or provider-live support without current
evidence. Fixture-backed support, wrappers, and config checks are kept separate
from live host/provider validation.

That boundary is part of the value: the repo is designed to keep AI-assisted
work honest about what has actually been verified.
