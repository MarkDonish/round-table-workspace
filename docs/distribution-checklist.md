# Distribution Checklist

Use this checklist when promoting Round Table Workspace outside the repository.
It turns the existing launch copy into an ordered, claim-safe submission plan.
For current public entry points, use `docs/public-submission-targets.md`.

This document does not add host-live or provider-live support claims. It only
packages already checked-in links and copy so the repository can be submitted
without inventing new claims.

## Primary Goal

Drive interested developers to the GitHub repository first, then to the
one-minute demo if they need proof before starring.

Primary URL:

```text
https://github.com/MarkDonish/round-table-workspace
```

Secondary demo URL:

```text
https://markdonish.github.io/round-table-workspace/one-minute-demo.html
```

Visual preview URL:

```text
https://markdonish.github.io/round-table-workspace/repo-card.html
```

Preview image:

```text
https://markdonish.github.io/round-table-workspace/repo-card.png
```

## Submission Order

| Order | Surface | Goal | Link to use | Copy source |
|---|---|---|---|---|
| 1 | Hacker News / Show HN | Get technical critique from builders | GitHub repo | `docs/show-hn-submission-draft.md` |
| 2 | Developer Reddit / forum threads | Find pain-aligned users of AI coding agents | GitHub repo | `docs/community-share-kit.md#community-post` |
| 3 | Product Hunt | Reach product-minded early adopters | GitHub repo plus one-minute demo | `docs/product-hunt-launch-kit.md` |
| 4 | Open-source directories and tool lists | Create durable discovery links | GitHub repo | `docs/directory-submission-kit.md` |
| 5 | AI agent newsletters and roundups | Reach people already tracking agent tools | One-minute demo plus GitHub repo | `docs/newsletter-roundup-pitch-kit.md` |
| 6 | Private team chats | Get direct workflow feedback | One-minute demo | `docs/community-share-kit.md#fast-evaluation-path` |
| 7 | GitHub issue comments or related discussions | Invite specific failure-mode feedback | AI failure modes guide | `docs/ai-failure-modes.md` |

## Copy Blocks

### Short Directory Entry

```text
Round Table Workspace is a local-first review gate for AI coding agents. It
uses /room, /debate, and ship-check to turn one confident AI answer into a
structured ship / revise / reject decision with local evidence.
```

### Community Intro

```text
I built Round Table Workspace for the moment right before a developer trusts
AI-generated work.

Instead of asking one agent whether a change is ready, it runs a small
round-table review and returns ship, revise, or reject.

Repo: https://github.com/MarkDonish/round-table-workspace
Demo: https://markdonish.github.io/round-table-workspace/one-minute-demo.html
```

### Newsletter Pitch

```text
Round Table Workspace is an open-source local-first workflow for reviewing
AI-generated coding work before it becomes a merge, launch note, architecture
decision, or public claim. It is fixture-backed by default, runs without a
provider key for the demo path, and keeps claim boundaries visible in repo
files.
```

## Submission Checklist

- Use the GitHub repository as the first URL when stars are the goal.
- Include the one-minute demo only when the platform accepts a secondary link.
- Use the repo preview card or image when a platform needs a screenshot,
  thumbnail, or social card.
- Mention `ship`, `revise`, or `reject` in the first paragraph.
- Mention local-first and no provider key for the default demo path.
- Keep the primary pain concrete: trusting AI-generated work too quickly.
- Ask for one specific response: star the repo, try the demo, or share a
  failure mode.

## Avoid

- Do not describe the fixture-backed demo as production validation.
- Do not claim universal support for every agent host.
- Do not claim host-live or provider-live support without fresh evidence.
- Do not pitch it as a generic multi-agent framework.
- Do not hide the GitHub repository behind a landing page when stars are the
  goal.

## Tracking

Record each submission with:

```text
date:
surface:
url:
copy variant:
initial response:
24h result:
72h result:
next change:
```

Use the 72-hour result to decide whether the next public post should lead with
the mechanism, the failure mode, the demo, or the comparison against a direct
agent answer.

For the full 24h and 72h feedback record, use
`docs/promotion-feedback-template.md`.

For the HN-specific title, first comment, reply bank, and "do not" list, use
`docs/show-hn-submission-draft.md`.

For newsletter editor emails, roundup listings, and follow-up replies, use
`docs/newsletter-roundup-pitch-kit.md`.

For Product Hunt fields, maker comment, FAQ, visual assets, and launch
guardrails, use `docs/product-hunt-launch-kit.md`.
