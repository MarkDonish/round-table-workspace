# Launch Notes

This file contains the public launch copy for Round Table Workspace.

## One-Line Positioning

Make your AI coding agents argue before they ship.

## Short Description

Round Table Workspace is a local-first decision layer for Codex, Claude Code,
and other CLI agents. It turns vague product and engineering questions into
structured room exploration, debate review, and ship/revise/reject decisions
with evidence you can commit and audit.

## GitHub Topics

Suggested repository topics:

```text
ai-agents
multi-agent
codex
claude-code
developer-tools
local-first
decision-making
ai-coding
cli
python
agent-workflow
code-review
vibe-coding
openai
llm
```

## X / Twitter Launch Thread

AI coding agents are fast. Too fast.

They can build an MVP before anyone asks:

Should we build this at all?

So I built Round Table Workspace: a local-first round table where Codex,
Claude Code, and CLI agents debate before you ship.

What it does:

- `/room` explores ambiguous ideas
- `/debate` reviews risky decisions
- `ship-check` returns ship / revise / reject
- outputs JSON + Markdown evidence
- runs local-first, no provider required for the default demo

The idea is simple:

Stop letting one confident AI agent make every product and engineering decision.
Make the agents argue first.

Example:

```bash
./rtw ship-check "Should we merge this AI-generated feature?"
```

Output:

```text
Decision: revise
Panel: product, engineering, risk, user-advocate
Next: run tests, add a visible demo, keep claims local-first unless validated
```

Useful for:

- AI-generated code reviews
- MVP decisions
- architecture tradeoffs
- launch claim checks
- local-first agent workflow experiments

GitHub:
https://github.com/MarkDonish/round-table-workspace

If this helps your AI coding workflow, star it and try it before your next
AI-generated feature ships.

## Hacker News

Title:

Show HN: Round Table Workspace – local-first debate layer for AI coding agents

Body:

I built a local-first round-table decision layer for Codex, Claude Code, and
other CLI agents.

The motivation: AI coding agents are fast, but a single confident answer often
skips product risk, evidence, and claim boundaries. Round Table Workspace adds
`/room` for exploration, `/debate` for decision review, and `ship-check` for a
quick ship/revise/reject gate before trusting AI-generated work.

The current release is fixture-backed and conservative about claims: local-first
by default, no provider required for the demo, and no host-live/provider-live
claim without evidence.

Repo: https://github.com/MarkDonish/round-table-workspace

## Reddit / Community Post

I built a local-first debate layer for AI coding agents.

Instead of asking one AI agent whether a feature is ready, Round Table Workspace
runs a structured decision workflow:

- `/room` to explore a vague idea
- `/debate` to review a risky decision
- `ship-check` to return ship / revise / reject before merging
- JSON/Markdown artifacts for evidence

It is designed for Codex, Claude Code, and local CLI agent workflows. The demo
is fixture-backed and runs without provider setup.

Repo: https://github.com/MarkDonish/round-table-workspace
