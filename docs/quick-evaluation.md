# Quick Evaluation Path

Use this page when you only have a few minutes to decide whether Round Table
Workspace is worth starring, trying, or sharing with another developer.

## 5-Minute Local Trial

From a fresh clone:

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

No provider key is required for this default path.

Expected JSON shape:

```json
{
  "decision": "revise",
  "panel_votes": [
    {"agent": "product", "vote": "revise"},
    {"agent": "engineering", "vote": "ship"},
    {"agent": "risk", "vote": "revise"},
    {"agent": "user-advocate", "vote": "revise"}
  ],
  "next_actions": [
    "Run ./rtw doctor --quick and the unit test suite."
  ]
}
```

If that is the pause you want before trusting generated work, star the repo and
try it before your next AI-generated feature, launch note, architecture change,
or agent-written document ships.

## What To Look For

The useful signal is not that another agent says "yes." The useful signal is
whether the workflow slows down a confident AI answer and gives you a concrete
next decision.

You should see:

- a `ship`, `revise`, or `reject` decision
- product, engineering, risk, and user-facing review angles
- missing evidence called out plainly
- next steps that are small enough to act on
- local artifacts you can keep with the repository

## Star If

Star the repo if at least one of these is true for your workflow:

- you use AI coding agents and want a pre-merge review habit
- you want a local-first alternative to trusting one confident chat answer
- you need a repeatable way to say `revise` before generated work ships
- you want claim boundaries to stay tied to current evidence
- you are experimenting with Codex, Claude Code, or other CLI agent workflows

## Skip For Now If

This repo is probably not the right thing to star yet if you need:

- a hosted SaaS dashboard
- universal live support for every local agent host
- provider-live execution without configuring and validating a provider lane
- a replacement for tests, security review, or human ownership

Those are intentionally outside the current public claim unless fresh evidence
proves the lane.

## Next Useful Links

- One-minute demo: <https://markdonish.github.io/round-table-workspace/one-minute-demo.html>
- AI feature review example: <https://markdonish.github.io/round-table-workspace/ai-generated-feature-review-demo.html>
- Use cases: <https://markdonish.github.io/round-table-workspace/use-cases.html>
- Why star this repo: [docs/why-star-this-repo.md](why-star-this-repo.md)
- Comparison guide: [docs/comparison-guide.md](comparison-guide.md)
