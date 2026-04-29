# Decision Quality Rubric

> Purpose: provide a machine-checkable quality standard for `/room`,
> `/debate`, and `/room -> /debate` outputs.
> Status: active validation source for v0.2.0.

This rubric evaluates whether a round-table output improves the user's decision
quality. It does not prove host-live or provider-live support.

## Scoring Model

Each dimension is scored from `0` to `2`.

| Score | Meaning |
|---|---|
| `0` | Missing, vague, or misleading. |
| `1` | Present but incomplete, weakly evidenced, or hard to act on. |
| `2` | Clear, specific, evidence-aware, and actionable. |

A strong result usually scores at least `10/14` with no `0` on
`uncertainty_disclosure` or `next_testable_step`.

## Dimensions

### problem_reframing

Checks whether the workflow restated the user's question into a decision-ready
form without changing its meaning.

- Pass: "The decision is whether to run a seven-day validation, not whether to
  build a full AI tutor."
- Fail: "This is a great AI opportunity" without narrowing the actual decision.

### key_variables

Checks whether the output names the variables that would change the decision.

- Pass: target student segment, repeated study frequency, retention threshold,
  acquisition channel, and quality-control cost.
- Fail: "Market demand, product quality, and execution" without concrete
  variables or thresholds.

### assumption_separation

Checks whether facts, inferences, assumptions, uncertainties, and
recommendations are separated.

- Pass: "Fact: no live student data yet. Assumption: students will repeat the
  workflow. Recommendation: test before building."
- Fail: "Students need this, so build it" when the need has not been validated.

### opposition_quality

Checks whether the opposing view is substantive, not decorative.

- Pass: risk-side argument explains why exam-week demand may be a false signal.
- Fail: "There are risks" without naming a mechanism or consequence.

### risk_to_action

Checks whether identified risks become mitigation, kill rules, or next checks.

- Pass: "If fewer than three students voluntarily repeat in seven days, stop."
- Fail: "Be careful about retention" without a measurable action.

### next_testable_step

Checks whether the output contains a next step that can be executed and reviewed.

- Pass: "Interview five students, choose one bottleneck, define thresholds, and
  run one seven-day cohort."
- Fail: "Do more research" or "build an MVP" without scope and review point.

### uncertainty_disclosure

Checks whether unknowns are explicitly named and not smoothed over.

- Pass: "First segment, acquisition channel, and frequency are still unknown."
- Fail: confident final language with no missing evidence or uncertainty list.

## Reviewer Usage

The `/debate` reviewer should include a rubric summary in full mode:

```json
{
  "rubric_scores": {
    "problem_reframing": 2,
    "key_variables": 1,
    "assumption_separation": 2,
    "opposition_quality": 2,
    "risk_to_action": 2,
    "next_testable_step": 2,
    "uncertainty_disclosure": 1
  },
  "total": 12,
  "blocking_dimensions": []
}
```

Any dimension scored `0` must be named in `required_followups`. A result should
not be marked `allow` if `next_testable_step` or `uncertainty_disclosure` is
`0`.
