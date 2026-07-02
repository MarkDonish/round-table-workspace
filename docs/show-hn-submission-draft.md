# Show HN Submission Draft

Use this draft only after the 72-hour X feedback has been reviewed in
`docs/promotion-feedback-template.md`.

Reviewed against the public Show HN guidelines on 2026-07-02:

- the project should be something people can try
- the title should begin with `Show HN`
- the post should not be a landing page
- do not ask friends to upvote or comment

This draft does not add host-live or provider-live support claims. It keeps the
submission focused on the local-first, fixture-backed workflow people can clone
and run.

## Entry Point

Submit at:

```text
https://news.ycombinator.com/submit
```

HN may require login before showing the submit form.

## Preferred Title

```text
Show HN: Round Table Workspace - make AI coding agents argue before they ship
```

Why this title:

- starts with `Show HN`
- says what the tool changes in plain language
- keeps the repo's strongest mechanism in the first line

## Alternate Titles

```text
Show HN: Round Table Workspace - a local review gate for AI coding agents
```

```text
Show HN: Round Table Workspace - ship/revise/reject for AI-generated work
```

Use the preferred title unless the 72-hour feedback says the phrase
`ship/revise/reject` pulled more link clicks than the round-table mechanism.

## URL

Use the GitHub repository as the submitted URL:

```text
https://github.com/MarkDonish/round-table-workspace
```

Do not submit the Pages overview as the primary URL while stars are the goal.

## First Comment

Post this as the first comment after submitting.

```text
I built this because AI coding agents can be very fast and still skip the
question that matters right before merge: should I trust this output yet?

Round Table Workspace gives that moment a small local review workflow:

- /room explores an ambiguous product or engineering question
- /debate brings useful reviewer roles into a structured round-table review
- ship-check returns ship, revise, or reject with evidence

The default path is deliberately low-friction:

git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick

It is fixture-backed by default and does not require provider keys for the demo
path. I am keeping the claims conservative: no host-live or provider-live
support is claimed without fresh evidence.

I would especially like feedback on two things:

1. Does the round-table mechanism make sense as a pre-merge review step?
2. What AI-generated workflow failure should this catch next?
```

## Optional Links For Replies

Use these only when someone asks for more detail. Do not overload the first
comment with every link.

```text
One-minute demo:
https://markdonish.github.io/round-table-workspace/one-minute-demo.html

Why this is different from a direct AI answer:
https://github.com/MarkDonish/round-table-workspace/blob/main/docs/comparison-guide.md

Failure modes it is meant to catch:
https://github.com/MarkDonish/round-table-workspace/blob/main/docs/ai-failure-modes.md

Use cases:
https://github.com/MarkDonish/round-table-workspace/blob/main/docs/use-cases.md
```

## Reply Bank

### If someone asks whether this runs real agents

```text
The default public path is fixture-backed and local-first. I am not claiming
host-live or provider-live support here unless there is fresh validation
evidence for that lane.

The point of the current release is the review workflow and evidence boundary:
turn one confident AI answer into a structured ship/revise/reject decision that
you can inspect before trusting it.
```

### If someone says this sounds like a multi-agent framework

```text
I would not frame it as a general multi-agent framework. It is narrower: a
review gate for the moment before AI-generated work becomes a merge, launch
claim, architecture decision, or public note.
```

### If someone asks what to try first

```text
The shortest path is:

git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

### If someone asks what feedback is most useful

```text
The most useful feedback is a concrete AI-generated failure mode that a
pre-merge review gate should catch. I am trying to keep the tool grounded in
real workflow misses, not generic agent hype.
```

## Do Not

- Do not ask for upvotes.
- Do not coordinate comments or votes.
- Do not submit before the 72-hour X feedback is reviewed.
- Do not describe fixture-backed demos as production validation.
- Do not claim host-live or provider-live support without fresh evidence.
- Do not hide the GitHub repository behind the Pages overview while stars are
  the goal.

## After Posting

Record the submission in `docs/promotion-feedback-template.md`:

```text
surface: Hacker News / Show HN
submission_url:
rank_or_position:
comments:
upvotes_or_reactions:
clicks_if_available:
stars_before:
stars_after:
notable replies:
moderation_notes:
```
