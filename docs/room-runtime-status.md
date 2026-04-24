# Room Runtime Status

> Purpose: lock the real `/room` implementation boundary after the Windows-to-GitHub migration, so Mac-side continuation uses checked-in source instead of historical reports.
> Last reviewed: 2026-04-23

---

## Source Of Truth

The current source-of-truth files for `/room` are:

- `README.md`
- `AGENTS.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `docs/room-chat-contract.md`
- `docs/room-runtime-bridge.md`
- `docs/room-runtime-status.md`
- `docs/room-e2e-validation.md`
- `docs/debate-e2e-validation.md`
- `docs/debate-runtime-bridge.md`
- `docs/DECISIONS-LOCKED.md`
- `prompts/room-selection.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/room-chat.md`
- `examples/room-examples.md`
- `.codex/skills/room-skill/SKILL.md`
- `.codex/skills/room-skill/WORKFLOW.md`
- `.codex/skills/room-skill/runtime/room_runtime.py`
- `.codex/skills/room-skill/runtime/local_codex_executor.py`
- `.codex/skills/room-skill/runtime/local_codex_regression.py`
- `.codex/skills/room-skill/runtime/chat_completions_regression.py`
- `.codex/skills/room-skill/runtime/chat_completions_live_validation.py`
- `.codex/skills/room-skill/runtime/chat_completions_executor.py`
- `.codex/skills/room-skill/runtime/room_e2e_validation.py`
- `.codex/skills/room-skill/runtime/room_debate_e2e_validation.py`
- `.codex/skills/room-skill/runtime/mock_chat_completions_server.py`
- `.codex/skills/room-skill/runtime/README.md`
- `.codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py`
- `.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py`
- `.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py`
- `.codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py`
- `.codex/skills/debate-roundtable-skill/runtime/README.md`
- `.codex/skills/debate-roundtable-skill/runtime/fixtures/canonical/`
- `.codex/skills/room-skill/runtime/fixtures/canonical/`
- `.env.room.example`
- `.env.debate.example`

If a report, checkpoint, or session artifact conflicts with the files above, the files above win.

---

## What Is Already Completed

The repository already contains a largely complete source layer for `/room`:

- state model, ownership, command semantics, and host responsibilities in `docs/room-architecture.md`
- selection policy and scoring rules in `docs/room-selection-policy.md`
- `/room -> /debate` handoff schema in `docs/room-to-debate-handoff.md`
- a checked-in portable agent registry in `docs/agent-registry.md`
- an implementation-facing runtime bridge contract in `docs/room-runtime-bridge.md`
- a host adapter architecture source in `docs/host-adapter-architecture.md`
- a checked-in runtime workflow playbook in `.codex/skills/room-skill/WORKFLOW.md`
- a checked-in `/room` runtime entry in `.codex/skills/room-skill/SKILL.md`
- a checked-in end-to-end validation guide in `docs/room-e2e-validation.md`
- a checked-in host bridge implementation in `.codex/skills/room-skill/runtime/room_runtime.py`
- a checked-in local child-agent executor in `.codex/skills/room-skill/runtime/local_codex_executor.py`
- a checked-in host-neutral local CLI agent adapter in `.codex/skills/room-skill/runtime/generic_agent_executor.py`
- a checked-in generic fixture agent in `.codex/skills/room-skill/runtime/generic_fixture_agent.py`
- a checked-in real Claude Code local CLI live validation wrapper in `.codex/skills/room-skill/runtime/claude_code_live_validation.py`
- checked-in Claude Code project skill adapters in `.claude/skills/room/SKILL.md` and `.claude/skills/debate/SKILL.md`
- a checked-in Claude Code project skill structure validator in `.claude/scripts/validate_project_skills.py`
- a checked-in local mainline regression runner in `.codex/skills/room-skill/runtime/local_codex_regression.py`
- a checked-in second-host validation runner in `.codex/skills/room-skill/runtime/local_codex_second_host_validation.py`
- a checked-in cross-machine validation lane in `.codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py`
- a checked-in Chat Completions fallback regression runner in `.codex/skills/room-skill/runtime/chat_completions_regression.py`
- a checked-in Chat Completions live validation wrapper in `.codex/skills/room-skill/runtime/chat_completions_live_validation.py`
- a checked-in `gpt54_family` local preset exposed across `local_codex_executor.py`, `room_e2e_validation.py`, `debate_e2e_validation.py`, `room_debate_e2e_validation.py`, and `local_codex_regression.py`
- the local `/room`, `/debate`, integration, and regression runners now default to that validated `gpt54_family` preset unless the caller explicitly overrides it
- that `gpt54_family` preset is now stepwise: selection stays on the primary lane with shorter fail-fast timeouts, heavy discussion steps keep a longer `gpt-5.4` window, and narrower structured steps like summary / upgrade / reviewer shift to a lighter same-family lane
- a checked-in local host preflight in `.codex/skills/room-skill/runtime/local_codex_executor.py` that verifies `~/.codex`, `~/.codex/sessions`, `session_index.jsonl`, and discovered state/log/sqlite DB locations before nested child-task work begins
- the checked-in local regression runner now persists `host-preflight.json` and fails fast when those host prerequisites are not ready
- the checked-in local regression runner now also persists `runtime-profile.json`, including top-level stage timings plus child-task timing aggregates by scope and policy key
- the checked-in local regression runner now also persists host / repo / input metadata, so imported evidence from another machine can be compared against the source manifest instead of being treated as anonymous JSON
- a checked-in local child-task trace manifest at `prompt-calls/*.child-trace.json`, written by `local_codex_executor.py` whenever the runner supplies a `trace_base`
- a checked-in generic local agent trace manifest at `prompt-calls/*.agent-trace.json`, written by `generic_agent_executor.py` whenever the runner supplies a `trace_base`
- those `*.child-trace.json` manifests now include attempt-level timestamps and wall times, plus full child-task wall time on completion
- structured local prompt-call failure payloads in `prompt-calls/*.error.json` and failed `prompt-calls/*.meta.json`, including `failure_category` and `trace_manifest` pointers
- a checked-in `/debate` packet preflight in `.codex/skills/debate-roundtable-skill/runtime/debate_packet_validator.py`
- a checked-in `/debate` execution bridge in `.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py`, including reject-followup-rereview validation
- a checked-in `/debate` prompt-host E2E runner in `.codex/skills/debate-roundtable-skill/runtime/debate_e2e_validation.py`
- a checked-in local `/debate` mock Chat Completions provider in `.codex/skills/debate-roundtable-skill/runtime/mock_chat_completions_server.py`
- a checked-in `/debate` canonical fixture pack in `.codex/skills/debate-roundtable-skill/runtime/fixtures/canonical/`
- a checked-in Chat Completions-compatible live prompt adapter in `.codex/skills/room-skill/runtime/chat_completions_executor.py`
- a checked-in E2E validation runner in `.codex/skills/room-skill/runtime/room_e2e_validation.py`
- a checked-in `/room -> /debate` integration runner in `.codex/skills/room-skill/runtime/room_debate_e2e_validation.py`
- a checked-in local mock Chat Completions provider in `.codex/skills/room-skill/runtime/mock_chat_completions_server.py`
- a checked-in provider fallback regression path that boots both mock providers, writes scope-specific mock env files, and validates room, debate, and integration through `--executor chat_completions`
- a Mac-validated Chat Completions fallback full regression suite using the checked-in local mock providers for both `/room` and `/debate`
- a checked-in live wrapper that now rejects unchanged example placeholder values in `.env.room` / `.env.debate`, persists preflight evidence, and can launch the real `/room -> /debate` provider-backed integration flow from one command
- a Mac-validated `local_codex` `/room` E2E path
- a Mac-validated `local_codex` `/debate` allow path plus reject-followup-rereview path
- a Mac-validated `local_codex` `/room -> /debate` full-chain integration path that consumes the persisted room packet directly
- a Mac-validated `local_codex` full regression suite (`smoke + room + debate allow + debate reject_followup + integration`) under the `GPT-5.4` family child-task lane
- a checked-in child-task reasoning-effort control on the local executor, so nested `/room` and `/debate` tasks do not have to inherit the host's global `model_reasoning_effort`
- a checked-in `gpt54_family` preset that freezes the currently validated Mac-local mainline: `gpt-5.4` primary child-task model, `gpt-5.4-mini` same-family fallback, `low` reasoning effort, and bounded timeouts
- a Mac-validated stepwise local execution policy under `gpt54_family`, verified by the full local regression suite
- a same-Mac second-host validation path through standalone `codex exec`, validated against the full local regression suite rather than a shortened smoke lane
- a checked-in source->target->source cross-machine handoff flow: prepare manifest/runbook on the source machine, run `local_codex_regression.py` on the target machine, then verify imported evidence back on the source machine
- Windows local mainline and enhanced validation evidence are now checked into `reports/WINDOWS_LOCAL_MAINLINE_VALIDATION.md` and `reports/WINDOWS_ENHANCED_VALIDATION.md`
- a validated `generic_cli` `/room -> /debate` adapter integration path using the checked-in fixture agent
- a validated `claude_code` executor route using the checked-in fixture agent; real Claude Code CLI execution remains a separate host-live validation
- validated Claude Code project skill structure, so Claude Code users get native `.claude/skills/` discovery entries after cloning the repo
- a current Mac Claude Code preflight result showing the CLI is installed (`2.1.114`) but live validation is blocked by `claude_code_not_logged_in`
- a Mac-validated `GPT-5.4` local mainline configuration for the full `/room -> /debate reject_followup` chain, with `gpt-5.4` as the primary child-task model and `gpt-5.4-mini` available as same-family fallback
- a checked-in `/room` host fallback for explicit `/upgrade-to-debate` requests when the upgrade prompt still returns `room_too_fresh`; that fallback reuses persisted room state and writes the required `user_forced_early_upgrade` packet warning
- a checked-in `/debate` terminal-outcome rule for the single follow-up cap: the second review may either allow the decision or end in a blocked conclusion with no further required followups
- a checked-in canonical fixture pack in `.codex/skills/room-skill/runtime/fixtures/canonical/`
- an explicit local provider config template in `.env.room.example`
- an explicit `/debate` provider config template in `.env.debate.example`
- repository-level entrypoints aligned so `/room` is first-class in `README.md`, `AGENTS.md`, and `examples/room-examples.md`
- a clean fallback chat contract in `docs/room-chat-contract.md`
- rebuilt and portable active prompts in:
  - `prompts/room-chat.md`
  - `prompts/room-summary.md`
  - `prompts/room-upgrade.md`
  - `prompts/room-selection.md`
- a Mac-local canonical replay path that writes evidence bundles to `artifacts/runtime/rooms/<room_id>/`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open sketch.

---

## What Is Not Yet Completed In This Repo

The remaining unfinished part is no longer the checked-in bridge itself.

The remaining gap is now narrower and sits in two places:

1. the checked-in local child-agent path is now proven on Mac and Windows, and the checked-in executor can explicitly control child-task reasoning effort through either per-flag overrides or the frozen `gpt54_family` preset; what is still not a target is blindly inheriting the host's heaviest default profile without child-task tuning
2. the generic local CLI adapter and Claude Code project skill discovery layer are proven at the adapter-contract / structure layer; real Claude Code live validation now has a checked-in wrapper, but this Mac is currently blocked by account entitlement/authentication
3. the external Chat Completions-compatible provider path still has value as fallback / regression coverage, and the repo now has both a checked-in one-command mock-provider regression runner and a checked-in real-provider live wrapper for that lane; what is still not proven is a real external `/room -> /summary -> /upgrade-to-debate -> /debate` run against an actual non-mock endpoint
4. debate handoff is executable-preflight-validated and the checked-in debate-side execution plus reject-followup-rereview bridge is now locally provable through fixture, generic local CLI, mock-provider, or local child-agent execution, but still not yet proven by a real external `/debate` execution chain

In short:

`/room` is protocol-complete, prompt-cleaned, workflow-checked-in, bridge-checked-in, fixture-backed E2E-validated, and validated through the checked-in local child-agent path. `/debate` now matches that local confidence level for both allow and reject-followup execution chains, and the unified `/room -> /debate` flow has passing local child-agent plus generic CLI adapter validation. The external provider lane still exists, but it is fallback coverage rather than the mainline.

---

## How To Treat Reports

`reports/` is historical evidence, not runtime source.

Use reports to understand:

- why a decision was made
- what was validated at the time
- what existed on the Windows machine

Do not use reports as the sole authority for:

- current prompt contracts
- runtime entrypoints
- path references
- portable implementation truth

The same rule applies to `artifacts/`: they are outputs, not authoring source.

---

## Current Risks

- The host-side `/room` execution path now exists and the local child-agent path is validated. The remaining latency risk is the unbounded host-default path; the checked-in child-task mainline should use explicit reasoning/timing controls instead of inheriting the host's heaviest profile.
- The local child-agent path is now easier to debug, but the longest-running steps can still consume the full child timeout window before the trace manifest flips from `started` to a terminal state.
- The local child-agent path depends on the host being allowed to write its Codex session/state files under `~/.codex/`; the checked-in host preflight now surfaces that boundary earlier, but a tighter outer sandbox can still block nested child-task execution before prompt validation begins.
- `/room -> /debate` handoff is no longer a plain-text contract grep, and the repo now has a checked-in integration runner plus direct `--packet-json` intake on the debate side; the remaining runtime gap is now mainly external-provider proof, not local chain design.
- Historical reports still reference old Windows runtime paths, which can mislead future continuation if read as implementation truth.
- The generated room bundles under `artifacts/runtime/rooms/` are outputs and must not be treated as new source-of-truth files.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. keep `.codex/skills/room-skill/runtime/local_codex_executor.py` as the main portable host path for `/room` and `/debate`
2. use `.codex/skills/room-skill/runtime/local_codex_executor.py --check-host-preflight --preset gpt54_family` as the shortest checked-in host readiness command
3. use `.codex/skills/room-skill/runtime/local_codex_regression.py` as the shortest checked-in regression command for the passing Mac-local mainline
4. use `.codex/skills/room-skill/runtime/local_codex_second_host_validation.py` when the question is no longer “当前线程能不能跑”，而是“独立宿主入口能不能把整套本地主线再跑一遍”
5. use `.codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py prepare` to freeze the exact commit, config, and target command before handing the work to another machine
6. use `.codex/skills/room-skill/runtime/local_codex_cross_machine_validation.py verify` after the target machine returns `local-codex-regression-report.json` and `runtime-profile.json`
7. use `.codex/skills/room-skill/runtime/chat_completions_regression.py` as the shortest checked-in regression command for the provider fallback lane
8. keep validating the desired `GPT-5.4` family child-task settings without regressing back to the host's unbounded default `xhigh` profile
9. when real provider credentials are available, run `.codex/skills/room-skill/runtime/chat_completions_live_validation.py --room-env-file .env.room --debate-env-file .env.debate`

This keeps the repository structure stable:

- `docs/`, `prompts/`, `examples/`, `.codex/skills/` stay as source
- `reports/` remains historical
- `artifacts/` remains generated output

---

## Non-Goals

- Do not move historical reports into source directories.
- Do not treat old session notes as stronger than current docs and prompts.
- Do not redesign `/debate`.
- Do not rewrite repo structure unless a concrete source/runtime conflict requires it.
