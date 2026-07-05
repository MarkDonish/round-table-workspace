# Launch Notes

This file contains the public launch copy for Round Table Workspace.

For reusable community blurbs, channel angles, and claim-safe sharing guidance,
see `docs/community-share-kit.md`.

For a 5-minute local trial and star decision path for new visitors, see
`docs/quick-evaluation.md`.

For a one-page evaluator packet for directory reviewers, newsletter curators,
and team shares, see `docs/review-packet.md`.

For a plain-English explanation of reviewer selection, round-table debate, and
ship/revise/reject decisions, see
<https://markdonish.github.io/round-table-workspace/mechanism.html>.

For copy-ready open-source directory, newsletter, and tool-list submission
fields, see `docs/directory-submission-kit.md`.

For evaluator copy that explains how this differs from direct agent answers,
CI, manual checklists, and multi-agent frameworks, see
`docs/comparison-guide.md`.

For concrete AI coding failure modes that the workflow is meant to catch, see
`docs/ai-failure-modes.md`.

For a short visual recording plan for X, LinkedIn, newsletters, and README
screenshots, see `docs/demo-recording-guide.md`.

For an architecture decision transcript that shows `ship-check` catching a
premature abstraction, see
`examples/transcripts/ship-check-architecture-decision.md`.

For the ordered public distribution plan across HN, developer forums,
directories, newsletters, and team chats, see `docs/distribution-checklist.md`.

For current public submission targets and entry points, see
`docs/public-submission-targets.md`.

For a claim-safe Show HN title, first comment, and reply bank, see
`docs/show-hn-submission-draft.md`.

For newsletter editor, roundup, and curated-list pitches, see
`docs/newsletter-roundup-pitch-kit.md`.

For Product Hunt launch fields, maker comment, FAQ, assets, and guardrails, see
`docs/product-hunt-launch-kit.md`.

For short video scripts, captions, and clip variants, see
`docs/short-video-script-kit.md`.

For Reddit, forum, Discord, Slack, and GitHub discussion posts, see
`docs/developer-forum-feedback-kit.md`.

For collecting real AI workflow examples from visitors, use the GitHub issue
form:
<https://github.com/MarkDonish/round-table-workspace/issues/new?template=workflow_example.yml>.

For first-time contributor starter tasks, see
`docs/contributor-starter-issues.md`.

For the 24h and 72h feedback record used before writing the next public post,
see `docs/promotion-feedback-template.md`.

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
ai-code-review
cli
python
agent-workflow
agentic-workflow
code-review
ship-check
round-table
vibe-coding
openai
llm
```

## X / Twitter Launch Thread

Use this mechanism-first version when X feedback says the audience understands
the problem but still needs the workflow explained. Keep the GitHub repository
link in the main post so X can render the native GitHub card. Do not replace the
repo link with a screenshot when stars are the goal.

Main post:

```text
Before merging AI-written code, I run Round Table Workspace.

It spins up reviewer agents, keeps the useful ones, brings them into a bounded debate, then returns a practical decision: ship, revise, or reject.

https://github.com/MarkDonish/round-table-workspace
```

Reply 1:

```text
Step 1: it creates candidate reviewer agents and keeps the ones that add real signal: product risk, engineering evidence, claim boundaries, or user-facing gaps.
```

Reply 2:

```text
Inside the review, agents push on each other's claims, call out contradictions, and name the evidence still missing. The point is to turn confidence into something checkable.
```

Reply 3:

```text
The output is small on purpose: ship, revise, or reject, plus the concrete next actions before merge. That is the handoff I want from agent-generated work.
```

Publishing checks:

- Wait for the native GitHub card before posting the main tweet.
- Put the GitHub repo link in the main post, not only in a reply.
- Post replies slowly if the platform throttles consecutive replies.
- Record 24h and 72h feedback in `docs/promotion-feedback-template.md`
  before writing the next public campaign.

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
