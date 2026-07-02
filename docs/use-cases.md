# Use Cases

Round Table Workspace is useful when an AI coding agent produced something that
looks plausible, but you still need a review step before trusting it.

## Fast Match

| Situation | Run | Decision you want |
|---|---|---|
| AI generated a feature or doc update | `./rtw ship-check "Should we merge this AI-generated feature?"` | `ship`, `revise`, or `reject` |
| A product idea is still vague | `./rtw room "What is the smallest useful MVP for this idea?"` | roles, tradeoffs, and next evidence |
| A launch claim may be too broad | `./rtw debate "Is this launch claim ready?"` | allow, reject, or follow-up |
| An architecture change sounds convincing | `./rtw debate "Should we refactor this now?"` | risks, counterarguments, and required proof |
| A team wants a repeatable AI review ritual | `./rtw doctor --quick` then `./rtw ship-check ...` | local evidence trail before trust |

## 1. Pre-Merge AI Code Review

Use this when an agent generated code, docs, or UI copy and the change looks
ready at first glance.

```bash
./rtw ship-check "Should we merge this AI-generated onboarding feature?"
```

What the review should surface:

- missing tests
- unsupported public claims
- vague success states
- maintainability risks
- the smallest useful next step

Good result: a clear `ship`, `revise`, or `reject` decision with evidence.

## 2. MVP Scope Review

Use this when a product idea is still ambiguous and one AI answer may collapse
too quickly into implementation.

```bash
./rtw room "What is the smallest useful MVP for this idea?"
```

What the review should surface:

- useful first user
- riskiest assumption
- smallest demo path
- evidence that would change the decision
- what not to build yet

Good result: a structured exploration trail and a handoff packet for later
decision review.

## 3. Launch Claim Check

Use this before publishing release notes, landing copy, or social posts that
describe support status.

```bash
./rtw debate "Is this launch claim ready?"
```

What the review should surface:

- fixture-backed claims that sound like live support
- historical evidence being treated as current
- provider or host support without fresh validation
- wording that needs to be softened

Good result: public wording that stays inside current evidence.

## 4. Architecture Tradeoff Review

Use this when an agent proposes a refactor, adapter, or workflow change that
sounds confident but could create maintenance drag.

```bash
./rtw debate "Should we introduce this adapter layer now?"
```

What the review should surface:

- real second use case or speculative abstraction
- migration cost
- rollback path
- test and fixture coverage needed before merge
- operational boundary

Good result: a decision that names the tradeoff instead of hiding it in code.

## 5. Team Review Ritual

Use this when a team wants a lightweight local habit before trusting generated
work.

```bash
./rtw doctor --quick
./rtw ship-check "Should we trust this AI-generated change?"
```

What the review should surface:

- whether the local workflow is healthy
- what evidence exists in the checkout
- what remains unverified
- whether the next step is to ship, revise, or stop

Good result: a repeatable review path that does not depend on a chat transcript.

## Claim Boundary

These use cases are local-first and fixture-backed unless fresh evidence says
otherwise. Do not describe wrappers, config preflight, or demos as host-live or
provider-live support without current validation.

Short version: no host-live or provider-live support is claimed without current
evidence.
