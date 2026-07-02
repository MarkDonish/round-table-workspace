# Public Submission Targets

Use this file with `docs/distribution-checklist.md` when preparing external
submissions for Round Table Workspace.

Verified: 2026-07-02.

This is a promotion checklist, not a support claim. It does not add
host-live or provider-live support. Keep each submission focused on the
local-first, fixture-backed review workflow and link back to the GitHub
repository when stars are the goal.

## Target List

| Priority | Surface | Current entry point | Use this asset | Why it fits |
|---|---|---|---|---|
| 1 | Hacker News / Show HN | <https://news.ycombinator.com/submit> | GitHub repo plus one-minute demo | HN explicitly supports projects people can try, and RTW has a no-provider demo path. |
| 2 | Product Hunt | <https://www.producthunt.com/launch> | `docs/product-hunt-launch-kit.md`, repo card, one-minute demo, GitHub repo | Product Hunt is built around makers sharing products and getting feedback from early adopters. |
| 3 | DevHunt | <https://devhunt.org/> | Repo card and GitHub repo | DevHunt is focused on developer tools, so RTW should lead with the AI coding review workflow. |
| 4 | Developer forums and subreddits | Use the community's own posting page | Community intro plus AI failure modes | Best when the post asks for workflow critique, not generic promotion. |
| 5 | AI agent newsletters and roundups | Use each publication's submission/contact path | `docs/newsletter-roundup-pitch-kit.md` plus repo card image | Best after the first X post has feedback data or a clearer demo angle. |

## Channel Notes

### Hacker News / Show HN

Use only when the project is easy to try. Lead with the GitHub repository and
include the no-provider demo path.

Recommended title:

```text
Show HN: Round Table Workspace – local-first review gate for AI coding agents
```

Use:

- `docs/show-hn-submission-draft.md`
- `docs/launch-copy.md#hacker-news`
- `docs/one-minute-demo.md`
- `docs/ai-failure-modes.md`

Avoid:

- asking friends to upvote
- posting a landing page instead of the runnable repo
- describing fixture-backed demos as production validation

### Product Hunt

Prepare before posting. Use the repo card image as the visual, the Pages demo
as proof, and the GitHub repo as the primary URL only if the platform allows a
repository-first product link.

Use:

- `docs/product-hunt-launch-kit.md`
- `docs/directory-submission-kit.md`
- `docs/repo-card.png`
- `docs/demo-recording-guide.md`

Avoid:

- asking for upvotes
- launching before the 72-hour X feedback is reviewed
- overclaiming host-live or provider-live support

### DevHunt

Lead with the developer-tool angle:

```text
A local-first review gate for AI-generated code, docs, launch claims, and
architecture decisions.
```

Use:

- GitHub repo as the primary URL
- `docs/repo-card.html` for preview
- `docs/comparison-guide.md` when explaining why this is different from a
  direct agent answer

### Developer Forums

Use forum posts for feedback, not broadcast. The best ask is:

```text
What AI-generated workflow failure should this review gate catch next?
```

Use:

- `docs/community-share-kit.md#community-post`
- `docs/ai-failure-modes.md`
- `docs/use-cases.md`

## Tracking Fields

For each submission, record:

```text
surface:
submitted_at:
url:
copy_source:
primary_link:
secondary_link:
initial comments:
24h result:
72h result:
stars_before:
stars_after:
next_action:
```

Do not publish a second public campaign from the same angle until the 72-hour
result is recorded.

Use `docs/promotion-feedback-template.md` to record X analytics, submission
metrics, repository movement, and the next copy angle.

Use `docs/show-hn-submission-draft.md` for the HN title, first comment, reply
bank, and HN-specific guardrails.

Use `docs/newsletter-roundup-pitch-kit.md` for AI agent newsletter, roundup,
and curated-list outreach after the 72-hour X feedback review.

Use `docs/product-hunt-launch-kit.md` for Product Hunt listing fields, maker
comment, FAQ, visual assets, and launch guardrails.

## Source Links

- Hacker News submit: <https://news.ycombinator.com/submit>
- Hacker News Show HN guidelines: <https://news.ycombinator.com/showhn.html>
- Product Hunt launch guide: <https://www.producthunt.com/launch>
- DevHunt: <https://devhunt.org/>
