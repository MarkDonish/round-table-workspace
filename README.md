# Round Table Workspace

[![CI](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Local First](https://img.shields.io/badge/local--first-yes-2ea44f)
![AI Agents](https://img.shields.io/badge/AI%20agents-round--table-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Demo: https://markdonish.github.io/round-table-workspace/

Make your AI coding agents hold a review round table before you trust the output.

Round Table Workspace is a local-first decision layer for Codex, Claude Code, and other CLI agents. It turns vague product or engineering questions into structured `/room` exploration, escalates risky choices into `/debate`, and adds a `ship-check` gate before you accept AI-generated work.

Instead of taking one confident agent answer at face value, you get a small panel of roles that review the work from product, engineering, risk, and user perspectives, then return a practical `ship`, `revise`, or `reject` decision.

If you use AI coding agents for real work, this repository is for the moment
right before you merge, publish, or trust their output.

Use it when you want to:

- catch weak reasoning before it becomes a real engineering decision
- turn one confident agent answer into a small review panel
- keep a local evidence trail instead of relying on a chat transcript
- decide whether generated work should ship, be revised, or be rejected

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw room "What is the smallest useful MVP for this idea?"
./rtw debate "Is this launch ready?"
./rtw doctor --quick
```

A `ship-check` result looks roughly like this:

```text
Decision: revise
Panel: product, engineering, risk, user-advocate
Why: useful direction, but public claims and evidence need tightening
Next: run tests, add a visible demo, keep claims local-first unless validated
```

For a concrete pre-merge example, see
[`docs/ai-generated-feature-review-demo.md`](docs/ai-generated-feature-review-demo.md).

## When To Star This

Star this repo if you want a local-first review layer for AI coding workflows,
especially if you use Codex, Claude Code, or other CLI agents and want a
repeatable decision gate before trusting generated work.

The current best path to try is:

```bash
./rtw demo startup-idea
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw doctor --quick
```

No provider key is required for the default demo path.

## Why This Exists

AI coding agents are fast. Sometimes too fast.

They can write code, docs, launch copy, or plans before the real decision has been tested:

- Should this actually be built?
- What evidence would change the decision?
- What user or maintenance risk are we ignoring?
- Is this ready to ship, or does it only sound plausible?
- Are we claiming host-live or provider-live support without current evidence?

Round Table Workspace adds a decision protocol before execution. It is not another chat UI. It is a repository-friendly protocol, CLI surface, schema set, fixture-backed runtime, and evidence trail for reviewing AI-assisted decisions.

## Quick Start

Run the pre-ship decision gate:

```bash
./rtw ship-check "Launch the new AI-generated onboarding flow"
```

Run a quick local health check after cloning:

```bash
./rtw doctor --quick
```

Try the fixture-backed room and debate surfaces:

```bash
./rtw room "I want to build an AI study product for college students"
./rtw debate "Should this MVP be shipped this week?"
```

Run the golden-path demo without configuring a provider:

```bash
./rtw demo startup-idea
```

Most commands support automation-friendly output:

```bash
./rtw ship-check "Should we merge this?" --output-json /tmp/ship-check.json --quiet
./rtw room "topic" --json
./rtw release-check --include-fixtures --quiet --output-json /tmp/rtw-release-check.json
```

## How It Works

```mermaid
flowchart TD
    A[Vague idea or AI-generated change] --> B[/room exploration]
    B --> C[Summary + handoff packet]
    C --> D[/debate decision review]
    D --> E{ship-check gate}
    E -->|ship| F[Proceed with evidence]
    E -->|revise| G[Fix risks or add evidence]
    E -->|reject| H[Stop or redefine the problem]
    F --> I[JSON + Markdown artifacts]
    G --> I
    H --> I
```

Core command surface:

| Command | When to use it | Output |
|---|---|---|
| `ship-check` | Before trusting AI-generated work | panel vote, risks, missing evidence, next steps |
| `/room` / `./rtw room` | When the topic is still exploratory | selected panel, structured turns, summary, optional handoff packet |
| `/debate` / `./rtw debate` | When a risky decision needs review | launch bundle, round-table record, reviewer result, allow/reject/follow-up outcome |
| `doctor` | When you want to know whether a fresh clone can run locally | JSON / Markdown evidence under the selected state root |
| `release-check` | When you need release-scope readiness evidence | aggregated readiness evidence without relying on old reports |

## Use Cases

- Pre-merge review for AI-generated code or docs
- MVP decision review before building
- Architecture tradeoff review before refactoring
- Risk review before public launch claims
- Local-first agent workflow experiments
- Decision evidence for Codex and Claude Code projects
- Training teams not to blindly trust a single confident agent answer

## Current Scope

The current release is `v0.2.2-pages-launch-kit`.

This repository currently provides:

- Codex local-mainline `/room`
- Codex local-mainline `/debate`
- Codex local-mainline `/room -> /debate`
- Fixture-backed `ship-check` decision gate scaffolding
- Committed protocol docs, prompts, skill entries, runtime bridge, and validation harnesses
- Claude Code project-level skill discovery structure as an adapter layer
- Fixture-validated generic local agent adapter contract
- Fresh-clone checks and post-release consumer audit paths
- Host / provider live-lane evidence reports
- Chat Completions compatible fallback and mock regression tools

This repository does not currently claim:

- Universal support for every local agent host
- OpenCode host-live support
- Gemini CLI, Aider, Goose, or Cursor Agent host-live support before their validation rows report `live_passed`
- Real Chat Completions compatible provider-live support before a valid `.env.room` / `.env.debate` exists and live validation passes
- General production stability across all machines and account environments

The project is intentionally conservative about public claims. Passing fixtures, having wrappers, or passing config preflight is not described as real host-live or provider-live support unless matching validation evidence exists.

## Repository Layout

```text
round-table-workspace/
├─ README.md
├─ LAUNCH.md
├─ AGENTS.md
├─ CHANGELOG.md
├─ docs/
├─ schemas/
├─ agents/
├─ config/
├─ roundtable_core/
├─ scripts/
├─ skills_src/
├─ evals/
├─ prompts/
├─ examples/
├─ .codex/skills/
├─ .claude/skills/
├─ reports/
└─ artifacts/
```

Current source-of-truth areas:

- `AGENTS.md`
- `LAUNCH.md`
- `docs/`
- `schemas/`
- `agents/`
- `config/`
- `roundtable_core/`
- `scripts/`
- `skills_src/`
- `evals/`
- `prompts/`
- `examples/`
- `.codex/skills/`
- `.claude/skills/` as an adapter layer

Historical or generated material:

- `reports/`
- `artifacts/`

If a report or artifact exposes a still-valid rule, migrate that rule into an active source file instead of treating historical output as an authority.

## Key Documents

| Document | Purpose |
|---|---|
| `LAUNCH.md` | Shortest safe path for a fresh clone |
| `docs/index.md` | Documentation map by user, protocol, runtime, validation, and history areas |
| `docs/why-star-this-repo.md` | Quick evaluator guide for deciding whether the repo is worth starring |
| `docs/ai-generated-feature-review-demo.md` | Concrete pre-merge demo for reviewing AI-generated work |
| `docs/user-entry-guide.md` | Plain-language guide to the repository model |
| `docs/agent-consumer-quickstart.md` | Command guide for Codex, Claude Code, and generic local agents |
| `docs/source-truth-map.md` | Boundary between source files and historical / generated material |
| `docs/release-readiness.md` | Release gate rules |
| `docs/release-candidate-scope.md` | Support scope and public claim boundaries |
| `docs/roadmap.md` | Roadmap and release horizon |
| `docs/milestones/v0.2.0.md` | v0.2.0 milestone scope and issue breakdown |
| `docs/launch-copy.md` | Launch copy for X, Hacker News, Reddit, and community posts |
| `docs/demo.html` | Static visual demo for GitHub Pages or screenshots |
| `docs/protocol-spec.md` | `/room`, `/debate`, and handoff protocol overview |
| `docs/protocol-versioning.md` | Release, protocol, schema, runtime, prompt, and fixture version boundaries |
| `docs/decision-quality-rubric.md` | Machine-checkable decision quality rubric |
| `docs/schema-validation-subset.md` | Draft 2020-12 fallback validator boundary |
| `docs/skill-generation.md` | Skill generation summary and drift-check maintenance |
| `docs/agent-factory-architecture.md` | Agent Factory manifest, profile, and registry lifecycle |
| `agents/registry.json` | Machine-readable agent registry used by the runtime bridge |
| `config/agent-registry.json` | Agent Factory custom / candidate registry |
| `schemas/room-session.schema.json` | Portable `/room` session state schema |
| `schemas/debate-session.schema.json` | Portable `/debate` session state schema |
| `schemas/debate-result.schema.json` | Portable `/debate` result schema |
| `schemas/room-to-debate-handoff.schema.json` | Portable `/room -> /debate` handoff schema |
| `schemas/agent-manifest.schema.json` | Agent Factory manifest schema |
| `schemas/agent-registry.schema.json` | Agent Factory custom / candidate registry schema |
| `schemas/agent-selection-request.schema.json` | Future selection bridge request schema |
| `docs/room-architecture.md` | `/room` protocol and behavior |
| `docs/debate-skill-architecture.md` | `/debate` protocol and behavior |
| `docs/room-to-debate-handoff.md` | Handoff contract from exploration to review |
| `docs/generic-local-agent-adapter.md` | Generic local CLI agent contract |
| `examples/transcripts/` | Example walkthroughs for `/room`, `/debate`, and handoff |
| `reports/claim-boundary-dashboard.md` | Generated snapshot only; for current status, run `./rtw evidence` or `./rtw release-check` |
| `CHANGELOG.md` | Release history |

## Host and Provider Boundaries

The default path is local-first. Provider URLs are optional and only belong to the Chat Completions compatible fallback or live validation lane.

Before making host or provider support claims, generate evidence:

```bash
python3 .codex/skills/room-skill/runtime/live_lane_evidence_report.py \
  --state-root /tmp/round-table-live-lane-evidence
```

Codex local-mainline regression:

```bash
python3 .codex/skills/room-skill/runtime/local_codex_regression.py \
  --state-root /tmp/round-table-local-codex-regression
```

Release-scope check:

```bash
./rtw release-check --include-fixtures --state-root /tmp/round-table-release-check
```

## Contributing

Contributions are welcome, but keep the claim boundary intact: do not describe fixture success as host-live or provider-live support.

Start with `CONTRIBUTING.md`, keep the default path local-first, and include new validation evidence in your pull request.

## Development Notes

Repository-level rules live in `AGENTS.md`. For follow-up development, read these first:

1. `AGENTS.md`
2. `docs/source-truth-map.md`
3. `docs/development-sync-protocol.md`
4. `docs/release-readiness.md`

Default development loop:

- develop locally
- validate locally
- commit verified changes
- push to `origin/main`
- report what changed, what was verified, and what remains outside the claim boundary
