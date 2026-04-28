# P2 Provider and OpenCode Live Lane Closure - 2026-04-28

This is a historical report. It records the final local attempts for the
remaining P2 provider/OpenCode lanes before launch. Current source-of-truth
entry points remain `README.md`, `docs/`, `prompts/`, `examples/`,
`.codex/skills/`, and `.claude/skills/`.

## Scope

- Provider lane: optional Chat Completions-compatible fallback/live validation.
- Host lane: OpenCode local CLI through the checked-in generic local-agent
  wrapper.
- Launch impact: neither lane blocks the current Codex local mainline release.
- Claim boundary: neither real provider-live nor OpenCode host-live support is
  claimable from this Mac after this run.

## Provider Live Lane

Readiness command:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py \
  --output-json /tmp/round-table-chat-completions-readiness-current.json
```

Result:

- `ready_for_live_run=false`
- `local_mainline_requires_provider_url=false`
- `room_provider_ready=false`
- `debate_provider_ready=false`
- Room blocker: `Missing ROOM_CHAT_COMPLETIONS_URL.`
- Debate blocker: `Missing DEBATE_CHAT_COMPLETIONS_URL. Fallbacks checked:
  ROOM_CHAT_COMPLETIONS_URL.`

Live validation was also attempted against the local `.env.room` and
`.env.debate` files. It failed before any provider request because the real
provider URL values are missing:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live-v0.1.2-attempt
```

Decision:

- This is externally blocked until a real provider URL/model/auth config is
  intentionally supplied locally.
- This is not a repository implementation blocker.
- This is not required for local `/room`, `/debate`, or `/room -> /debate`.

## OpenCode Host-Live Lane

Local OpenCode state was checked before retrying the matrix:

- OpenCode version: `1.14.27`
- State DB integrity: `PRAGMA integrity_check;` returned `ok`
- Backup location: `/tmp/round-table-opencode-db-backup-20260428/`
- WAL checkpoint repair command returned `0|0|0`:

```bash
sqlite3 /Users/markdonish/.local/share/opencode/opencode.db \
  'PRAGMA wal_checkpoint(TRUNCATE);'
```

A direct minimal OpenCode smoke passed after the checkpoint:

```bash
/Users/markdonish/.opencode/bin/opencode run \
  --model opencode/gpt-5-nano \
  --pure \
  --dir /Users/markdonish/Documents/Codex/2026-04-21-mac-github-https-github-com-mark/round-table-workspace \
  'Reply with exactly: OPENCODE_OK'
```

Observed output included:

```text
OPENCODE_OK
```

The full host-live matrix was retried:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-installed \
  --force-host opencode \
  --skip-host 'gemini_cli=not installed on this Mac; not claimed' \
  --skip-host 'aider=not installed on this Mac; not claimed' \
  --skip-host 'goose=not installed on this Mac; not claimed' \
  --skip-host 'cursor_agent=not installed on this Mac; not claimed' \
  --state-root /tmp/round-table-opencode-host-validation-after-wal-fix \
  --agent-timeout-seconds 1800
```

Result:

- Matrix `ok=false`
- OpenCode row: `matrix_status=live_failed`
- Claim: `real_host_live_validation_failed`
- Persisted matrix report:
  `/tmp/round-table-opencode-host-validation-after-wal-fix/local-agent-host-validation-matrix.md`
- Persisted adapter report:
  `/tmp/round-table-opencode-host-validation-after-wal-fix/opencode/generic-agent-adapter-validation-report.json`

The adapter failure remained inside the wrapped OpenCode CLI:

```text
wrapped agent exited with code 1
opencode wrapper retrying after transient local OpenCode failure (attempt 1/2)
Failed to run the query 'PRAGMA wal_checkpoint(P...
```

The newest OpenCode log also showed upstream model pressure during the same
period:

```text
too_many_requests
```

Decision:

- OpenCode can run a direct minimal CLI smoke on this Mac.
- OpenCode still cannot be claimed as `/room -> /debate` host-live support,
  because the checked-in matrix did not pass.
- The remaining failure is in OpenCode's local state/upstream execution lane,
  not in the checked-in Codex local mainline.

## Current Launch Decision

- Codex local mainline remains launchable.
- Claude Code host-live remains claimable only for the previously validated
  Mac/account evidence.
- Provider live remains optional and blocked on real local provider config.
- OpenCode host-live remains P2 non-claimable until the host matrix returns
  `matrix_status=live_passed`.

Do not widen public support claims based on provider readiness, mock provider
regression, OpenCode inventory, OpenCode wrapper presence, or direct OpenCode
smoke alone.
