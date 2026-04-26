# Local Agent Host Recipes

This document is the source of truth for real local host readiness recipes beyond the validated Codex mainline.

## Purpose

The generic adapter contract is already defined in `docs/generic-local-agent-adapter.md`. This file explains how to apply that contract to real local agent hosts without pretending that fixture validation is the same as host-live validation.

If a host can run non-interactively but does not emit clean JSON, use `docs/third-party-agent-wrapper-recipes.md` and validate the wrapped command instead of the raw command.

## Fast Decision Tree

Use this order for every non-Codex host:

1. Run `agent_consumer_self_check.py` to confirm the repo-local launch scope.
2. Run `agent_host_inventory.py` to classify installed, missing, auth-blocked, or ready hosts.
3. If the host is missing, install it or skip that host on this machine.
4. If the host is auth-blocked, log in or skip that host; do not run live validation and call it passed.
5. If the host is installed and can run non-interactively, validate the wrapped command with `generic_agent_adapter_validation.py`.
6. Claim support only when the matrix row is `matrix_status=live_passed`.

Provider URLs are not required for this path. This is a local CLI agent path,
not the optional Chat Completions-compatible provider lane.

## Host Coverage Matrix

This table mirrors the checked-in candidates from
`.codex/skills/room-skill/runtime/agent_host_inventory.py`.

| Host id | Display name | Executable | First gate | Validation path | Claim rule |
|---|---|---|---|---|---|
| `claude_code` | Claude Code | `claude` | `claude auth status` plus `claude_code_live_validation.py --preflight-only` | Use `claude_code_live_validation.py --smoke-only` for local CLI execution, then the full wrapper for `/room -> /debate` | Claim default Claude Code support only when the full wrapper reports `claimable_as_default_claude_code_host_live=true`, or matrix reports `matrix_status=live_passed` for the real Claude command |
| `gemini_cli` | Gemini CLI | `gemini` | `agent_host_inventory.py` must find `gemini` on `PATH` | Provide a non-interactive stdin/file command through `generic_agent_json_wrapper.py` | Claim only after `generic_agent_adapter_validation.py` returns full pass criteria |
| `opencode` | OpenCode | `opencode` | `agent_host_inventory.py` must find `opencode` on `PATH` | Provide a non-interactive stdin/file command through `generic_agent_json_wrapper.py` | Claim only after `generic_agent_adapter_validation.py` returns full pass criteria |
| `aider` | Aider | `aider` | `agent_host_inventory.py` must find `aider` on `PATH` and the command must not require an interactive TTY | Prefer a small local non-interactive wrapper, then validate that wrapper | Claim only after `generic_agent_adapter_validation.py` returns full pass criteria |
| `goose` | Goose | `goose` | `agent_host_inventory.py` must find `goose` on `PATH` | Provide a non-interactive stdin/file command through `generic_agent_json_wrapper.py` | Claim only after `generic_agent_adapter_validation.py` returns full pass criteria |
| `cursor_agent` | Cursor Agent | `cursor-agent` | `agent_host_inventory.py` must find `cursor-agent` on `PATH` | Provide a non-interactive stdin/file command through `generic_agent_json_wrapper.py` | Claim only after `generic_agent_adapter_validation.py` returns full pass criteria |

Run the docs consistency check after editing this table:

```bash
python3 .codex/skills/room-skill/runtime/host_recipes_consistency_check.py \
  --output-json /tmp/round-table-host-recipes-consistency.json
```

This check is intentionally based on the checked-in inventory candidate list.
It does not install or run real third-party hosts.

## Inventory First

For a fresh clone or a new local agent host, start with the consumer self-check:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

This validates the claim-safe local-first scope without requiring provider URLs
or paid third-party accounts. Use `docs/agent-consumer-quickstart.md` for the
human-facing path.

Run:

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py
```

This checks common local agent CLIs on `PATH` and reports whether each host is:

- missing
- installed but not yet live-validated
- blocked by auth
- ready for live validation

The inventory does not execute `/room` or `/debate`. It only tells you whether a real host is available enough to attempt the next validation step.

## Validation Matrix

Use the matrix command when you need a durable report that separates missing, auth-blocked, pending, passed, and failed host lanes:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

By default this command does not force real third-party agent execution. It writes JSON and Markdown evidence and keeps blocked hosts blocked instead of pretending they passed.

For every host with a selectable command, the matrix writes both:

- `recommended_validation_command`: a human-facing shell command rendered from the argv.
- `recommended_validation_argv`: the canonical machine-readable argv list for scripts, CI, or another local agent.

Use `recommended_validation_argv` when nested quoting is risky. The Markdown report prints both forms so another machine can copy the command or replay the argv without reconstructing shell quotes.

When inventory reports a host as `ready_for_live_validation`, run only those ready hosts:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-live-ready \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

For an installed host that needs an explicit command override:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-installed \
  --agent-command "my_agent=my-agent run --prompt {prompt_file} --input {input_file} --output {output_file}" \
  --state-root /tmp/round-table-my-agent-host-validation
```

Only `matrix_status: "live_passed"` may be used as real host-live support evidence.

Fixture validation is not host-live evidence.

## Claude Code Recipe

Claude Code has two layers in this repository:

- Project skill discovery: `.claude/skills/room/SKILL.md` and `.claude/skills/debate/SKILL.md`
- Runtime host validation: `.codex/skills/room-skill/runtime/claude_code_live_validation.py`

Preflight:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --preflight-only \
  --state-root /tmp/round-table-claude-code-live-preflight
```

Local CLI smoke after preflight passes:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --smoke-only \
  --state-root /tmp/round-table-claude-code-live-smoke
```

Full live validation after the account is entitled and logged in:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

Interpret the wrapper by level:

- `validation_level=preflight_only` proves only CLI presence and auth state.
- `validation_level=smoke_only` proves the local Claude Code CLI can answer a minimal JSON task.
- `validation_level=full_integration` with `claimable_as_default_claude_code_host_live=true` is the only default Claude Code wrapper result that proves real `/room -> /debate` host-live support.

If preflight reports `claude_code_not_logged_in`, do not mark Claude Code live validation as passed. If smoke passes but full integration times out or fails, keep the lane as partial and inspect the persisted trace before claiming support.

## Generic stdin Agent Recipe

Use this when the agent command accepts prompt text on stdin and returns one JSON object on stdout:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_agent \
  --agent-command "my-agent run --json" \
  --state-root /tmp/round-table-my-agent-validation
```

Pass only if the report returns:

```json
{
  "ok": true,
  "pass_criteria": {
    "agent_smoke_ready": true,
    "room_flow_passed": true,
    "handoff_packet_forwarded": true,
    "debate_flow_passed": true,
    "full_chain_passed": true
  }
}
```

## File-Based Agent Recipe

Use this when the agent prefers explicit prompt/input/output files:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_agent \
  --agent-command "my-agent run --prompt {prompt_file} --input {input_file} --output {output_file}" \
  --state-root /tmp/round-table-my-agent-validation
```

The adapter replaces these placeholders:

- `{prompt_file}`
- `{input_file}`
- `{output_file}`
- `{repo_root}`

The agent may also read:

- `ROUND_TABLE_PROMPT_FILE`
- `ROUND_TABLE_INPUT_JSON`
- `ROUND_TABLE_OUTPUT_JSON`
- `ROUND_TABLE_REPO_ROOT`
- `ROUND_TABLE_ROOM_ID`
- `ROUND_TABLE_DEBATE_ID`

## Wrapper Recipe

If a real agent cannot reliably emit a clean JSON object, create a small local wrapper that:

1. reads stdin or `ROUND_TABLE_PROMPT_FILE`
2. calls the real agent
3. extracts or repairs one JSON object
4. writes it to `ROUND_TABLE_OUTPUT_JSON`
5. exits non-zero if no valid JSON object is available

Then validate the wrapper, not the raw agent command:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_wrapped_agent \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-my-wrapped-agent-validation
```

Validate the checked-in wrapper itself before blaming a real host:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py
```

## Interpreting Inventory

If inventory shows `live_readiness: "blocked_auth"`, do not run or report full live validation until the host account is logged in and entitled.

If inventory shows `live_readiness: "missing_cli"`, install that host first or skip its recipe.

If inventory shows `live_readiness: "installed_needs_agent_contract_validation"`, run `generic_agent_adapter_validation.py` with that host's real command before claiming support.

If inventory shows `live_readiness: "ready_for_live_validation"`, run the host-specific live wrapper when one exists, otherwise run the generic adapter validation command with the real host command.

## Boundary

- Do not treat inventory as live validation.
- Do not treat a matrix `blocked`, `missing_cli`, or `pending_live_validation` row as support evidence.
- Do not treat fixture validation as proof that a real third-party model follows the prompt contract.
- Do not require provider URLs for the local mainline.
- Do not let real agent wrappers mutate `/room` or `/debate` state directly.
