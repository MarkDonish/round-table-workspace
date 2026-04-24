# Host Adapter Architecture

This document is the source of truth for making the round-table runtime work across Codex, Claude Code, and other local agents.

## Goal

The project must not depend on one vendor-specific prompt host. `/room` and `/debate` keep their protocol contracts in `prompts/` and their state/runtime logic in `.codex/skills/*/runtime/`; host-specific execution is isolated behind adapters.

Claude Code also gets a native project-skill discovery layer under `.claude/skills/`. Those files are thin adapters that point back to the canonical sources; they must not fork the protocol.

## Runtime Layers

| Layer | Responsibility | Source of truth |
|---|---|---|
| Protocol prompts | Define JSON input/output contracts for room selection, room chat, summary, upgrade, debate roundtable, review, and follow-up | `prompts/` |
| Runtime bridge | Own state, validation, persistence, packet handoff, and runner orchestration | `.codex/skills/room-skill/runtime/`, `.codex/skills/debate-roundtable-skill/runtime/` |
| Host adapter | Execute one prompt task through a concrete local agent or fallback provider and return one JSON object | `generic_agent_executor.py`, `local_codex_executor.py`, `chat_completions_executor.py` |
| Claude Code skill adapter | Provide native Claude Code project skill discovery for `/room` and `/debate` | `.claude/skills/room/SKILL.md`, `.claude/skills/debate/SKILL.md` |

## Supported Adapters

| Adapter | Executor name | Current status | Intended use |
|---|---|---|---|
| Canonical fixture | `fixture` | Validated | Deterministic protocol/runtime regression |
| Generic local CLI agent | `generic_cli` | Adapter path validated with `generic_fixture_agent.py` | Any local agent CLI that can read a task prompt from stdin and return JSON |
| Claude Code local CLI | `claude_code` | Adapter route validated with `generic_fixture_agent.py`; live wrapper checked in; current Mac preflight is blocked by `claude_code_not_logged_in` | Claude Code or Claude-compatible local command |
| Codex local child task | `local_codex` | Mac and Windows mainline validated | Codex-first local runtime lane |
| Chat Completions provider | `chat_completions` | Mock provider validated; real live provider pending | Fallback/regression lane, not the local mainline |

## Generic CLI Contract

`generic_agent_executor.py` runs a local command with these guarantees:

- The full task prompt is passed on `stdin`.
- The same task prompt is also written to `{prompt_file}`.
- The structured JSON input is written to `{input_file}`.
- The agent may either print one JSON object to `stdout` or write one JSON object to `{output_file}`.
- The command runs from the repository root.
- Trace files are written beside each prompt call when the runner supplies a trace base.

Supported command placeholders:

```text
{prompt_file}
{input_file}
{output_file}
{repo_root}
```

Injected environment variables:

```text
ROUND_TABLE_PROMPT_FILE
ROUND_TABLE_INPUT_JSON
ROUND_TABLE_OUTPUT_JSON
ROUND_TABLE_REPO_ROOT
ROUND_TABLE_ROOM_ID
ROUND_TABLE_DEBATE_ID
```

`ROUND_TABLE_ROOM_ID` and `ROUND_TABLE_DEBATE_ID` are supplied by the room/debate runners when applicable.

## Commands

Smoke-test a generic local agent command:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_executor.py \
  --check-agent-exec \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py"
```

Run the full `/room -> /debate` chain through the generic CLI adapter:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor generic_cli \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-generic-cli-integration
```

Run the same adapter route under the Claude Code executor name:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

When a real Claude Code CLI is installed and accepts prompt text on stdin, pass its command with `--agent-command`, or set `CLAUDE_CODE_AGENT_COMMAND`. If no override is supplied, `claude_code` defaults to `claude -p`.

Run the checked-in Claude Code live wrapper:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --preflight-only \
  --state-root /tmp/round-table-claude-code-live-preflight

python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

The wrapper first runs `claude --version` and `claude auth status`. If auth reports `loggedIn=false`, the wrapper writes a blocked report instead of pretending the host-live lane passed.

Validate the Claude Code project-skill adapter layer without a Claude subscription:

```bash
python3 .claude/scripts/validate_project_skills.py
```

## Boundaries

- `/room` and `/debate` remain local runtime protocols; provider URLs are not the mainline.
- The generic adapter proves host portability at the CLI contract layer; each real third-party agent still needs its own live validation run.
- Host adapters must not mutate room or debate state directly. They return candidate prompt JSON only; the runtime bridge remains the only state writer.
- `.claude/skills/` is a discovery layer for Claude Code users, not a second implementation source.
