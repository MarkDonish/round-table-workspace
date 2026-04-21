# Development Sync Protocol

> Purpose: define how local development progress is tracked, verified, committed, and synced to GitHub for this repository.
> Last reviewed: 2026-04-21

---

## Role

This file is the checked-in operating protocol for development continuity.

Use it when a local agent or developer continues work on this repository, especially across:

- multiple machines
- multiple sessions
- local development plus GitHub sync

This file is not a historical report.
It is an active source-of-truth workflow document.

---

## Default Rule

Development happens in the local repository first.

GitHub is the remote sync target.

The expected loop is:

1. inspect local repo state
2. read the relevant source-of-truth files
3. implement locally
4. verify locally
5. commit verified changes
6. push to GitHub
7. report what changed and what still remains

Do not treat GitHub as a mounted working directory.
Do not treat `reports/` as the live implementation source.

If local Superpowers is installed, use it as a workflow accelerator on top of this repository protocol, not instead of it.

---

## Per-Task Sync Standard

The required sync unit is not every keystroke.

The required sync unit is one verified development task or one verified milestone.

That means:

- small task: usually 1 task -> 1 commit -> 1 push
- larger task: split by milestone, and sync each milestone after verification
- unfinished exploratory work should not be reported as done

If a task is blocked before verification, report the blocker clearly instead of pretending it is complete.

---

## Required Start Checklist

Before starting a new development task, check:

1. current branch and repo cleanliness
2. whether local `main` is already aligned with `origin/main`
3. which files are source of truth for this task
4. whether there are unrelated local changes that should not be touched

Minimum command checks:

- `git status -sb`
- `git log --oneline -5`
- `git remote -v`

If local Superpowers is available and the task is non-trivial, also read:

- `docs/superpowers/local-development-integration.md`

---

## Source Of Truth Rule

For active development, prefer:

- `README.md`
- `AGENTS.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/`

Treat these as non-source:

- `reports/`
- `artifacts/`

Use `reports/` only for archaeology, context, or old decisions.
Use `artifacts/` only for outputs, fixtures, generated evidence, or exports.

---

## Verification Rule

Before commit and push, perform the most relevant local verification available.

Examples:

- CLI help or syntax check
- fixture replay
- contract validation
- local test command
- smoke run of the changed path

If a full live validation cannot run because credentials, provider config, or external systems are missing, state that explicitly in the final report.

If local Superpowers participates in the task, use it to strengthen planning and review quality, but keep verification anchored in real repo-local commands and checked-in validation paths.

---

## Local Superpowers Integration

This repository now explicitly supports local Superpowers participation in development.

Preferred mapping:

1. `superpowers:writing-plans` for multi-step implementation planning
2. `superpowers:subagent-driven-development` when subagents are available and tasks are separable
3. `superpowers:executing-plans` when the plan should execute inline
4. `superpowers:requesting-code-review` before closing a significant milestone

Repository-specific boundaries:

- repository source-of-truth files still win
- `docs/superpowers/plans/` is a workflow plan area, not a stronger protocol layer
- verified milestones in this repo still end with commit + push unless the user says otherwise
- live validation claims must stay separated from fixture or mock validation claims

---

## Commit And Push Rule

After verification:

1. review the changed scope
2. stage only the intended files
3. commit with a specific message
4. push to `origin main`

Do not leave verified source changes only in local working state unless the user explicitly asks not to push yet.

---

## Reporting Rule

After each synced task or milestone, report:

1. what changed
2. what was verified
3. what commit was created
4. whether it was pushed
5. what is still unfinished

Do not blur:

- completed
- partially completed
- not started
- blocked

---

## Secrets And Local Config

Sync source code and checked-in docs to GitHub.

Do not push machine-local secrets such as:

- real `.env` files
- provider tokens
- local auth credentials
- machine-specific private config

Checked-in templates are allowed, such as:

- `.env.room.example`

Real secret values stay local.

---

## Current Repository-Specific Expectation

For this repository, the default expectation is:

- `/room` and `/debate` source changes should be committed and pushed after each verified milestone
- runtime outputs under `artifacts/` should stay out of commits unless they are intentionally checked-in fixtures
- live provider validation should be reported separately from fixture-driven validation

This is how development remains traceable across local work, GitHub history, and future agent handoff.
