# Short Video Script Kit

Use this kit when turning Round Table Workspace into a short video for X,
LinkedIn, Product Hunt, newsletters, or developer forums.

Do not publish a new public video campaign before the 72-hour X feedback is
reviewed in `docs/promotion-feedback-template.md`.

This file packages scripts for the current local-first, fixture-backed project
surface. It does not add host-live or provider-live support claims.

## Source Assets

Use these checked-in assets:

- Demo recording guide: `docs/demo-recording-guide.md`
- One-minute demo: `docs/one-minute-demo.md`
- AI-generated feature review demo:
  `docs/ai-generated-feature-review-demo.md`
- Repo card image: `docs/repo-card.png`
- GitHub repository: <https://github.com/MarkDonish/round-table-workspace>

## Video Gate

Only record or publish after all are true:

```text
72h X feedback recorded:
repo card still current:
one-minute demo still current:
GitHub repo link visible:
no secrets or local account details visible:
claim dashboard fresh:
```

## Core Video Idea

```text
An AI coding agent can sound ready before the decision is ready.
Round Table Workspace adds a local review gate:
/room -> /debate -> ship-check -> ship / revise / reject.
```

Keep the video about one mechanism, not the whole repository.

## 30-Second Script

Best for X, Product Hunt gallery, and developer forums.

| Time | Visual | On-screen text / voiceover |
|---:|---|---|
| 0-3s | Terminal with repo open | "Before trusting AI-generated work..." |
| 3-7s | Run `./rtw ship-check "Should we merge this AI-generated feature?"` | "Run a quick review gate." |
| 7-14s | Show reviewer panel | "Product, engineering, risk, and user views check the answer." |
| 14-22s | Highlight `Decision: revise` | "The result is not vague: ship, revise, or reject." |
| 22-27s | Show next actions | "Fix the missing evidence before merge." |
| 27-30s | Show GitHub repo | "Local-first demo. No provider key needed." |

Caption:

```text
AI coding agents can sound ready before the decision is ready.

Round Table Workspace adds a local review gate:
/room -> /debate -> ship-check -> ship / revise / reject

GitHub: https://github.com/MarkDonish/round-table-workspace
```

## 60-Second Script

Best for LinkedIn, README demo GIF planning, and newsletter embeds.

| Time | Visual | On-screen text / voiceover |
|---:|---|---|
| 0-5s | Repo title or terminal prompt | "AI coding agents are fast. Sometimes too fast." |
| 5-12s | Show a plausible AI-generated feature scenario | "The code looks plausible, but the decision is still open." |
| 12-20s | Run `ship-check` | "Before merging, ask the review gate." |
| 20-32s | Show panel votes | "A small reviewer panel looks at product value, engineering readiness, risk, and user clarity." |
| 32-42s | Highlight `Decision: revise` and confidence | "You get a direct decision: ship, revise, or reject." |
| 42-52s | Highlight next actions | "The useful part is the missing evidence: tests, claim boundaries, and user-facing clarity." |
| 52-60s | Show repo URL and one-minute demo link | "Try the local demo before the next generated change ships." |

Caption:

```text
This is the review step I wanted before trusting AI-generated coding work.

Round Table Workspace turns one confident answer into:
- reviewer perspectives
- a ship / revise / reject decision
- evidence you can inspect

Repo: https://github.com/MarkDonish/round-table-workspace
```

## Product Hunt Gallery Clip

Use this as a silent clip or GIF.

```text
Frame 1: AI-generated feature looks ready
Frame 2: ./rtw ship-check "Should we merge this?"
Frame 3: Reviewer panel votes
Frame 4: Decision: revise
Frame 5: Next actions: tests, claim boundary, user clarity
Frame 6: GitHub repo URL
```

Overlay text:

```text
Make AI coding agents argue before they ship.
```

## Forum-Friendly Clip

Use this when the post is feedback-first.

```text
Question for people using AI coding agents:
where would this review gate fit?

The demo:
1. run ship-check
2. see reviewer votes
3. get ship / revise / reject
4. inspect the missing evidence
```

Caption:

```text
I am looking for workflow feedback, not upvotes.

What generated-work failure should this catch next?
```

## Shot Checklist

Before recording:

- hide tokens, `.env` files, local account names, browser cookies, and private
  repo paths
- zoom terminal text so `Decision: revise` is readable
- keep the GitHub repository link visible at the end
- show one decision, not a long transcript
- keep the default claim to local-first and fixture-backed

## Do Not

- Do not claim host-live or provider-live support without fresh evidence.
- Do not say the workflow guarantees correctness.
- Do not show private local files, keys, cookies, or account details.
- Do not ask for votes, upvotes, or coordinated promotion.
- Do not publish before the 72-hour X feedback is reviewed.

## Tracking

Record each video post in `docs/promotion-feedback-template.md`:

```text
surface:
posted_at:
url:
copy_source: docs/short-video-script-kit.md
video_variant:
primary_link:
views_or_impressions:
likes_or_reactions:
comments:
clicks_if_available:
stars_before:
stars_after:
next_action:
```
