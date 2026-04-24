# Local Agent Host Recipes

This document is the source of truth for real local host readiness recipes beyond the validated Codex mainline.

## Purpose

The generic adapter contract is already defined in `docs/generic-local-agent-adapter.md`. This file explains how to apply that contract to real local agent hosts without pretending that fixture validation is the same as host-live validation.

If a host can run non-interactively but does not emit clean JSON, use `docs/third-party-agent-wrapper-recipes.md` and validate the wrapped command instead of the raw command.

## Inventory First

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

Full live validation after the account is entitled and logged in:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

If preflight reports `claude_code_not_logged_in`, do not mark Claude Code live validation as passed.

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
- Do not treat fixture validation as proof that a real third-party model follows the prompt contract.
- Do not require provider URLs for the local mainline.
- Do not let real agent wrappers mutate `/room` or `/debate` state directly.
