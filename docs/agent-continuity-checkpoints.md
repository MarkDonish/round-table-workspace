# Agent Continuity Checkpoints

This document defines the repo-local alternative to host-level agent memory.

## Boundary

Some hosts expose historical memory to the agent as read-only. In that case the
agent can read prior context but cannot mutate the host-level memory store.

This repository therefore provides a project-local checkpoint command:

```bash
python3 .codex/skills/room-skill/runtime/development_checkpoint.py \
  --title "Development Checkpoint" \
  --topic "What changed" \
  --decision "Decision to preserve" \
  --completed "Completed item" \
  --next-task "Next task"
```

By default, the command writes Markdown and JSON under:

```text
reports/checkpoints/generated/
```

These files are durable project history. They are not protocol source of truth.

## What It Saves

The checkpoint captures:

- current git status, recent log, and remotes
- active source-truth boundary
- topics, decisions, quotes, completed work, partial work, unfinished work,
  blockers, verification evidence, code references, and next tasks provided by
  the agent
- optional release readiness summary when `--include-release-readiness` is used

## What It Does Not Do

- It does not edit Codex global memory.
- It does not edit Claude Code memory.
- It does not replace `AGENTS.md`, `README.md`, `docs/`, `prompts/`,
  `examples/`, `.codex/skills/`, or `.claude/skills/`.
- It does not make `reports/` an implementation source.
- It does not claim provider-live or host-live validation by itself.

## Recommended Use

Use this command when:

- a session is about to end or context is nearly full
- a network interruption is likely
- another machine or another local agent host will continue the same work
- a decision should be recoverable without relying on chat history

Use `/tmp` as `--output-dir` for validation-only smoke tests. Use the default
repo path when the checkpoint itself should be kept as durable project history.

## Source Boundary

If a checkpoint conflicts with active source files, the active source files win.

Active source:

- `AGENTS.md`
- `README.md`
- `LAUNCH.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- `.claude/skills/`

Historical/output:

- `reports/`
- `artifacts/`
