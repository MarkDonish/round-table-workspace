# Developer Forum Feedback Kit

Use this kit when preparing a Reddit, forum, Discord, Slack, or GitHub
discussion post for Round Table Workspace.

Do not post this kit before the 72-hour X feedback is reviewed in
`docs/promotion-feedback-template.md`.

This file is for feedback-first community posts. It does not add host-live or
provider-live support claims, and it does not ask for coordinated votes,
upvotes, or stars.

## Source Links

- Reddit content policy: <https://redditinc.com/policies/content-policy>
- Reddit spam policy:
  <https://support.reddithelp.com/hc/en-us/articles/360043504051-What-constitutes-spam>
- Reddit self-promotion guidance:
  <https://www.reddit.com/wiki/selfpromotion/>
- Hacker News Show HN guidelines: <https://news.ycombinator.com/showhn.html>

Community-specific rules are the source of truth before posting. If a community
does not allow project promotion, do not post there.

## Fit Check

Use this post only when all are true:

```text
72h X feedback recorded:
target community rules checked:
post is feedback-first:
GitHub repo is the primary link:
no request for upvotes/stars:
claim dashboard fresh:
```

## Best-Fit Communities

Prioritize communities where members already discuss:

- AI coding agents
- code review workflows
- local-first developer tools
- CLI tools
- AI-generated code failures
- open-source maintainer workflows

Avoid broad communities where the post would read like generic launch spam.

## Primary Ask

Use one feedback question:

```text
What AI-generated coding failure should this review gate catch next?
```

Alternative:

```text
Where would a ship / revise / reject gate fit in your AI coding workflow?
```

Do not ask:

```text
Can you upvote this?
Can you star this?
Can you help launch this?
```

## Short Post

```text
I built Round Table Workspace for the moment right before a developer trusts
AI-generated work.

It creates a small review flow for AI coding agents:

- /room explores the problem
- /debate brings useful reviewer roles into a round-table review
- ship-check returns ship, revise, or reject with local evidence

Default demo path needs no provider key:
https://github.com/MarkDonish/round-table-workspace

The failure mode I am trying to catch is: "the agent sounds confident, so the
work gets merged or published before the real risk is checked."

If you use AI coding agents, what generated-work failure should this review
gate catch next?
```

## Longer Context Post

```text
I have been working on Round Table Workspace, a local-first review workflow for
AI coding agents.

The idea is simple: before trusting AI-generated work, run it through a small
review loop.

1. /room explores the product or engineering question
2. /debate pulls in useful reviewer roles for a structured round-table review
3. ship-check returns ship, revise, or reject with evidence

This is not meant to replace tests or human review. It is a guardrail for the
moment before a confident AI answer turns into a merge, architecture decision,
launch note, or public claim.

Repo:
https://github.com/MarkDonish/round-table-workspace

One-minute demo:
https://markdonish.github.io/round-table-workspace/one-minute-demo.html

I am looking for feedback from people actually using AI coding agents:

Where would this kind of review gate fit in your workflow, and what failure
mode should it catch first?
```

## Title Options

Use the plainest title that matches the community:

```text
Feedback wanted: a local review gate for AI coding agents
```

```text
How do you review AI-generated coding work before trusting it?
```

```text
Open-source tool for ship / revise / reject reviews of AI-generated work
```

Avoid:

```text
I built the best multi-agent framework
This will change AI coding forever
Please star my GitHub repo
```

## Reply Bank

### "How is this different from tests?"

```text
Tests answer whether known behavior still works. This is earlier in the
workflow: should the generated work be trusted, revised, or rejected before it
becomes a merge or public claim?
```

### "Is this production-ready?"

```text
The default public path is local-first and fixture-backed. I am keeping
host-live and provider-live support separate unless there is fresh evidence for
those claims.
```

### "Why not just ask the agent to review itself?"

```text
The goal is to make the review structured and repeatable: separate exploration,
round-table review, and a final ship / revise / reject decision with evidence.
```

### "What should I try first?"

```text
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

### "What feedback would help most?"

```text
The most useful feedback is a real AI-generated-work failure you have seen:
bad architecture, overconfident launch claims, missing user value, weak tests,
or a change that sounded ready but was not.
```

## Community Rules Checklist

Before posting:

- Read the target community rules.
- Search the community for recent similar posts.
- Prefer a feedback question over a launch announcement.
- Disclose that you are the maker.
- Use one primary link, preferably the GitHub repository.
- Do not ask for votes, upvotes, stars, bookmarks, or coordinated comments.
- Do not repost the same copy across multiple communities.
- Do not argue with moderators or members if the post is removed.

## What To Emphasize

- The concrete failure mode: trusting confident AI output too quickly.
- The mechanism: `/room`, `/debate`, then `ship-check`.
- The result: `ship`, `revise`, or `reject`.
- The default path: local-first and no provider key for the demo.
- The feedback ask: what should the review gate catch next?

## What To Avoid

- Do not describe the project as a generic multi-agent framework.
- Do not claim universal support for every agent host.
- Do not claim host-live or provider-live support without fresh evidence.
- Do not imply the workflow replaces tests, code review, or maintainers.
- Do not post before the 72-hour X feedback is reviewed.

## Tracking

Record each post in `docs/promotion-feedback-template.md`:

```text
surface:
community:
posted_at:
url:
copy_source: docs/developer-forum-feedback-kit.md
primary_link:
secondary_link:
initial comments:
24h result:
72h result:
stars_before:
stars_after:
next_action:
```
