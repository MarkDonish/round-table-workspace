# Round Table Workspace

Local-first multi-agent decision workflows for Codex, Claude Code, and other
local CLI agents.

Round Table Workspace turns `/room` and `/debate` into checked-in docs,
prompts, skills, runtime scripts, validation tools, and release boundaries. It
is local-first: the "room" is not a web conference room, and provider URLs are
optional fallback infrastructure rather than the default path.

## Quick Start In 5 Minutes

Clone and enter the repository:

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
```

Check whether this clone is usable locally:

```bash
./rtw doctor
```

For a faster source/readiness preflight:

```bash
./rtw doctor --quick
```

Try the command surfaces:

```bash
./rtw room "我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进"
./rtw debate "这个创业方向值不值得做"
```

Current support: the checked-in Codex local mainline for `/room`, `/debate`,
and `/room -> /debate`; Claude Code project-skill discovery; generic local
agent adapter contracts with fixture validation; clone-friendly self-checks;
and host/provider evidence reporting.

Current limits: `./rtw room` and `./rtw debate` are claim-safe stubs until the
full host runtime is wired into the unified CLI; provider-live support requires
real `.env.room` and `.env.debate` files plus live validation; fixture passes,
wrapper presence, and config preflights are not host-live or provider-live
claims.

For the shortest maintained startup path, read `LAUNCH.md`.

## What It Does

Round Table Workspace helps a local agent host:

- explore ambiguous questions through a stateful multi-agent discussion
- escalate mature questions into a formal review workflow
- preserve summaries, handoff packets, review results, and validation evidence
- keep source files, generated artifacts, and historical reports clearly
  separated
- verify which host and provider claims are actually supported before release

The project is intentionally conservative about claims. A fixture pass, wrapper
presence, or config preflight is not described as real host-live or
provider-live support unless the matching validation evidence exists.

## Core Workflows

| Workflow | Use It When | Output |
|---|---|---|
| `/room` | You are still exploring a topic and need a stateful discussion | selected panel, structured turns, summaries, optional handoff packet |
| `/debate` | You need a higher-stakes decision reviewed by a round table | launch bundle, round-table record, reviewer result, allow/reject/follow-up outcome |
| `/room -> /debate` | Exploration has produced enough context for formal review | persisted handoff from discussion into decision review |
| self-check | You want to know whether a fresh clone is usable locally | JSON/Markdown evidence under a chosen state root |

Example interaction shape:

```text
/room 我想讨论一个面向大学生的 AI 学习产品，从方向、切口、风险一步步推进
/focus 先只盯最小可验证切口
/summary
/upgrade-to-debate
```

```text
/debate 这个创业方向值不值得做
/debate --with Jobs,Taleb 这个方向值不值得做
/debate --quick 我该不该先做这个 MVP
```

For longer illustrative walkthroughs, see `examples/transcripts/`.

## Current Support Scope

The current release is `v0.1.3`.

The repository may currently be used for:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- checked-in protocol docs, prompts, skill entrypoints, runtime bridges, and
  validation harnesses
- Claude Code project-skill discovery structure as an adapter layer
- generic local agent adapter contracts with fixture-backed validation
- clone-friendly self-checks and post-release consumer audits
- host/provider live-lane evidence reporting
- Chat Completions-compatible fallback and mock regression tooling

The repository does not currently claim:

- universal support for every local agent host
- OpenCode host-live support
- Gemini CLI, Aider, Goose, or Cursor Agent host-live support before their own
  validation rows report `live_passed`
- real Chat Completions-compatible provider-live support before valid
  `.env.room` and `.env.debate` files exist and live validation passes
- universal production stability across all possible machines and accounts

See `docs/release-candidate-scope.md` and `docs/releases/v0.1.3.md` for the
claim-safe release boundary.

## Repository Map

```text
round-table-workspace/
├─ README.md
├─ LAUNCH.md
├─ AGENTS.md
├─ CHANGELOG.md
├─ docs/
├─ prompts/
├─ examples/
├─ .codex/skills/
├─ .claude/skills/
├─ reports/
└─ artifacts/
```

Active source of truth:

- `AGENTS.md`
- `LAUNCH.md`
- `docs/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- `.claude/skills/` as an adapter layer

Historical or generated material:

- `reports/`
- `artifacts/`

When a report or artifact reveals a still-valid rule, the rule should be moved
into active source files instead of leaving historical material as the authority.

## Key Documents

| Document | Purpose |
|---|---|
| `LAUNCH.md` | shortest safe startup path for a fresh clone |
| `docs/user-entry-guide.md` | plain-language guide to the repository logic |
| `docs/agent-consumer-quickstart.md` | commands for Codex, Claude Code, and generic local agents |
| `docs/source-truth-map.md` | source vs historical/output boundary |
| `docs/release-readiness.md` | release gate rules |
| `docs/release-candidate-scope.md` | claim-safe support scope |
| `docs/protocol-spec.md` | unified `/room`, `/debate`, and handoff protocol overview |
| `docs/room-architecture.md` | `/room` protocol and behavior |
| `docs/debate-skill-architecture.md` | `/debate` protocol and behavior |
| `docs/room-to-debate-handoff.md` | handoff contract from exploration to review |
| `docs/generic-local-agent-adapter.md` | generic local CLI agent contract |
| `examples/transcripts/` | illustrative `/room`, `/debate`, and handoff walkthroughs |
| `CHANGELOG.md` | release history |

## Host And Provider Boundaries

The default path is local-first. Provider URLs are optional and only belong to
the Chat Completions-compatible fallback or live validation lane.

Before making support claims for a host or provider, generate evidence:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

For the Codex local mainline:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

For release-scope review:

```bash
python3 .codex/skills/room-skill/runtime/release_candidate_report.py \
  --include-fixture-runs \
  --strict-git-clean \
  --state-root /tmp/round-table-release-candidate
```

## Development Notes

Repository-local rules live in `AGENTS.md`. Future development should start by
reading:

1. `AGENTS.md`
2. `docs/source-truth-map.md`
3. `docs/development-sync-protocol.md`
4. `docs/release-readiness.md`

Default development rule:

- develop locally
- verify locally
- commit verified changes
- push to `origin/main`
- report what changed, what was verified, and what remains outside the claim
  boundary
