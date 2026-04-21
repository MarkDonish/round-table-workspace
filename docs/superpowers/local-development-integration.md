# Local Superpowers Development Integration

> Purpose: embed the locally installed Superpowers workflow into active development on this repository without letting workflow tooling override repository source of truth.
> Last reviewed: 2026-04-21

---

## Role

This document defines how local Superpowers should participate in development for this repository.

It is a workflow layer, not a protocol replacement.

That means:

- `AGENTS.md`, `README.md`, `docs/`, `prompts/`, `examples/`, and `.codex/skills/` remain source of truth
- local Superpowers improves planning, execution discipline, and review quality
- local Superpowers must not override checked-in repository rules

Priority remains:

1. user instructions
2. repository instructions and source files
3. local Superpowers workflow
4. default host behavior

---

## Expected Local Install

The local Superpowers install on this machine currently resolves under:

- `~/.codex/superpowers/skills/`

The most relevant workflow skills for this repository are:

- `superpowers:using-superpowers`
- `superpowers:writing-plans`
- `superpowers:subagent-driven-development`
- `superpowers:executing-plans`
- `superpowers:requesting-code-review`

If the local install is missing, continue with the repository workflow and report that Superpowers was unavailable.

---

## Integration Rule

Use local Superpowers as a quality multiplier for process-heavy work, especially when the task is:

- multi-step
- easy to overclaim
- cross-file
- validation-heavy
- suitable for plan-first execution

Do not use Superpowers as an excuse to skip repository startup analysis.

The repository startup sequence still comes first:

1. inspect repo state
2. read source-of-truth files
3. identify the current blocker
4. then decide which Superpowers workflow should participate

---

## Required Workflow Mapping

### 1. Session Start

If the host supports local Superpowers skill loading, begin with:

- `superpowers:using-superpowers`

This is the global workflow initializer.
It does not replace repo-local instructions.

### 2. Plan Creation

When the task is multi-step or needs explicit decomposition before edits:

- use `superpowers:writing-plans`

Repository-specific rule:

- save plans under `docs/superpowers/plans/`
- keep plans implementation-facing and repo-relative
- treat plans as workflow artifacts, not stronger than checked-in protocol docs

### 3. Plan Execution

When a plan already exists:

- prefer `superpowers:subagent-driven-development` if the host supports subagents and the tasks are reasonably separable
- use `superpowers:executing-plans` when execution should stay inline or the host cannot support the recommended subagent workflow

Repository-specific adaptation:

- do not let Superpowers execution bypass `docs/development-sync-protocol.md`
- verified milestones in this repository are still expected to end with commit + push unless the user says otherwise
- this repository currently develops on `main` by explicit user direction and checked-in sync protocol, so do not import a generic “never touch main” rule without checking current repo instructions

### 4. Review Gate

Before closing a major feature or verified milestone:

- use `superpowers:requesting-code-review`

Minimum trigger points for this repository:

- after a high-risk runtime change
- before pushing a major behavior change
- after finishing a plan-driven batch

### 5. Finish And Report

After Superpowers-assisted execution:

- run the most relevant local verification
- commit only verified source changes
- push to `origin/main`
- report completed / partial / blocked status explicitly

This repository's reporting format still comes from `docs/development-sync-protocol.md`.

---

## Repository-Specific Guardrails

When Superpowers participates in this repository, keep these rules explicit:

1. `docs/`, `prompts/`, `examples/`, and `.codex/skills/` remain the real source layers.
2. `reports/` and `artifacts/` remain non-source even if a workflow skill produces useful evidence there.
3. Plan documents under `docs/superpowers/plans/` do not override active protocol documents.
4. Superpowers should improve execution discipline, not increase repo churn.
5. If external live validation is blocked by missing secrets or provider config, use fixture or mock validation where available and report the live blocker plainly.

---

## Practical Default

For this repository, the default development loop should now be:

1. repo startup analysis from checked-in source
2. `superpowers:writing-plans` for multi-step work
3. `superpowers:subagent-driven-development` when supported, else `superpowers:executing-plans`
4. `superpowers:requesting-code-review` before merging a meaningful milestone
5. local verification
6. commit
7. push
8. explicit progress report

This is the intended meaning of “embed local Superpowers into the development process” for this repository.
