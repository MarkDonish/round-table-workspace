# Agent Consumer Quickstart

This page is for people who clone the repository and want to know whether the round-table system is usable from their local agent host.

It applies to:

- Codex local users
- Claude Code users
- other local CLI agents that can read a prompt and return JSON

## One-Command Self Check

Run this from the repository root:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

This command is safe for a fresh clone:

- it does not require provider URLs
- it does not require a paid third-party account
- it does not send requests to real provider endpoints
- it treats `reports/` and `artifacts/` as historical/output material, not source
- it writes JSON and Markdown evidence under the selected `--state-root`

Use the faster preflight mode when you only need source and readiness checks:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --quick \
  --state-root /tmp/round-table-agent-consumer-self-check-quick
```

## Fresh Release Checkout Audit

Maintainers can verify that a tagged release works from a fresh cloned checkout
instead of only the current working tree:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.1 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

The audit clones the requested ref, runs the consumer self-check, validates the
Claude Code project-skill structure, and reruns the strict release gate from the
fresh checkout. It still does not require provider URLs or paid third-party
accounts.

## How To Interpret PASS

A passing self-check means:

- source-truth roots exist
- the release readiness gate has no P0 blockers for the local-first scope
- Claude Code project-skill discovery structure is valid
- local agent host lanes are classified as `missing`, `blocked`, `pending`, or `live_passed`
- in default mode, fixture-backed generic adapter and JSON wrapper validation passed

It does not mean:

- every possible third-party CLI is installed
- a paid Claude Code account is logged in
- provider-live execution passed
- every host can be claimed as live-supported

Only a matrix row with `matrix_status=live_passed` can be claimed as real host-live support.

## Codex Path

Codex is the current local-first mainline.

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

If this passes, the Codex local `/room`, `/debate`, and `/room -> /debate` mainline is working on that machine.

## Claude Code Path

Without a paid or logged-in Claude Code account, you can still validate the project-skill adapter and fixture route:

```bash
python3 .claude/scripts/validate_project_skills.py

python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

After the local account is logged in and entitled, run:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --preflight-only \
  --state-root /tmp/round-table-claude-code-live-preflight

python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --smoke-only \
  --state-root /tmp/round-table-claude-code-live-smoke

python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live
```

If the preflight reports `claude_code_not_logged_in`, the adapter is prepared but the real Claude Code live lane is blocked by account authentication. If `--smoke-only` passes, treat it as local CLI execution evidence only; claim real default Claude Code `/room -> /debate` support only when the full wrapper reports `claimable_as_default_claude_code_host_live=true`.

## Generic Local Agent Path

Use the host decision tree in `docs/local-agent-host-recipes.md` before trying
to claim real host support. That document is checked against the runtime
inventory candidates by:

```bash
python3 .codex/skills/room-skill/runtime/host_recipes_consistency_check.py \
  --output-json /tmp/round-table-host-recipes-consistency.json
```

Inventory local CLI hosts first:

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py \
  --output-json /tmp/round-table-agent-host-inventory.json
```

Build a durable host validation matrix:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

If a host is intentionally not installed or not in scope for this machine, make
that explicit instead of treating the missing CLI as unresolved work:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --skip-host 'gemini_cli=not installed on this machine; not claimed' \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

Generate a focused live-lane evidence summary before making support claims:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

The live-lane report accepts the same skip markers:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --skip-host 'gemini_cli=not installed on this machine; not claimed' \
  --state-root /tmp/round-table-live-lane-evidence
```

This report also states that provider URLs are not required for the local
mainline and are not the meeting room.

The matrix report includes both `recommended_validation_command` for human
copy/paste and `recommended_validation_argv` for scripts or another local agent
that should not re-parse nested shell quotes.

Validate a real host command only after the host can run non-interactively:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label <host_id> \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-<host-id>-validation
```

## Provider Boundary

The meeting flow is local-agent based. Provider URLs are not meeting rooms and are not required for the Codex local mainline.

Only use the provider lane when intentionally validating a Chat Completions-compatible fallback provider:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py \
  --output-json /tmp/round-table-chat-completions-readiness.json
```
