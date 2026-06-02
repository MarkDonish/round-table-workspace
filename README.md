# Round Table Workspace

[![CI](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/MarkDonish/round-table-workspace/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Local First](https://img.shields.io/badge/local--first-yes-2ea44f)
![AI Agents](https://img.shields.io/badge/AI%20agents-round--table-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Demo: https://markdonish.github.io/round-table-workspace/

Make your AI coding agents argue before they ship.

Round Table Workspace is a local-first decision layer for Codex, Claude Code,
and other CLI agents. It turns vague product and engineering questions into
structured `/room` exploration, escalates risky choices into `/debate`, and
adds a `ship-check` gate that returns a practical ship / revise / reject review
before you trust one AI-generated answer.

```bash
git clone https://github.com/MarkDonish/round-table-workspace.git
cd round-table-workspace
./rtw ship-check "Should we merge this AI-generated feature?"
./rtw room "What is the smallest useful MVP for this idea?"
./rtw debate "Is this launch ready?"
./rtw doctor --quick
```

Example `ship-check` shape:

```text
Decision: revise
Panel: product, engineering, risk, user-advocate
Why: useful direction, but public claims and evidence need tightening
Next: run tests, add a visible demo, keep claims local-first unless validated
```

## Why This Exists

AI coding agents are fast. Too fast.

They can produce a feature before anyone asks:

- should we build this at all?
- what evidence would change our mind?
- what user risk are we ignoring?
- is this actually ready to ship, or just plausible-looking?
- are we claiming host-live/provider-live support without evidence?

Round Table Workspace adds a decision layer before execution. It is not another
chat UI. It is a checked-in protocol, CLI, schema set, fixture-backed runtime,
and evidence trail for making AI-assisted decisions reviewable.

## 30-Second Demo

Run the new pre-ship decision gate:

```bash
./rtw ship-check "Launch the new AI-generated onboarding flow"
```

Run the clone-friendly self-check:

```bash
./rtw doctor --quick
```

Try the fixture-backed room/debate surfaces:

```bash
./rtw room "I want to build an AI study product for college students"
./rtw debate "Should this MVP be shipped this week?"
```

Run the golden demo without provider setup:

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
    A[Ambiguous idea or AI-generated change] --> B[/room exploration]
    B --> C[summary + handoff packet]
    C --> D[/debate decision review]
    D --> E{ship-check gate}
    E -->|ship| F[Proceed with evidence]
    E -->|revise| G[Fix risks / collect missing evidence]
    E -->|reject| H[Stop or reframe]
    F --> I[JSON + Markdown artifacts]
    G --> I
    H --> I
```

Core surfaces:

| Command | Use it when | Output |
|---|---|---|
| `ship-check` | You need a quick ship / revise / reject review before trusting AI-generated work | panel votes, risks, missing evidence, next actions |
| `/room` / `./rtw room` | You are still exploring a topic and need a stateful multi-agent discussion | selected panel, structured turns, summaries, optional handoff packet |
| `/debate` / `./rtw debate` | You need a higher-stakes decision reviewed by a round table | launch bundle, round-table record, reviewer result, allow/reject/follow-up outcome |
| `doctor` | You want to know whether a fresh clone is usable locally | JSON/Markdown evidence under a chosen state root |
| `release-check` | You want release-scope validation without replacing historical reports | aggregated readiness evidence |

## Use Cases

- Pre-ship review for AI-generated code or docs
- Product decision review before building an MVP
- Architecture tradeoff review before refactoring
- Risk review before publishing launch claims
- Local-first agent workflow experiments
- Decision evidence generation for Codex / Claude Code projects
- Teaching teams not to trust a single confident agent answer

## Current Support Scope

The current release is `v0.2.2-pages-launch-kit`.

The repository may currently be used for:

- Codex local mainline `/room`
- Codex local mainline `/debate`
- Codex local mainline `/room -> /debate`
- fixture-backed `ship-check` decision-gate scaffolding
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

The project is intentionally conservative about claims. A fixture pass, wrapper
presence, or config preflight is not described as real host-live or
provider-live support unless matching validation evidence exists.

## Repository Map

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

Active source of truth:

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

When a report or artifact reveals a still-valid rule, the rule should be moved
into active source files instead of leaving historical material as the authority.

## Key Documents

| Document | Purpose |
|---|---|
| `LAUNCH.md` | shortest safe startup path for a fresh clone |
| `docs/index.md` | documentation map by user, protocol, runtime, validation, and historical areas |
| `docs/user-entry-guide.md` | plain-language guide to the repository logic |
| `docs/agent-consumer-quickstart.md` | commands for Codex, Claude Code, and generic local agents |
| `docs/source-truth-map.md` | source vs historical/output boundary |
| `docs/release-readiness.md` | release gate rules |
| `docs/release-candidate-scope.md` | claim-safe support scope |
| `docs/roadmap.md` | project roadmap and release horizons |
| `docs/milestones/v0.2.0.md` | v0.2.0 milestone scope and issue split |
| `docs/launch-copy.md` | public launch copy for X, Hacker News, Reddit, and community posts |
| `docs/demo.html` | static visual demo for GitHub Pages or screenshots |
| `docs/protocol-spec.md` | unified `/room`, `/debate`, and handoff protocol overview |
| `docs/protocol-versioning.md` | release/protocol/schema/runtime/prompt/fixture version boundaries |
| `docs/decision-quality-rubric.md` | machine-checkable decision quality rubric |
| `docs/schema-validation-subset.md` | Draft 2020-12 fallback validator boundary |
| `docs/skill-generation.md` | generated skill summary and drift-check maintenance |
| `docs/agent-factory-architecture.md` | Agent Factory manifest, profile, and registry lifecycle |
| `agents/registry.json` | machine-readable agent registry consumed by runtime bridges |
| `config/agent-registry.json` | Agent Factory custom/candidate registry |
| `schemas/room-session.schema.json` | portable `/room` session state schema |
| `schemas/debate-session.schema.json` | portable `/debate` session state schema |
| `schemas/debate-result.schema.json` | portable `/debate` result schema |
| `schemas/room-to-debate-handoff.schema.json` | portable `/room -> /debate` handoff schema |
| `schemas/agent-manifest.schema.json` | Agent Factory manifest schema |
| `schemas/agent-registry.schema.json` | Agent Factory custom/candidate registry schema |
| `schemas/agent-selection-request.schema.json` | future selection bridge request schema |
| `docs/room-architecture.md` | `/room` protocol and behavior |
| `docs/debate-skill-architecture.md` | `/debate` protocol and behavior |
| `docs/room-to-debate-handoff.md` | handoff contract from exploration to review |
| `docs/generic-local-agent-adapter.md` | generic local CLI agent contract |
| `examples/transcripts/` | illustrative `/room`, `/debate`, and handoff walkthroughs |
| `reports/claim-boundary-dashboard.md` | generated snapshot only; run `./rtw evidence` or `./rtw release-check` for current status |
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
./rtw release-check --include-fixtures --state-root /tmp/round-table-release-check
```

## Contributing

Contributions are welcome when they preserve the claim boundary: do not turn a
fixture pass into a host-live or provider-live claim. Start with
`CONTRIBUTING.md`, keep changes local-first by default, and include fresh
verification evidence in PRs.

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
