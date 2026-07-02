This is an illustrative transcript, not host-live or provider-live validation evidence.

# Demo: Reviewing An AI-Generated Feature Before Merge

This demo shows the moment Round Table Workspace is designed for: an AI coding
agent produced a confident change, and you need a review gate before trusting it.

## Scenario

An agent generated a new onboarding feature:

- adds a welcome checklist
- stores completion state in local storage
- updates the empty dashboard copy
- includes a short README note

The code looks plausible. The question is whether it should be merged.

## Command

```bash
./rtw ship-check "Should we merge this AI-generated onboarding feature?"
```

## Round-Table Review

| Reviewer | Focus | Finding |
|---|---|---|
| Product | Does this help the user finish onboarding? | Useful direction, but the first-run path is still vague. |
| Engineering | Is the implementation safe to merge? | Needs tests around local-storage fallback and reset behavior. |
| Risk | Could the change create hidden support issues? | Empty-state copy makes a support promise the app does not yet prove. |
| User advocate | Will a new user understand the next action? | Checklist labels are clearer than before, but success state is missing. |

## Decision

```text
Decision: revise
Confidence: medium
Why:
- useful feature shape
- missing test coverage around persisted state
- unclear success state for first-time users
- public copy should avoid claiming a completed onboarding flow

Next:
1. add tests for local-storage disabled, reset, and completed states
2. add a visible success state after the checklist is done
3. weaken the README copy from "guided onboarding" to "onboarding checklist"
4. rerun the project test suite before merge
```

## What Changed Because Of The Review

Without the review, the change might have shipped because it looked complete.

With the review, the merge decision becomes more precise:

- do not reject the feature
- do not merge it as-is
- revise the missing evidence and copy claims first

That is the practical value of the workflow: it turns one confident AI answer
into a small decision record with risks, missing evidence, and a next action.

## What This Demo Proves

This demo proves the repository's intended review pattern, not live host support.

It is safe to use as a mental model for:

- AI-generated feature review
- pre-merge decision gates
- launch-copy claim checks
- documentation changes that sound plausible but lack evidence

For current runtime support boundaries, use:

```bash
./rtw doctor --quick
./rtw release-check --include-fixtures
```
