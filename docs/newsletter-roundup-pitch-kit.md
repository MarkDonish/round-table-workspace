# Newsletter And Roundup Pitch Kit

Use this kit when pitching Round Table Workspace to AI agent newsletters,
developer-tool roundups, curated GitHub lists, or small operator newsletters.

Do not send these pitches before the 72-hour X feedback is reviewed in
`docs/promotion-feedback-template.md`.

This file does not add host-live or provider-live support claims. It packages
the current local-first, fixture-backed project surface for editors and
curators who need a concise reason to include the repository.

## Best Fit

Use this kit for publications that cover:

- AI coding agents
- developer tools
- local-first workflows
- open-source agent infrastructure
- code review and engineering process
- practical LLM tooling

Do not use it for generic AI news blasts where the audience is not likely to
clone a repo or try a CLI workflow.

## Primary Links

```text
GitHub repo:
https://github.com/MarkDonish/round-table-workspace

One-minute demo:
https://markdonish.github.io/round-table-workspace/one-minute-demo.html

Repo preview card:
https://markdonish.github.io/round-table-workspace/repo-card.html

Repo preview image:
https://markdonish.github.io/round-table-workspace/repo-card.png

Comparison guide:
https://github.com/MarkDonish/round-table-workspace/blob/main/docs/comparison-guide.md

AI failure modes:
https://github.com/MarkDonish/round-table-workspace/blob/main/docs/ai-failure-modes.md
```

## Subject Lines

Use one subject line per outreach. Keep the first send plain.

```text
Open-source review gate for AI coding agents
```

```text
Round Table Workspace: ship/revise/reject for AI-generated work
```

```text
A local-first workflow for reviewing AI agent output before merge
```

## Short Pitch

```text
Round Table Workspace is an open-source, local-first review workflow for AI
coding agents. It gives generated work a small round-table review before a
developer trusts it: /room explores the problem, /debate reviews risky choices,
and ship-check returns ship, revise, or reject with local evidence.

Repo: https://github.com/MarkDonish/round-table-workspace
Demo: https://markdonish.github.io/round-table-workspace/one-minute-demo.html
```

## Editor Email

```text
Hi,

I am sharing Round Table Workspace in case it fits an upcoming AI agent or
developer-tool roundup.

It is an open-source local-first review workflow for AI coding agents. The
simple idea is: before trusting generated work, run a small round-table review
and get a concrete ship / revise / reject decision.

The default demo path is fixture-backed and does not require provider keys. The
project is intentionally conservative about claims: it does not claim
host-live or provider-live support without fresh evidence.

Why it may fit your readers:

- it targets a concrete AI coding failure mode: trusting one confident answer
  too quickly
- it is cloneable and testable from the repo
- it includes a one-minute demo and claim-boundary docs
- it is useful for code reviews, launch claims, architecture decisions, and
  AI-assisted workflow checks

GitHub:
https://github.com/MarkDonish/round-table-workspace

One-minute demo:
https://markdonish.github.io/round-table-workspace/one-minute-demo.html

If it is useful, the most accurate framing is:
"a local-first review gate for AI-generated coding work before you trust it."
```

## Roundup Listing

```text
Round Table Workspace - a local-first review gate for AI coding agents. It
uses /room, /debate, and ship-check to turn one confident AI answer into a
structured ship / revise / reject decision with local evidence.

Repo: https://github.com/MarkDonish/round-table-workspace
Demo: https://markdonish.github.io/round-table-workspace/one-minute-demo.html
```

## One-Sentence Blurbs

```text
A local-first review workflow that makes AI coding agents argue before you
trust generated work.
```

```text
Ship / revise / reject decisions for AI-generated coding work, with local
evidence and conservative claim boundaries.
```

```text
A pre-merge review gate for teams using Codex, Claude Code, or other CLI agent
workflows.
```

## Follow-Up Reply

Use only after a real response. Do not spam follow-ups.

```text
Thanks for taking a look. If useful, the fastest evaluation path is:

git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick

The best feedback would be one AI-generated workflow failure that this kind of
review gate should catch next.
```

## What To Emphasize

- review AI-generated work before trusting it
- local-first default demo path
- no provider key required for the demo path
- ship / revise / reject as the practical outcome
- claim boundaries are visible in repo docs
- GitHub repository is the primary link when stars are the goal

## What To Avoid

- Do not claim host-live or provider-live support without fresh evidence.
- Do not describe fixture-backed demos as production validation.
- Do not pitch it as a general multi-agent framework.
- Do not send the same copy to every publication.
- Do not send before 72-hour X feedback is reviewed.
- Do not ask editors for stars, upvotes, or coordinated promotion.

## Tracking

After sending, record the outreach in `docs/promotion-feedback-template.md`:

```text
surface:
submitted_at:
url:
copy_source: docs/newsletter-roundup-pitch-kit.md
primary_link:
secondary_link:
initial comments:
24h result:
72h result:
stars_before:
stars_after:
next_action:
```
