This is an illustrative transcript, not host-live or provider-live validation evidence.

# Transcript: `ship-check` Architecture Decision

This example shows the shape of a fast `ship-check` review before accepting an
AI-generated architecture change. It is hand-written to demonstrate the
decision gate and should not be read as output from a live host, provider, or
release validation run.

Topic: Should we add a generic provider adapter layer now?

## Scenario

An AI coding agent proposes a new adapter layer:

- one interface for OpenAI-compatible providers
- one config file for provider routing
- one fallback path when a provider call fails
- one set of docs saying future providers can plug in easily

The proposal sounds useful, but the repository currently has only one
validated local-first path and no fresh provider-live evidence.

## Command

```bash
./rtw ship-check "Should we add a generic provider adapter layer now?"
```

## Round-Table Review

| Reviewer | Focus | Finding |
|---|---|---|
| Product | Does this help the next user now? | The next user mostly needs the local demo and clear claim boundaries. |
| Engineering | Is the abstraction justified? | One real provider path is not enough to justify a broad adapter layer. |
| Risk | Could this make support claims too broad? | Yes. The docs could imply provider-live support before evidence exists. |
| Maintainer | What will this cost later? | More config and fallback paths increase test and support surface. |

## Decision

```text
Decision: revise
Confidence: medium
Why:
- the direction may become useful after a second real provider path exists
- current evidence only supports local-first fixture-backed behavior
- a generic adapter would create a larger maintenance surface now
- docs must not imply provider-live support without fresh validation

Next:
1. keep the current local-first path as the default
2. write down the provider adapter contract as a narrow design note
3. add one negative fixture for overbroad provider claims
4. require fresh provider-live evidence before enabling or marketing it
```

## What Changed Because Of The Review

Without the review, the adapter might have shipped because it sounded like good
architecture.

With the review, the decision becomes smaller and avoids premature abstraction:

- do not reject the idea forever
- do not merge a generic adapter now
- capture the contract as a design note
- wait for a second real provider path before broadening the runtime

That is the practical value of `ship-check`: it turns "this abstraction sounds
clean" into a concrete `revise` decision with evidence requirements.

## What This Transcript Demonstrates

- `ship-check` can review architecture decisions, not only feature merges.
- A `revise` decision can preserve an idea without accepting premature scope.
- Claim boundaries are part of architecture review when provider or host
  support is involved.
- The output is useful even when the final answer is "not yet."

## Claim Boundary

This transcript does not add provider-live support. It does not prove any
provider adapter works on this machine or any other machine.

For current runtime support boundaries, use:

```bash
./rtw doctor --quick
./rtw release-check --include-fixtures
```
