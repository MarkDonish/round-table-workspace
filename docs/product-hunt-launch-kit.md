# Product Hunt Launch Kit

Use this kit when preparing a Product Hunt launch for Round Table Workspace.

Do not launch before the 72-hour X feedback is reviewed in
`docs/promotion-feedback-template.md`.

This file does not add host-live or provider-live support claims. It packages
the current local-first, fixture-backed project surface for a Product Hunt
listing that can send builders back to the GitHub repository.

## Source Links

- Product Hunt launch guide: <https://www.producthunt.com/launch>
- Product Hunt launch preparation guide:
  <https://www.producthunt.com/launch/preparing-for-launch>
- Product Hunt posting help:
  <https://help.producthunt.com/en/articles/479557-how-to-post-a-product>

Current platform notes to respect:

- use a personal Product Hunt account, not a company account, for posting
- complete account onboarding before trying to post
- prepare listing fields and assets before starting the submission
- scheduling may be available before launch day

## Launch Gate

Only prepare the draft until all are true:

```text
72h X feedback recorded:
GitHub card/link preview checked:
repo_card.png still current:
one-minute demo still current:
claim dashboard fresh:
release-check strict clean:
```

## Primary Product URL

Use the GitHub repository when stars are the goal:

```text
https://github.com/MarkDonish/round-table-workspace
```

Use the Pages overview only as a supporting link:

```text
https://markdonish.github.io/round-table-workspace/
```

## Name

```text
Round Table Workspace
```

## Tagline Options

Preferred:

```text
Make AI coding agents argue before they ship
```

Mechanism-first:

```text
Ship/revise/reject for AI-generated coding work
```

Developer-tool:

```text
A local review gate for AI coding agents
```

Use the preferred tagline unless the 72-hour X feedback shows stronger clicks
for `ship / revise / reject`.

## Short Description

```text
Round Table Workspace is a local-first review workflow for AI coding agents.
It uses /room, /debate, and ship-check to turn one confident AI answer into a
structured ship / revise / reject decision with local evidence.
```

## Longer Description

```text
AI coding agents are fast, but a single confident answer can skip product
value, engineering readiness, user clarity, and launch-claim risk.

Round Table Workspace adds a small review layer before you trust generated
work. /room explores the problem, /debate brings useful reviewer roles into a
round-table discussion, and ship-check returns ship, revise, or reject with
evidence you can inspect.

The default demo path is local-first and fixture-backed. It does not require
provider keys, and the repo keeps host-live/provider-live claims separate from
what has fresh evidence.
```

## Maker Comment

```text
I built Round Table Workspace for the moment right before a developer trusts
AI-generated work.

The pattern I kept seeing: an AI coding agent gives a confident answer, but the
decision still needs product sense, engineering review, risk checks, and a
clear next action.

This project turns that pause into a small local workflow:

- /room explores an ambiguous product or engineering question
- /debate reviews risky choices through a structured round table
- ship-check returns ship, revise, or reject with evidence

The default demo path is intentionally conservative: local-first,
fixture-backed, and no provider key required. I am not claiming host-live or
provider-live support without fresh evidence.

I would love feedback from people using AI coding agents in real work:

What is one generated-work failure this review gate should catch next?
```

## Gallery Assets

Use existing assets first:

```text
Repo preview image:
docs/repo-card.png
https://markdonish.github.io/round-table-workspace/repo-card.png

Repo preview card:
docs/repo-card.html
https://markdonish.github.io/round-table-workspace/repo-card.html

One-minute demo:
https://markdonish.github.io/round-table-workspace/one-minute-demo.html

AI-generated feature review demo:
https://markdonish.github.io/round-table-workspace/ai-generated-feature-review-demo.html
```

If Product Hunt needs multiple gallery images, create them from:

- repo card
- one-minute `ship-check` transcript
- before/after review value from README
- `ship / revise / reject` decision example

Do not generate new screenshots that imply host-live or provider-live support.

## Suggested Topics

```text
Developer Tools
Artificial Intelligence
Open Source
Productivity
```

Use only categories that are available in the Product Hunt submission flow.

## FAQ

### Is this a multi-agent framework?

```text
No. It is narrower: a review gate for the moment before AI-generated work
becomes a merge, launch claim, architecture decision, or public note.
```

### Does it run live providers by default?

```text
No. The public demo path is fixture-backed and local-first. Host-live and
provider-live support are not claimed without fresh validation evidence.
```

### What should I try first?

```text
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

### Who is it for?

```text
Developers and teams using AI coding agents who want a repeatable review step
before trusting generated work.
```

## Do Not

- Do not ask for upvotes.
- Do not coordinate comments or votes.
- Do not launch before the 72-hour X feedback is reviewed.
- Do not describe fixture-backed demos as production validation.
- Do not claim host-live or provider-live support without fresh evidence.
- Do not use a landing page as the primary URL while stars are the goal.

## Tracking

After launch, record results in `docs/promotion-feedback-template.md`:

```text
surface: Product Hunt
submitted_at:
url:
copy_source: docs/product-hunt-launch-kit.md
primary_link:
secondary_link:
rank_or_position:
comments:
upvotes_or_reactions:
clicks_if_available:
stars_before:
stars_after:
notable replies:
next_action:
```
