# Review Packet

Use this page when you are deciding whether Round Table Workspace is worth a
star, a directory listing, a newsletter mention, or a deeper local trial.

## 30-Second Summary

Round Table Workspace is a local-first review gate for AI coding agents. It
helps a developer slow down one confident AI answer, pull useful reviewer roles
into a structured round-table discussion, and end with a practical `ship`,
`revise`, or `reject` decision before trusting generated work.

Primary links:

- Repo: <https://github.com/MarkDonish/round-table-workspace>
- Pages overview: <https://markdonish.github.io/round-table-workspace/>
- Mechanism: <https://markdonish.github.io/round-table-workspace/mechanism.html>
- One-minute demo: <https://markdonish.github.io/round-table-workspace/one-minute-demo.html>
- 5-minute evaluation: <https://markdonish.github.io/round-table-workspace/quick-evaluation.html>

## Who It Is For

- developers using Codex, Claude Code, or other CLI agents for real work
- maintainers reviewing AI-generated code, docs, launch copy, or architecture
- teams that want an evidence trail before trusting a generated answer
- tool curators looking for local-first AI coding workflow projects

## What To Verify First

From a fresh clone:

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

Expected evaluation signal:

- `ship`, `revise`, or `reject` is visible
- product, engineering, risk, and user-facing review angles are visible
- missing evidence is called out before generated work is trusted
- next steps are small enough to act on
- local evidence can stay with the repository

## Why It Is Different

| Usual path | Round Table Workspace path |
|---|---|
| One AI answer sounds confident. | A small reviewer panel checks the answer. |
| Risks stay buried in a chat transcript. | Risks and missing evidence are written down. |
| The next step is vague. | The result is `ship`, `revise`, or `reject`. |
| Public claims can outrun evidence. | Claim boundaries stay tied to current validation. |

## Evidence And Boundaries

Current public claim:

- local-first workflow
- fixture-backed default demo path
- no provider key required for the default demo
- launch-kit, review examples, issue templates, and claim-boundary checks are
  committed in the repo

Do not claim:

- universal host-live support
- provider-live execution without a configured and validated provider lane
- correctness guarantees for AI-generated work
- replacement for tests, security review, or human ownership

No host-live or provider-live support is claimed without fresh evidence.

## Copy-Safe Listing

Name:

```text
Round Table Workspace
```

Short description:

```text
Local-first round-table review workflow for AI coding agents before trusting generated work.
```

Long description:

```text
Round Table Workspace helps developers using Codex, Claude Code, and CLI agents
review AI-generated work before trusting it. It creates a small reviewer panel,
brings useful perspectives into a round-table debate, and returns a practical
ship / revise / reject decision with evidence and claim boundaries.
```

Tags:

```text
ai-agents, ai-code-review, cli, codex, claude-code, local-first, ship-check, round-table
```

## Reviewer Checklist

- Open the repo and confirm the README explains the mechanism in plain English.
- Open the Pages overview and one-minute demo.
- Run the 5-minute local trial if evaluating hands-on.
- Check `reports/claim-boundary-dashboard.md` before repeating support claims.
- Keep fixture-backed, host-live, and provider-live evidence separate.
- If the project is useful, star the repo and mention which workflow it should
  cover next.
