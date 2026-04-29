# User Entry Guide

This guide explains the whole repository logic for a new user entering the
round-table workspace for the first time.

## What This Repository Is

This repository is a local-first multi-agent decision workspace.

It gives a local agent host a structured way to run two kinds of decision
workflows:

- `/room`: a stateful discussion room for exploring a question step by step.
- `/debate`: a formal round-table review for making a higher-stakes decision.

The system is not a hosted website and does not require users to join a URL
meeting room. The "room" is a local agent workflow backed by checked-in docs,
prompts, skills, and runtime scripts.

## The Core Mental Model

Think of the repository as five layers:

| Layer | What It Does | Main Files |
|---|---|---|
| Product protocol | Defines what `/room` and `/debate` mean | `docs/`, `prompts/`, `examples/` |
| Skill entrypoints | Tells Codex and Claude Code when and how to enter the workflow | `.codex/skills/`, `.claude/skills/` |
| Runtime bridge | Turns a prompt workflow into persisted JSON state, packets, and reports | `.codex/skills/*/runtime/` |
| Host adapters | Lets Codex, Claude Code, or other local CLI agents run the same contract | `generic_agent_*`, `agent_host_inventory.py` |
| Validation/release gates | Proves what can be claimed and what remains unclaimed | `release_readiness_check.py`, `live_lane_evidence_report.py` |

The important rule is: docs/prompts/skills define the behavior; runtime scripts
execute and validate it; `reports/` and `artifacts/` are evidence and output,
not source of truth.

## The Default User Flow

### 1. Clone Or Sync

Start from the repository root:

```bash
git pull origin main
```

### 2. Run The Local Self-Check

This is the safest first command for a new user:

```bash
python3 .codex/skills/room-skill/runtime/agent_consumer_self_check.py \
  --state-root /tmp/round-table-agent-consumer-self-check
```

If this passes, the checked-in local-first scope is usable on the machine.

This command does not require:

- provider URLs
- real API keys
- paid third-party agent accounts
- OpenCode/Gemini/Aider/Goose/Cursor Agent to be installed

### 3. Choose The Workflow

Use `/room` when the question is still being explored:

```text
/room 我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进
/focus 先只盯最小可验证切口
/summary
/upgrade-to-debate
```

Use `/debate` when the decision needs structured review:

```text
/debate 这个创业方向值不值得做
/debate --with Jobs,Taleb 这个方向值不值得做
/debate --quick 我该不该先做这个 MVP
```

`/room` can hand off to `/debate` through a persisted handoff packet. That is
the main end-to-end workflow: explore first, then escalate only when the topic
needs formal judgment.

## Command Discovery

`/room` and `/debate` stay explicit-only. A host may suggest them when a user
asks a broad product, strategy, risk, or "should we do this" question, but the
suggestion must not start the workflow.

Examples:

- "今天上海天气怎么样？" Answer directly; no command hint is needed.
- "这个创业方向要不要做？" Suggest: "可以用 `/room ...` 先探索，或用
  `/debate ...` 做正式判断。"
- "`/room 我想讨论一个大学生 AI 学习产品`" Now the room workflow may start.

## How `/room` Works

`/room` is a local, stateful discussion workflow.

It does these things:

- selects an initial panel of agents based on the topic
- keeps room state across turns
- records chat turns as structured JSON
- produces summaries
- decides whether the issue is ready to upgrade to `/debate`
- writes a handoff packet when the user explicitly upgrades

Important files:

- `.codex/skills/room-skill/SKILL.md`
- `.claude/skills/room/SKILL.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-chat-contract.md`
- `docs/room-to-debate-handoff.md`
- `.codex/skills/room-skill/runtime/room_runtime.py`

## How `/debate` Works

`/debate` is a formal round-table review workflow.

It does these things:

- accepts a direct `/debate` topic or a `/room` handoff packet
- selects or reselects agents for balance
- creates a launch bundle
- runs round-table discussion
- runs reviewer checks
- returns allow/reject/follow-up outcomes
- supports reject -> follow-up -> re-review chains

Important files:

- `.codex/skills/debate-roundtable-skill/SKILL.md`
- `.claude/skills/debate/SKILL.md`
- `docs/debate-skill-architecture.md`
- `docs/reviewer-protocol.md`
- `docs/red-flags.md`
- `prompts/debate-roundtable.md`
- `prompts/debate-reviewer.md`
- `.codex/skills/debate-roundtable-skill/runtime/debate_runtime.py`

## How Local Agent Hosts Fit In

The current mainline is Codex local execution.

The repository also includes adapters for other local agent hosts:

- Claude Code project-skill adapter
- generic local CLI adapter
- OpenCode wrapper tooling
- host inventory and validation matrix

Only validated host-live lanes may be claimed as real support. A fixture pass or
wrapper presence is not the same as a real host-live pass.

Current supported claim:

- Codex local mainline is launchable.
- Claude Code has machine/account-scoped host-live evidence for the validated
  Mac account.

Not currently claimed:

- OpenCode host-live support.
- Gemini CLI, Aider, Goose, or Cursor Agent host-live support.
- Real provider-live support.

## Provider URLs Are Optional

Provider URLs are not meeting-room URLs.

They are only for the optional Chat Completions-compatible fallback lane. The
local `/room`, `/debate`, and `/room -> /debate` mainline does not need a
provider URL.

Use provider live validation only when intentionally proving an external
provider:

```bash
python3 .codex/skills/room-skill/runtime/chat_completions_live_validation.py \
  --room-env-file .env.room \
  --debate-env-file .env.debate \
  --state-root /tmp/round-table-chat-completions-live
```

## What To Read First

For normal users:

1. `README.md`
2. `LAUNCH.md`
3. `docs/user-entry-guide.md`
4. `docs/agent-consumer-quickstart.md`

For developers or future agents:

1. `AGENTS.md`
2. `docs/development-sync-protocol.md`
3. `docs/source-truth-map.md`
4. `docs/release-readiness.md`
5. `docs/NEXT-STEPS.md`

For release/support claims:

1. `docs/release-candidate-scope.md`
2. `docs/releases/v0.1.3.md`
3. `CHANGELOG.md`
4. `reports/GITHUB_RELEASE_PUBLICATION_2026-04-28_v0.1.3.md`

## What The Repository Can Claim Today

The current release is `v0.1.3`.

Claimable:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- checked-in protocol, prompts, skills, runtime bridges, validation harnesses
- Claude Code project-skill discovery structure
- default Claude Code CLI host-live support on the validated Mac account
- generic local agent adapter contract with fixture-backed validation
- host/provider live-lane evidence tooling
- clone-friendly consumer self-check and release audit tooling

Not claimable yet:

- all possible local agent hosts being live-supported
- OpenCode host-live support
- real provider-live support
- universal production stability across every possible user environment

## Short Version

Run the self-check first. If it passes, use `/room` for exploration and
`/debate` for formal review. Treat provider URLs and extra local agent hosts as
optional expansion lanes, not requirements for the local mainline.
