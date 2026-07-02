# Contributor Starter Issues

Use this page when the public `good first issue` label is empty, stale, or hard
to scan. The goal is to give new visitors small, claim-safe ways to help Round
Table Workspace without needing to understand the whole runtime.

Each starter issue should stay narrow, include a clear acceptance check, and
avoid host-live or provider-live claims unless fresh validation evidence exists.

## Claim Boundary

No host-live or provider-live claims should be added by starter issues unless a
maintainer links fresh validation evidence. Keep examples, transcripts, and
docs local-first or fixture-backed when that is the only current evidence.

## Starter Issue Set

### 1. Add one more `ship-check` transcript for a docs-only AI change

Why it helps: visitors understand the project faster when they can see concrete
examples of the review gate catching a real failure mode.

Suggested scope:

- Add one transcript under `examples/transcripts/`.
- Use a docs-only AI-generated change, such as a release note, README claim, or
  launch copy update.
- Keep the outcome conservative: `revise` is a good default if evidence or
  wording is missing.
- Link the transcript from `README.md` or `docs/index.md`.

Acceptance check:

```bash
python3 -m unittest tests.test_transcripts -v
python3 -m unittest tests.test_launch_surface.LaunchSurfaceTest -v
```

Labels: `good first issue`, `documentation`, `example`

### 2. Improve a quick-start error message for fresh clones

Why it helps: a visitor who hits a confusing local error is less likely to try
the repo long enough to star it.

Suggested scope:

- Run `./rtw doctor --quick` in a fresh checkout.
- Pick one existing error or warning that could be clearer.
- Improve the wording without changing the underlying claim boundary.
- Add or update a focused test if the message is covered by unit tests.

Acceptance check:

```bash
./rtw doctor --quick --quiet
python3 -m unittest discover -v
```

Labels: `good first issue`, `enhancement`

### 3. Add one workflow example issue from a real AI coding moment

Why it helps: Round Table Workspace gets sharper when it learns from real
places where AI coding agents sound confident too early.

Suggested scope:

- Use the `AI workflow example` issue template.
- Describe the workflow or failure mode.
- Mark whether the expected review decision is `ship`, `revise`, or `reject`.
- Do not include API keys, tokens, cookies, customer data, or private logs.

Acceptance check:

- The issue is public, clear, and reproducible enough for a maintainer to turn
  into a fixture, transcript, or docs example.

Labels: `good first issue`, `feedback`, `example`

### 4. Add one comparison row to the evaluator guide

Why it helps: teams evaluating this repo need to know when it fits better than
plain chat, CI, manual checklists, or heavier multi-agent frameworks.

Suggested scope:

- Update `docs/comparison-guide.md`.
- Add one specific alternative workflow, such as direct Claude Code review,
  plain PR review, a CI-only gate, or a team checklist.
- Explain when Round Table Workspace helps and when it is overkill.
- Keep support claims local-first unless evidence says otherwise.

Acceptance check:

```bash
python3 -m unittest tests.test_launch_surface.LaunchSurfaceTest.test_comparison_guide_is_claim_safe_and_linked -v
```

Labels: `good first issue`, `documentation`

## Maintainer Checklist

When creating or refreshing starter issues:

- Keep each issue small enough for a first-time contributor.
- Include a concrete file path or command.
- Add `good first issue`.
- Add `help wanted` only when outside contribution is genuinely welcome.
- Keep secrets, private logs, and account-specific data out of the task.
- Keep live support claims tied to current evidence.
