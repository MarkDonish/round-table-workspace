# Claude Code Host Live Validation - 2026-04-26

This report is historical evidence. Active claim rules remain in:

- `docs/claude-code-skill-adapter.md`
- `docs/local-agent-host-recipes.md`
- `docs/release-readiness.md`
- `docs/release-candidate-scope.md`

## Result

- Result: `PASS`
- Host: `claude_code`
- Tested command: `claude -p --input-format text --output-format text --no-session-persistence --tools ""`
- Claude Code version: `2.1.119 (Claude Code)`
- Auth state at validation time: `loggedIn=true`, `apiProvider=firstParty`
- Validation level: `full_integration`
- Support claim: `real_claude_code_host_live_validated`
- Claimable as host live: `true`
- Claimable as default Claude Code host live: `true`

## Pass Criteria

```json
{
  "cli_available": true,
  "auth_logged_in": true,
  "agent_smoke_ready": true,
  "room_flow_passed": true,
  "handoff_packet_forwarded": true,
  "debate_flow_passed": true,
  "full_chain_passed": true
}
```

## Validation Commands

Preflight:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --preflight-only \
  --state-root /tmp/round-table-claude-code-live-preflight-20260426
```

Smoke:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --smoke-only \
  --state-root /tmp/round-table-claude-code-live-smoke-20260426
```

Full integration:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py \
  --state-root /tmp/round-table-claude-code-live-full-20260426 \
  --agent-timeout-seconds 360
```

## Runtime Evidence

- Run id: `claude-code-live-f90fc459`
- Flow id: `claude-code-live-f90fc459-integration`
- Room id: `claude-code-live-f90fc459-integration-room`
- Debate id: `claude-code-live-f90fc459-integration-debate`
- Integration report: `/private/tmp/round-table-claude-code-live-full-20260426/claude-code-live-f90fc459/integration/claude-code-live-f90fc459-integration/integration-report.json`
- Room validation report: `/private/tmp/round-table-claude-code-live-full-20260426/claude-code-live-f90fc459/integration/claude-code-live-f90fc459-integration/rooms/claude-code-live-f90fc459-integration-room/validation-report.json`
- Debate validation report: `/private/tmp/round-table-claude-code-live-full-20260426/claude-code-live-f90fc459/integration/claude-code-live-f90fc459-integration/debates/claude-code-live-f90fc459-integration-debate/validation-report.json`
- Handoff packet: `/private/tmp/round-table-claude-code-live-full-20260426/claude-code-live-f90fc459/integration/claude-code-live-f90fc459-integration/rooms/claude-code-live-f90fc459-integration-room/handoff/packet-turn-002.json`

## Claim Boundary

This is real host-live evidence for the tested Mac account and default Claude Code wrapper command.

Do not use this report to claim:

- every Claude Code account is entitled
- every machine has Claude Code installed and logged in
- Gemini CLI, OpenCode, Aider, Goose, or Cursor Agent support
- provider-live support
- universal production stability across all local agent hosts
