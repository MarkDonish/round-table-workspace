# Launch Quickstart

This is the shortest safe entrypoint for a freshly cloned copy of the
round-table workspace.

The default launch path is local-first. You do not need a provider URL to use
or validate the Codex local mainline.

## 1. Sync The Repository

Run from the repository root:

```bash
git pull origin main
```

## 2. Run The Consumer Self-Check

Use the full self-check when validating a clone for real use:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

Use the quick mode when you only need a fast source/readiness preflight:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --quick \
  --state-root /tmp/round-table-agent-consumer-self-check-quick
```

## 3. Interpret The Result

A passing self-check means the checked-in local-first scope is usable:

- source-truth files are present
- release readiness has no P0 blocker for the supported local scope
- Claude Code project-skill structure is valid
- generic local agent fixture and JSON wrapper paths can be validated
- local agent host lanes are classified without over-claiming live support

It does not mean every third-party agent host or provider has passed live
execution. Only a host matrix row with `matrix_status=live_passed` can be
claimed as real host-live support.

## 4. Audit The Published Release Path

After a release is tagged, use the post-release audit to simulate a fresh
consumer checkout of the release tag:

```bash
python3 .codex/skills/room-skill/runtime/post_release_consumer_audit.py \
  --ref v0.1.0 \
  --state-root /tmp/round-table-post-release-consumer-audit
```

This clones the requested ref into a temporary checkout and reruns the
consumer-facing self-check, Claude project-skill validation, and strict release
readiness from that checkout. It still does not require provider URLs.

## 5. Pick The Matching Runtime Path

Codex local mainline:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

Claude Code adapter without account/live entitlement:

```bash
python3 .claude/scripts/validate_project_skills.py

python3 .codex/skills/room-skill/runtime/room_debate_e2e_validation.py \
  --executor claude_code \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_fixture_agent.py" \
  --state-root /tmp/round-table-claude-code-adapter-fixture
```

Generic local CLI agent:

Use `docs/local-agent-host-recipes.md` for the host decision tree and claim
rules before validating a real third-party command.

```bash
python3 .codex/skills/room-skill/runtime/local_agent_host_validation_matrix.py \
  --state-root /tmp/round-table-local-agent-host-validation-matrix

python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence

python3 .codex/skills/room-skill/runtime/generic_agent_adapter_validation.py \
  --agent-label <host_id> \
  --agent-command "python3 .codex/skills/room-skill/runtime/generic_agent_json_wrapper.py --agent-command '<real agent command>'" \
  --state-root /tmp/round-table-<host-id>-validation
```

Use the live lane evidence report before making support claims. It summarizes
which host/provider lanes are claimable, blocked, missing, pending, or not
configured without requiring provider URLs.

## 6. Keep The Source Boundary Clear

Active source of truth:

- `AGENTS.md`
- `README.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- `.claude/skills/` as an adapter layer only

Not active implementation source:

- `reports/`
- `artifacts/`

Provider fallback is available for intentional Chat Completions-compatible
regression or live testing, but it is not the local meeting room and is not
required for the local mainline.

## 7. Save A Repo-Local Checkpoint

If the host's global memory is read-only or another machine will continue the
work, write a project checkpoint instead:

```bash
python3 .codex/skills/room-skill/runtime/development_checkpoint.py \
  --title "Development Checkpoint" \
  --topic "Current work" \
  --completed "Completed item" \
  --next-task "Next task"
```

Checkpoint outputs under `reports/checkpoints/generated/` are historical
continuity records, not implementation source.

Current release notes: `docs/releases/v0.1.0.md`.
