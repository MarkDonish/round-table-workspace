# Promotion Feedback Template

Use this template after each public post or submission. It keeps promotion
decisions tied to observed feedback instead of rewriting the next campaign from
memory.

This template does not add host-live or provider-live support claims. It only
records public response, repository movement, and the next copy angle to test.

## Rule

Do not publish a second public campaign from the same angle until the 72-hour
result is recorded.

For the next X post, use the local OpenClaw DeepSeek writing path only after
these fields are filled in.

## Snapshot

```text
campaign:
surface:
post_url:
posted_at:
copy_source:
primary_link:
secondary_link:
media_or_card:
stars_before:
stars_after:
forks_before:
forks_after:
watchers_before:
watchers_after:
```

## X Metrics

Record the numbers exactly as shown in X analytics.

```text
24h impressions:
24h engagements:
24h engagement rate:
24h link clicks:
24h profile visits:
24h likes:
24h reposts:
24h replies:
24h bookmarks:
24h new follows:

72h impressions:
72h engagements:
72h engagement rate:
72h link clicks:
72h profile visits:
72h likes:
72h reposts:
72h replies:
72h bookmarks:
72h new follows:
```

## Submission Metrics

Use this section for Hacker News, Product Hunt, DevHunt, developer forums,
newsletters, and directories.

```text
surface:
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

## Qualitative Feedback

```text
best positive signal:
most useful criticism:
most repeated confusion:
question people asked:
phrase that seemed to work:
phrase that felt too vague:
unexpected audience:
```

## Angle Decision

Choose one next angle. Keep the next post focused on one reason to click the
GitHub repository.

| Angle | Use when the data says | Next copy should lead with |
|---|---|---|
| mechanism-first | People ask how the round table actually works | Agent selection, debate, and final ship / revise / reject decision |
| failure-mode-first | Replies mention bad AI-generated work or risky merges | The concrete mistake RTW catches before trust |
| demo-first | Link clicks are weak but media engagement is strong | A short transcript or screen recording before the repo link |
| comparison-first | People compare it with direct agent answers, CI, or multi-agent frameworks | What RTW adds before tests or human review |
| proof-card-first | The repo card gets attention but the text underexplains value | GitHub card plus one practical workflow outcome |

Selected angle:

```text
angle:
why this angle:
what to remove from the old copy:
what to keep from the old copy:
next primary link:
next secondary link:
```

## Decision Gate

```text
ship next campaign:
revise before posting:
reject this angle:
reason:
```

Use `docs/public-submission-targets.md` for the next surface, and
`docs/distribution-checklist.md` for the channel order.
