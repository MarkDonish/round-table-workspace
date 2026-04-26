# /room Runtime Bridge

This directory contains the checked-in host bridge behind `/room`.

It does not replace the prompts. Instead, it does the host-side work that the prompts are not allowed to do:

- validate prompt JSON outputs
- assign `turn_role`
- persist room state
- update `silent_rounds`, `turn_count`, `last_stage`, and `recent_log`
- persist summary snapshots
- validate and persist `/room -> /debate` handoff packets
- call the checked-in `/debate` packet preflight before persisting handoff acceptance

## Main Entry

Run:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py --help
```

For the checked-in end-to-end validation runner:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py --help
```

For the checked-in `/room -> /debate` integration runner:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py --help
```

For the checked-in local child-agent executor:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py --help
```

For the checked-in generic local agent CLI adapter:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_executor.py --help
```

For the checked-in generic local agent adapter validation kit:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py --help
```

For the checked-in generic agent JSON wrapper:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --help
```

For the checked-in generic agent JSON wrapper validation:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py --help
```

For the checked-in local agent host inventory:

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py --help
```

For the checked-in local agent host validation matrix:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py --help
```

For the checked-in host/provider live-lane evidence report:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py --help
```

For the checked-in agent consumer self-check:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py --help
```

For the checked-in post-release consumer audit:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py --help
```

For the checked-in GitHub Release publication status check:

```bash
python3 .codex/skills/room-skill/runtime/github_release_publication_check.py --help
```

For the checked-in real Claude Code local CLI live validation wrapper:

```bash
python3 .codex/skills/room-skill/runtime/claude_code_live_validation.py --help
```

For the checked-in local mainline regression runner:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py --help
```

For the checked-in Chat Completions fallback regression runner:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py --help
```

For the checked-in Chat Completions live readiness checker:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py --help
```

This is an optional provider fallback/regression lane. It is not required for
the local Codex mainline, and its URL is not a meeting room URL.

For the checked-in Chat Completions live validation wrapper:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py --help
```

For the checked-in release readiness gate:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py --help
```

For the checked-in release candidate report:

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py --help
```

For the checked-in local mock Chat Completions provider:

```bash
python3 .codex/skills/room-skill/runtime/mock_chat_completions_server.py --help
```

For live prompt calls against a Chat Completions-compatible provider:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py --help
```

For the checked-in `/debate` packet preflight:

```bash
python3 .codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py --help
```

## Most Useful Commands

Replay the checked-in canonical flow:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py validate-canonical
```

Run the checked-in E2E validation flow through canonical fixtures:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-e2e
```

Run a local child-agent smoke test:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py \
  --check-local-exec \
  --preset gpt54_family
```

Run a generic local agent CLI smoke test:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_executor.py \
  --check-agent-exec \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py"
```

Run the one-command generic local agent adapter validation kit:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --state-root /tmp/round-table-generic-agent-adapter-validation
```

Validate the generic agent JSON wrapper against noisy fixture outputs:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py \
  --state-root /tmp/round-table-generic-agent-json-wrapper-validation
```

Inventory local agent hosts before attempting real live validation:

```bash
python3 .codex/skills/room-skill/runtime/agent_host_inventory.py \
  --output-json /tmp/round-table-agent-host-inventory.json
```

Build a durable host validation matrix without forcing live third-party execution:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --state-root /tmp/round-table-local-agent-host-validation-matrix
```

Generate a claim-safe live lane evidence report:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

Run the clone-friendly consumer self-check without provider URLs or paid third-party accounts:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

Audit a tagged release from a fresh cloned checkout:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.1 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

Check whether the GitHub Release page exists and whether this host can publish
it automatically:

```bash
python3 .codex/skills/room-skill/runtime/github_release_publication_check.py \
  --state-root /tmp/round-table-github-release-publication
```

Validate a real local agent command with the same contract:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_agent \
  --agent-command "my-agent run --prompt {prompt_file} --input {input_file} --output {output_file}" \
  --state-root /tmp/round-table-my-agent-validation
```

Validate a noisy real local agent through the checked-in JSON wrapper:

```bash
python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label my_wrapped_agent \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-my-wrapped-agent-validation
```

Run the real Claude Code local CLI preflight and live wrapper:

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

`--preflight-only` proves CLI/auth state. `--smoke-only` proves local Claude Code can execute a minimal JSON task. Only the full default-Claude wrapper with `claimable_as_default_claude_code_host_live=true` proves `/room -> /debate` host-live support for the default Claude Code command.

If preflight reports `claude_code_not_logged_in`, run `claude auth login` in a local terminal, then rerun the wrapper.

Run the checked-in local host preflight before starting the local mainline:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_executor.py \
  --check-host-preflight \
  --preset gpt54_family
```

Run the checked-in full local mainline regression suite:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

Run the checked-in second-host validation wrapper through a standalone `codex exec` host:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_second_host_validation.py \
  --state-root /tmp/round-table-local-codex-second-host
```

Prepare a checked-in cross-machine validation bundle, then verify imported evidence from another machine:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py \
  prepare \
  --state-root /tmp/round-table-local-codex-cross-machine

python3 .codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py \
  verify \
  --manifest-json /tmp/round-table-local-codex-cross-machine/<run-id>/cross-machine-validation-manifest.json \
  --report-json /path/to/imported/local-codex-regression-report.json \
  --runtime-profile-json /path/to/imported/runtime-profile.json
```

Run the checked-in full Chat Completions fallback regression suite with local mock providers:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_regression.py \
  --state-root /tmp/round-table-chat-completions-regression
```

Check real-provider env readiness without sending provider requests:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_readiness.py \
  --output-json /tmp/round-table-chat-completions-readiness.json
```

Check release readiness without calling real providers or requiring third-party agent accounts:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --output-json /tmp/round-table-release-readiness.json
```

Generate a release candidate support-scope report:

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate
```

Run the checked-in real-provider live wrapper after filling `.env.room` and `.env.debate`:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

Run the checked-in E2E validation flow through local child-agent tasks:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor local_codex \
  --state-root /tmp/round-table-room-local-codex
```

Run the checked-in E2E validation flow through a generic local agent CLI:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor generic_cli \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-room-generic-cli
```

Check live provider config from an explicit env file:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --env-file .env.room \
  --check-provider-config
```

Call one checked-in prompt through a Chat Completions-compatible endpoint:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_executor.py \
  --env-file .env.room \
  --prompt-file prompts/room-selection.md \
  --input-json path/to/selection-input.json \
  --output-json path/to/selection-output.json
```

Run the checked-in E2E validation flow against a real Chat Completions-compatible provider:

```bash
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --env-file .env.room
```

Run the checked-in `/room -> /debate` integration flow through canonical fixtures:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor fixture \
  --state-root /tmp/round-table-room-debate-e2e
```

Run the checked-in `/room -> /debate` integration flow through local child-agent tasks:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor local_codex \
  --local-codex-model gpt-5.4 \
  --local-codex-fallback-models gpt-5.4-mini \
  --local-codex-reasoning-effort low \
  --local-codex-timeout-seconds 240 \
  --local-codex-timeout-retries 1 \
  --scenario reject_followup \
  --state-root /tmp/round-table-room-debate-local-codex
```

Run the checked-in `/room -> /debate` integration flow through a generic local agent CLI:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor generic_cli \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-room-debate-generic-cli
```

Run the same adapter route under the Claude Code executor name:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-room-debate-claude-code-adapter
```

Run the checked-in `/room -> /debate` integration flow against real providers:

```bash
python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor chat_completions \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-room-debate-live
```

Run the same provider-backed path locally without external credentials:

```bash
python3 .codex/skills/room-skill/runtime/mock_chat_completions_server.py --port 32123

ROOM_CHAT_COMPLETIONS_URL=http://127.0.0.1:32123/v1/chat/completions \
ROOM_CHAT_COMPLETIONS_MODEL=mock-room-model \
python3 .codex/skills/room-skill/runtime/room_e2e_validation.py \
  --executor chat_completions \
  --state-root /tmp/round-table-room-mock-provider
```

Create a room from `room_full` and optionally continue into the first turn:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py start-room \
  --topic "我想讨论一个面向大学生的 AI 学习产品，先别急着下结论，先把方向、切口、风险一步一步推出来。" \
  --selection-json path/to/room_full.json \
  --initial-turn-selection-json path/to/turn_selection.json \
  --initial-turn-chat-json path/to/turn_chat.json
```

Apply a follow-up turn:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-turn \
  --room-id room-1234abcd \
  --user-input "/focus 先只盯最小可验证切口" \
  --selection-json path/to/turn_selection.json \
  --chat-json path/to/turn_chat.json
```

Apply `/summary`:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-summary \
  --room-id room-1234abcd \
  --summary-json path/to/summary.json
```

Apply `/upgrade-to-debate`:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py run-upgrade \
  --room-id room-1234abcd \
  --upgrade-json path/to/upgrade.json \
  --explicit-user-request
```

Apply `/add` or `/remove` after a `roster_patch` prompt result:

```bash
python3 .codex/skills/room-skill/runtime/room_runtime.py patch-roster \
  --room-id room-1234abcd \
  --action add \
  --selection-json path/to/roster_patch.json
```

## Output Location

Runtime state and evidence bundles are written under:

`artifacts/runtime/rooms/<room_id>/`

Typical files:

- `state.json`
- `prompt-calls/001-room_full-selection.input.json`
- `prompt-calls/001-room_full-selection.output.json`
- `prompt-calls/001-room_full-selection.child-trace.json`
- `turns/turn-001.selection.json`
- `turns/turn-001.chat.json`
- `turns/turn-001.turn.json`
- `summary/summary-turn-002.json`
- `handoff/packet-turn-002.json`
- `handoff/debate-acceptance.json`
- `validation-report.json`

## Scope Boundary

This bridge is intentionally host-agnostic.

It assumes some host or operator already called:

- `prompts/room-selection.md`
- `prompts/room-chat.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`

The bridge then validates those JSON outputs and performs the state writeback that only the host is allowed to perform.

`local_codex_executor.py` is the checked-in local child-agent adapter. It reuses the local Codex host to run one prompt as one nested child task, normalizes the resulting JSON back into the runtime contracts, and now exposes explicit child-task reasoning control so `/room` and `/debate` do not blindly inherit the host's global `xhigh` profile.

`generic_agent_adapter_validation.py` is the checked-in adapter kit for non-Codex local agents. It runs `generic_agent_executor.py --check-agent-exec` first, then runs the full `/room -> /debate` integration flow through `--executor generic_cli`. The default command uses `generic_fixture_agent.py`, so the kit can be verified offline before replacing `--agent-command` with a real third-party CLI.

`generic_agent_json_wrapper.py` is the checked-in normalizer for third-party local agents that add Markdown fences, progress logs, or explanatory text around JSON. It runs the real agent command, extracts the first parseable JSON object from stdout or file output, and writes a clean JSON object back to `ROUND_TABLE_OUTPUT_JSON`.

`generic_agent_json_wrapper_validation.py` validates that wrapper against `wrapper_fixture_agent.py` in three noisy modes: Markdown fenced JSON, stdout logs around JSON, and noisy output-file JSON. Passing this proves the wrapper layer, not a real third-party host.

`agent_host_inventory.py` is the checked-in readiness inventory for real local agent hosts. It detects common CLI candidates, records lightweight version/auth evidence where available, and explicitly separates `missing_cli`, `blocked_auth`, and `ready_for_live_validation` from actual `/room -> /debate` live validation.

`local_agent_host_validation_matrix.py` is the checked-in evidence matrix for real local agent hosts. It safely persists `missing_cli`, `blocked`, `pending_live_validation`, `live_passed`, and `live_failed` rows, and only runs live validations when explicitly requested by `--run-live-ready`, `--run-installed`, or `--force-host`.

`live_lane_evidence_report.py` is the checked-in support-claim summary for host/provider live lanes. It aggregates the host matrix, provider readiness, and checked-in host-live evidence into JSON/Markdown, and keeps `claimable`, `missing_cli`, `blocked`, `pending_live_validation`, and provider-not-configured lanes separate.

It also exposes a checked-in `gpt54_family` preset. That preset freezes the currently validated Mac-local lane: `gpt-5.4` primary child-task model, `gpt-5.4-mini` same-family fallback, `low` reasoning effort, bounded timeouts, and prompt-level step policies.

It now also exposes `--check-host-preflight`, which verifies the local `~/.codex` storage prerequisites that nested child tasks depend on, then runs the same checked-in smoke probe. This makes the host-side failure boundary explicit before `/room` or `/debate` work starts.

When `trace_base` is provided by `room_e2e_validation.py`, `room_debate_e2e_validation.py`, or `debate_e2e_validation.py`, the local child-task lane now also writes a checked-in trace manifest at `prompt-calls/*.child-trace.json`. That manifest records:

- the exact child-task artifact paths
- model and fallback lane selection
- timeout / retry settings
- per-attempt started/finished timestamps
- per-attempt wall time
- per-attempt status
- final child-task status
- full child-task wall time
- structured last-failure details when the child task fails
- the applied step policy key when the preset supplied one

If a local child task fails, the runner-level `prompt-calls/*.error.json` and `prompt-calls/*.meta.json` now include the same `failure_category` plus a direct `trace_manifest` pointer, so the host can jump from the failed step straight into the nested-child evidence bundle.

The runner-level mainline now defaults to that preset. In practice, `room_e2e_validation.py`, `room_debate_e2e_validation.py`, and `local_codex_regression.py` all use `gpt54_family` unless you explicitly override the local child-task settings.

The checked-in step policies currently do three things:

- keep selection steps on the primary `gpt-5.4` lane but fail faster with shorter timeouts and no retry loop
- leave heavier discussion steps like `room-chat`, `debate-roundtable`, and `debate-followup` on the primary `gpt-5.4` lane with a longer timeout window
- route narrower structured steps like `room-summary`, `room-upgrade`, and `debate-reviewer` onto a lighter `gpt-5.4-mini -> gpt-5.4` same-family lane

It also hardens two real local-host failure modes that showed up during Mac validation:

- recover the final child message from `stdout.jsonl` when `--output-last-message` is truncated
- repair truncated JSON when a string loses its closing quote either at EOF or right before the next structural delimiter such as `},{"text": ...`
- normalize object-style evidence buckets like `{text, source}` back into the string lists expected by the runtime validators

The local failure categories now surfaced by the executor are:

- `timeout`
- `transient_transport_failure`
- `rate_limit_or_model_overloaded`
- `host_permission_or_sandbox_denied`
- `invalid_model`
- `missing_child_message`
- `invalid_json_output`
- `command_failed`

`local_codex_regression.py` is the checked-in local mainline regression runner. It now runs the host preflight first, then sequences `/room`, `/debate allow`, `/debate reject_followup`, and `/room -> /debate` integration into one evidence bundle. It defaults to the `gpt54_family` preset, so a bare regression command already lands on the validated Mac-local lane and persists a checked-in `host-preflight.json` alongside the regression report.

It now also persists a checked-in `runtime-profile.json` next to the regression report. That profile records:

- suite started/finished timestamps
- wall time per top-level stage: `host_preflight`, `room`, `debate_allow`, `debate_followup`, `integration`
- aggregated child-task timing by top-level scope
- aggregated child-task timing by prompt policy key
- the slowest child-task manifests for quick inspection

The regression report itself now also persists:

- host metadata for the machine that produced the evidence
- repo metadata including current commit and branch
- the exact topic and follow-up input used for that run

`local_codex_second_host_validation.py` is the checked-in wrapper for the second-host lane. It launches a standalone shell-level `codex exec` host, instructs that host to run `local_codex_regression.py`, then persists:

- the outer host command payload
- outer host stdout / stderr / last-message evidence
- the nested regression report and nested runtime profile
- a wrapper-level `second-host-validation-report.json`

This turns the previously manual “独立宿主复验” flow into a stable checked-in command.

`local_codex_cross_machine_validation.py` is the checked-in cross-machine lane. It has two modes:

- `prepare`: freeze the source machine's expected commit, local mainline config, target command, and a short runbook
- `verify`: compare imported `local-codex-regression-report.json` and `runtime-profile.json` against that prepared manifest

This means the source machine no longer has to treat imported target-machine evidence as anonymous JSON. The verifier can now check commit match, config match, input match, and whether the evidence actually came from a different machine.
For a real handoff, `prepare` should be run from a clean committed tree; when the source repo is dirty, the bundle now records that warning explicitly.

`chat_completions_regression.py` is the checked-in provider fallback regression runner. It boots one local `/room` mock provider plus one local `/debate` mock provider, writes checked-in `.env.room.mock` and `.env.debate.mock` files into the evidence bundle, runs provider preflight for both scopes, then sequences `/room`, `/debate allow`, `/debate reject_followup`, and `/room -> /debate` integration through `--executor chat_completions`.

`chat_completions_readiness.py` is the checked-in config-only readiness command for the real external provider lane. It checks `.env.room` and `.env.debate`, rejects missing values and unchanged template placeholders, and does not send provider requests.

`chat_completions_live_validation.py` is the checked-in real-provider wrapper for the remaining unproven external lane. It first validates `.env.room` and `.env.debate` through the same checked-in provider-config reader, persists both preflight results, then launches the full `/room -> /debate` integration flow through `--executor chat_completions`. It also writes a failure report when env files are missing or still using template placeholder values.

`release_readiness_check.py` is the checked-in launch-scope gate. It aggregates source-of-truth presence, runtime entrypoint presence, Claude Code project-skill structure, local agent host inventory, local agent host validation matrix tooling, and provider config readiness without sending real provider requests. It reports P0 blockers separately from non-blocking gaps such as missing third-party CLIs, Claude auth blockers, or provider env files that are not ready.

`release_candidate_report.py` is the checked-in release-candidate renderer. It wraps the release gate and emits claim-safe JSON/Markdown, separating what can be launched from what must not be claimed without host-live or provider-live evidence.

Because nested child tasks persist session and state data under `~/.codex/`, the `local_codex` mainline should be run from a normal local terminal or any host environment that permits writing `~/.codex/sessions` and the local Codex state DB. A tighter sandbox can make the chain fail before prompt execution even starts.

`room_e2e_validation.py` is a checked-in validation harness above that bridge. It can drive the same flow through canonical fixtures, local child-agent execution, or a real Chat Completions-compatible provider, then persist evidence bundles for review.

When `/upgrade-to-debate` is explicitly user-forced and the checked-in upgrade prompt still returns `room_too_fresh`, the host bridge now packages a legal handoff packet from persisted room state. That fallback is intentionally narrow: it only applies to `user_explicit_request`, still writes the required `user_forced_early_upgrade` warning into the packet, and keeps extra host-debug detail only in `packaging_meta.warnings`.

`room_debate_e2e_validation.py` is the checked-in orchestration layer above both runtime bridges. It first runs `/room`, then forwards the persisted handoff packet into `/debate`, so the full handoff chain can be exercised with one command.

`mock_chat_completions_server.py` is a local-only fallback validation aid. It serves the checked-in canonical fixtures behind a Chat Completions-compatible HTTP endpoint so the provider-backed path can be regression-checked without relying on external credentials.

`debate_packet_validator.py` is a checked-in `/debate`-side preflight. `/room` calls it before writing `handoff/debate-acceptance.json`, so handoff acceptance is no longer just a plain-text skill-entry check.

## Live Provider Config

Live provider config is optional. Do not create `.env.room` or `.env.debate`
just to run the local `/room` or `/debate` mainline; use
`local_codex_regression.py` for that path.

The checked-in example env file is:

`/.env.room.example`

Required variables:

- `ROOM_CHAT_COMPLETIONS_URL`
- `ROOM_CHAT_COMPLETIONS_MODEL`

Optional variables:

- `ROOM_PROVIDER_AUTH_BEARER`
- `ROOM_PROVIDER_TIMEOUT_SECONDS`
