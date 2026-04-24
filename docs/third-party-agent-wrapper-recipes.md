# Third-Party Agent Wrapper Recipes

This document is the source of truth for connecting real local agent CLIs that do not reliably emit a clean JSON object.

## Why The Wrapper Exists

`generic_agent_executor.py` already supports any local CLI that returns one JSON object. Real agents often add:

- Markdown code fences
- explanatory text before or after JSON
- progress logs on stdout
- file output mixed with status messages

`generic_agent_json_wrapper.py` normalizes those outputs before the runtime bridge sees them. The wrapper does not write `/room` or `/debate` state. It only returns one prompt JSON object to the existing runtime bridge.

## Wrapper Command

Use this shape when validating a real agent:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_wrapped_agent \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-my-wrapped-agent-validation
```

The wrapped command receives the task prompt on stdin and can also use:

- `ROUND_TABLE_PROMPT_FILE`
- `ROUND_TABLE_INPUT_JSON`
- `ROUND_TABLE_OUTPUT_JSON`
- `ROUND_TABLE_FINAL_OUTPUT_JSON`
- `ROUND_TABLE_WRAPPER_RAW_OUTPUT_JSON`
- `ROUND_TABLE_REPO_ROOT`
- `{prompt_file}`
- `{input_file}`
- `{output_file}`
- `{raw_output_file}`
- `{repo_root}`

Prefer `{raw_output_file}` for raw agent file output. The wrapper writes the cleaned JSON object back to the final `ROUND_TABLE_OUTPUT_JSON` path expected by the runtime adapter.

## Offline Wrapper Validation

Run:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py \
  --state-root /tmp/round-table-generic-agent-json-wrapper-validation
```

This validates three common noisy-output cases:

- Markdown fenced JSON
- stdout logs around JSON
- noisy file output

Passing this proves the wrapper layer works. It does not prove a real third-party agent follows the prompt contracts.

## Host Templates

These are starting templates, not live validation claims. Confirm each CLI's current help output on the target machine before claiming support.

| Host | Template | Notes |
|---|---|---|
| Claude Code | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command 'claude -p --input-format text --output-format text --no-session-persistence --tools ""'` | Current Mac has CLI installed but `agent_host_inventory.py` reports `not_logged_in`; use `claude_code_live_validation.py` after login. |
| Gemini CLI | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<gemini command that reads stdin or {prompt_file}>'` | Inventory currently reports missing CLI on this Mac. |
| OpenCode | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<opencode command that reads stdin or {prompt_file}>'` | Validate stdout/file JSON behavior before claiming live support. |
| Aider | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<aider command that can run non-interactively against {prompt_file}>'` | Interactive defaults usually need a non-interactive wrapper script. |
| Goose | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<goose command that reads stdin or {prompt_file}>'` | Use `{raw_output_file}` if the host supports explicit output files. |
| Cursor Agent | `python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<cursor-agent command that reads stdin or {prompt_file}>'` | Inventory currently reports missing CLI on this Mac. |

## Pass Standard

Only claim real host support after:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label <host_id> \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-<host-id>-validation
```

The report must return:

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

## Boundaries

- This wrapper is for local CLI agents, not provider URLs.
- Fixture wrapper validation is not a real host-live pass.
- The wrapper may clean JSON shape, but it must not invent missing prompt fields.
- The runtime bridge remains the only writer of room/debate state.
- If a host cannot run non-interactively, create a host-specific local script and validate that script through this wrapper.
