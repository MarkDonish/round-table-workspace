# Release Readiness

This document is the source of truth for deciding what this repository can currently launch and what must not be over-claimed.

## Current Launch Scope

The repository can be treated as ready for the current supported scope when the checked-in release gate has no P0 blockers:

- Codex local mainline for `/room`, `/debate`, and `/room -> /debate`
- checked-in protocol, prompts, runtime bridges, and validation harnesses
- Claude Code project-skill discovery layer as an adapter, not a forked implementation
- generic local agent adapter contract and fixture-backed validation path
- third-party local agent JSON wrapper tooling and recipes
- third-party local agent validation matrix/report tooling
- host/provider live-lane evidence report tooling
- third-party local agent host recipe consistency tooling
- clone-friendly agent consumer self-check tooling
- clone-friendly launch quickstart
- Chat Completions-compatible provider fallback tooling and mock regression path

This does not mean every possible host or provider is live-validated.

Current host-live evidence: the default Claude Code CLI wrapper passed full
`/room -> /debate` live validation on this Mac on 2026-04-26. That result is
claimable for the tested Mac account and default wrapper command only; new
machines/accounts must rerun `claude_code_live_validation.py`.

## Current Release

The current reproducible release target is:

- Tag: `v0.1.0`
- Changelog: `CHANGELOG.md`
- Release notes: `docs/releases/v0.1.0.md`

Create or update this tag only after the strict release gate and claim-safe
release report pass from a clean Git tree.

## Not Claimed By This Scope

Do not claim these as complete unless the matching live validation report exists:

- real Claude Code live execution when the local account is not logged in or entitled
- real third-party local agent execution before its command passes `generic_agent_adapter_validation.py`
- real Chat Completions-compatible provider execution before `.env.room` and `.env.debate` are ready and `chat_completions_live_validation.py` passes
- universal production stability across all local agent hosts without per-host evidence

## P0 Blocker Definition

For the current launch scope, a P0 blocker means the repository cannot honestly ship the Codex-local mainline.

| Blocker | Why It Blocks | How To Clear |
|---|---|---|
| Source-of-truth files missing | The runtime would no longer have canonical docs/prompts/skills to execute from | Restore `AGENTS.md`, `README.md`, `docs/`, `prompts/`, `examples/`, `.codex/skills/` |
| Runtime entrypoint missing | The checked-in bridge or validation path is incomplete | Restore the missing runtime file and rerun readiness |
| Claude project-skill structure drift | Cross-host adapter discovery would point to stale or missing sources | Run and fix `python3 .claude/scripts/validate_project_skills.py` |
| Readiness tooling failure | The release gate cannot distinguish real blockers from non-blocking live gaps | Fix `agent_host_inventory.py`, `local_agent_host_validation_matrix.py`, or `chat_completions_readiness.py`, then rerun the gate |
| Local agent host validation matrix tooling failure | The release gate cannot classify third-party host lanes into missing/blocked/pending/passed/failed | Fix `local_agent_host_validation_matrix.py`, then rerun the gate |
| Live lane evidence report tooling failure | Support claims would lose the one-command summary separating claimable, blocked, missing, pending, and provider-not-configured lanes | Fix `live_lane_evidence_report.py`, then rerun the gate and report |
| Host recipe consistency failure | External-agent docs no longer cover every checked-in host candidate or have lost the claim-boundary warnings | Fix `docs/local-agent-host-recipes.md`, `docs/agent-consumer-quickstart.md`, or `LAUNCH.md`, then rerun `host_recipes_consistency_check.py` |
| Generic fixture adapter validation fails when included | The host-neutral adapter contract no longer runs end to end | Run with `--include-fixture-runs`, inspect the report, fix adapter/runtime drift |
| Generic JSON wrapper validation fails when included | Noisy third-party agent output can no longer be normalized safely | Run `generic_agent_json_wrapper_validation.py`, inspect the failing mode, fix wrapper/runtime drift |
| Dirty tree under strict gate | A release candidate cannot be reproduced from Git | Commit or discard intended changes, then rerun with `--strict-git-clean` |

These are not P0 for the Codex-local launch scope:

- provider `.env` files missing
- Claude Code account not logged in on a target machine that is trying to claim Claude Code host-live support
- Gemini/OpenCode/Aider/Goose/Cursor Agent CLI missing
- real third-party live validation not yet run

They are real gaps, but they block only their own host/provider lane.

## Release Gate

Run the default non-secret gate:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --output-json /tmp/round-table-release-readiness.json
```

Run the stronger fixture-backed gate:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --include-fixture-runs \
  --output-json /tmp/round-table-release-readiness.json
```

Run the strict Git gate for a release tag:

```bash
python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --include-fixture-runs \
  --strict-git-clean \
  --output-json /tmp/round-table-release-readiness.json
```

The command does not send real provider requests and does not require third-party agent subscriptions.

## Claim-Safe Release Report

Generate a claim-safe release summary:

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate
```

The support-scope rules for interpreting that report live in `docs/release-candidate-scope.md`.

## Recommended Release Validation

Before tagging or announcing a release, run:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression

python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --state-root /tmp/round-table-generic-agent-adapter-validation

python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper_validation.py \
  --state-root /tmp/round-table-generic-agent-json-wrapper-validation

python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --state-root /tmp/round-table-local-agent-host-validation-matrix

python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence

python3 .codex/skills/room-skill/runtime/host_recipes_consistency_check.py \
  --output-json /tmp/round-table-host-recipes-consistency.json

python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check

python3 .codex/skills/room-skill/runtime/chat_completions_regression.py \
  --state-root /tmp/round-table-chat-completions-regression

python3 .claude/scripts/validate_project_skills.py

python3 .codex/skills/room-skill/runtime/release_readiness_check.py \
  --include-fixture-runs \
  --strict-git-clean

python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate
```

After tagging or before publishing handoff instructions, run the post-release
consumer audit from a fresh cloned checkout of the release ref:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.0 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

This audit proves the release ref itself can run the clone-friendly local-first
consumer path. It does not prove real provider-live support or live support for
third-party local agent CLIs that are not installed and validated.

If a real provider is available, run this separately:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

If a real local agent host is available, run:

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --run-live-ready \
  --state-root /tmp/round-table-local-agent-host-validation-matrix

python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence

python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label <host_id> \
  --agent-command "<host command>" \
  --state-root /tmp/round-table-<host-id>-validation
```

## Current Interpretation Rules

- `reports/` is historical evidence, not release source.
- `artifacts/` is runtime output, not release source.
- A fixture pass is not a real host-live pass.
- A mock provider pass is not a real provider-live pass.
- A readiness preflight is not a live execution pass.
- Provider URLs are never required for the local mainline.
