# Community Share Kit

Use this page when sharing Round Table Workspace in developer communities,
launch directories, newsletters, or private team chats.

## One-Sentence Description

Round Table Workspace is a local-first review workflow that makes AI coding
agents explore, debate, and return a `ship`, `revise`, or `reject` decision
before you trust generated work.

## Best Links

- GitHub repo: <https://github.com/MarkDonish/round-table-workspace>
- Pages overview: <https://markdonish.github.io/round-table-workspace/>
- One-minute demo:
  <https://markdonish.github.io/round-table-workspace/one-minute-demo.html>
- Use cases:
  <https://markdonish.github.io/round-table-workspace/use-cases.html>
- AI feature review demo:
  <https://markdonish.github.io/round-table-workspace/ai-generated-feature-review-demo.html>
- Repo preview card:
  <https://markdonish.github.io/round-table-workspace/repo-card.html>
- Repo preview image:
  <https://markdonish.github.io/round-table-workspace/repo-card.png>
- Reviewer checklist:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/reviewer-checklist.md>
- Why star this repo:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/why-star-this-repo.md>
- Comparison guide:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/comparison-guide.md>
- AI failure modes:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/ai-failure-modes.md>
- Demo recording guide:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/demo-recording-guide.md>
- Contributing guide:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/CONTRIBUTING.md>
- Good first issues:
  <https://github.com/MarkDonish/round-table-workspace/labels/good%20first%20issue>
- Directory submission kit:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/directory-submission-kit.md>
- Distribution checklist:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/distribution-checklist.md>
- Public submission targets:
  <https://github.com/MarkDonish/round-table-workspace/blob/main/docs/public-submission-targets.md>
- LLM summary:
  <https://markdonish.github.io/round-table-workspace/llms.txt>

## Short Blurbs

### 120 Characters

Local-first round-table review for AI coding agents before you trust generated
work.

### 280 Characters

Round Table Workspace gives AI coding agents a review step before you trust
their output: `/room` explores the problem, `/debate` reviews risky choices, and
`ship-check` returns `ship`, `revise`, or `reject` with evidence you can audit.

### Community Post

I built Round Table Workspace for the moment right before you trust
AI-generated work.

It gives Codex, Claude Code, and local CLI agents a simple review workflow:

- `/room` explores an ambiguous product or engineering question
- `/debate` brings useful reviewer roles into a structured round-table review
- `ship-check` returns `ship`, `revise`, or `reject`
- outputs stay local-first and audit-friendly

The default demo path runs without provider keys:

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

If you use AI coding agents for real work, this is meant to be the review gate
before a confident answer becomes a merge, launch note, architecture change, or
public claim.

## Channel Angles

| Channel | Best angle | Suggested CTA |
|---|---|---|
| Hacker News | Show a local-first review gate for AI coding agents | Try the 60-second demo and critique the workflow |
| Reddit / developer forums | Ask whether teams need a pre-merge AI review gate | Share one failure mode this would catch |
| LinkedIn | Frame it as an AI-assisted engineering governance workflow | Share the short recording or Pages demo |
| Newsletters | Position it as a lightweight open-source tool for safer agent work | Link to the one-minute transcript or demo GIF |
| Private team chats | Share the `ship-check` command as a quick local trial | Run it before the next AI-generated change |
| Open-source directories | Use the repo as the primary URL and the demo as proof | Follow the distribution checklist and public submission targets |

## Good First Feedback

- Report where the 60-second demo was unclear.
- Suggest one AI-generated workflow that needs a better `ship-check` example.
- Ask whether a host, provider, wrapper, or release claim is backed by current evidence.
- Share one failure mode from real AI-assisted coding that a round-table review
  should catch.

## What To Emphasize

- The project is for AI coding workflows that need a real review step.
- It creates a small panel of reviewer roles instead of trusting one answer.
- The workflow moves from exploration to debate to a concrete decision.
- The result is practical: `ship`, `revise`, or `reject`.
- The default demo is local-first and does not require provider keys.
- Evidence and claim boundaries are kept visible in repo files.

## What To Avoid Claiming

- No host-live or provider-live support is claimed without current evidence.
- Fixture-backed demos are not described as production validation.
- Config preflight is not described as real provider availability.
- The project is not marketed as universal support for every local agent host.
- The workflow helps review AI-generated work; it does not guarantee correctness.

## Fast Evaluation Path

For someone deciding whether the repo is worth starring:

1. Open the Pages overview.
2. Read the comparison guide if they are deciding whether this is different
   from a direct agent answer, CI, or a manual checklist.
3. Scan the failure modes guide to see whether the pain is familiar.
4. Use the demo recording guide if they need a quick visual explanation.
5. Read the AI feature review demo.
6. Run the 60-second local demo.
7. Use the distribution checklist if they want to share the repo with a team,
   directory, newsletter, or developer community.
8. Check whether `ship`, `revise`, or `reject` would help their current agent
   workflow.

```bash
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

If the answer is yes, star the repo and try it before the next generated change
ships.
