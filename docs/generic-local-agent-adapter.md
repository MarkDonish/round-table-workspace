# Generic Local Agent Adapter

This document is the source of truth for adapting `/room` and `/debate` to local agents beyond Codex and Claude Code.

## Goal

Any local agent host should be able to run the round-table prompt tasks if it can:

1. read a task prompt from stdin or a prompt file
2. read structured JSON input from a file if needed
3. return one JSON object on stdout or write one JSON object to an output file
4. run from the repository root without mutating runtime state directly

The runtime bridge stays in this repository. The local agent only produces prompt JSON.

## Contract

The checked-in adapter is:

```text
.codex/skills/room-skill/runtime/generic_agent_executor.py
```

It passes the full task prompt on stdin and also exposes these placeholders in `--agent-command`:

```text
{prompt_file}
{input_file}
{output_file}
{repo_root}
```

It also injects these environment variables:

```text
ROUND_TABLE_PROMPT_FILE
ROUND_TABLE_INPUT_JSON
ROUND_TABLE_OUTPUT_JSON
ROUND_TABLE_REPO_ROOT
ROUND_TABLE_ROOM_ID
ROUND_TABLE_DEBATE_ID
```

The agent command may either print one JSON object to stdout or write one JSON object to `ROUND_TABLE_OUTPUT_JSON`.

## One-Command Validation

Before validating a real host, inventory the local machine:

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py
```

Run the default offline validation with the checked-in fixture agent:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py
```

Validate a real local agent command:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_agent \
  --agent-command "my-agent run --json" \
  --state-root /tmp/round-table-my-agent-validation
```

If the agent prefers file arguments:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_agent \
  --agent-command "my-agent run --prompt {prompt_file} --input {input_file} --output {output_file}" \
  --state-root /tmp/round-table-my-agent-validation
```

Passing validation means:

- the agent smoke test returned parseable `{"ok": true}`
- `/room` completed through the generic adapter
- `/room` persisted a valid handoff packet
- `/debate` consumed the packet
- the final `/room -> /debate` chain reported `full_chain_passed: true`

## Minimal Agent Behavior

For each prompt call, the local agent must:

1. follow the prompt contract in `prompts/`
2. return only one top-level JSON object
3. avoid Markdown wrappers around JSON
4. avoid writing room or debate state files itself
5. avoid reading historical `reports/` as current handoff input

The runtime bridge validates, normalizes, persists, and rejects bad output.

## Boundary

- This is not a provider URL lane.
- This is not a second implementation of `/room` or `/debate`.
- This does not require a Claude subscription.
- Real third-party agent commands still need their own live validation run.
- Fixture validation proves the adapter contract, not the quality of a specific real agent model.
