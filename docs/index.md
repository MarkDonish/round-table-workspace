# Documentation Index

> Purpose: route users, maintainers, and release reviewers to the right active
> source files without treating historical reports as implementation authority.

## Start Here

| Document | Use |
|---|---|
| `README.md` | Project overview, five-minute path, support boundary, and key links. |
| `LAUNCH.md` | Shortest safe startup path for fresh clones and local agent hosts. |
| `AGENTS.md` | Repository operating rules, explicit-only triggers, and source boundaries. |
| `docs/user-entry-guide.md` | Plain-language explanation of the repository logic. |

## User Guides

| Document | Use |
|---|---|
| `docs/agent-consumer-quickstart.md` | Clone-friendly commands for Codex, Claude Code, and generic local agents. |
| `examples/transcripts/` | Illustrative `/room`, `/debate`, and handoff walkthroughs. |
| `docs/roadmap.md` | Release horizons and roadmap direction. |
| `docs/milestones/v0.2.0.md` | v0.2.0 task scope and status. |

## Protocol Specs

| Document | Use |
|---|---|
| `docs/protocol-spec.md` | Unified `/room`, `/debate`, and `/room -> /debate` overview. |
| `docs/room-architecture.md` | Detailed `/room` behavior and state rules. |
| `docs/debate-skill-architecture.md` | Detailed `/debate` routing and review workflow. |
| `docs/room-to-debate-handoff.md` | Handoff contract from exploration to decision review. |
| `docs/reviewer-protocol.md` | Reviewer behavior, red flags, and allow/reject logic. |
| `docs/decision-quality-rubric.md` | Decision quality scoring dimensions for eval and reviewer use. |
| `docs/agent-factory-architecture.md` | Agent Factory lifecycle, registry split, and current backend boundary. |
| `schemas/room-session.schema.json` | Portable `/room` session state shape. |
| `schemas/debate-session.schema.json` | Portable `/debate` session state shape. |
| `schemas/debate-result.schema.json` | Portable `/debate` final result shape. |
| `schemas/room-to-debate-handoff.schema.json` | Portable handoff packet shape. |
| `schemas/agent-manifest.schema.json` | Agent Factory manifest shape. |
| `schemas/agent-registry.schema.json` | Agent Factory custom/candidate registry shape. |
| `schemas/agent-selection-request.schema.json` | Selection bridge request shape for later `/debate --pool` work. |

## Runtime And Adapters

| Document | Use |
|---|---|
| `docs/room-runtime-bridge.md` | Room runtime bridge and persistence rules. |
| `docs/debate-runtime-bridge.md` | Debate runtime bridge and packet validation. |
| `docs/host-adapter-architecture.md` | Host adapter layers and boundaries. |
| `docs/generic-local-agent-adapter.md` | Generic local CLI agent adapter contract. |
| `docs/local-agent-host-recipes.md` | Host-specific validation recipes. |
| `docs/third-party-agent-wrapper-recipes.md` | Wrapper recipes for noisy local CLI agents. |
| `docs/skill-generation.md` | Skill generator and drift-check maintenance path. |
| `docs/agent-builder-workflow.md` | Agent Builder validation and registry workflow. |
| `docs/agent-library-ui.md` | Future local UI data contract notes. |

## Validation And Release

| Document | Use |
|---|---|
| `docs/source-truth-map.md` | Active source versus historical/generated boundary. |
| `docs/release-readiness.md` | Release gate rules. |
| `docs/release-candidate-scope.md` | Claim-safe release support scope. |
| `docs/provider-live-readiness.md` | Provider fallback readiness rules. |
| `reports/claim-boundary-dashboard.md` | Generated dashboard of claimable, blocked, and unconfigured lanes. |
| `CHANGELOG.md` | Release history and unreleased changes. |

## Historical And Generated Material

| Area | Boundary |
|---|---|
| `reports/` | Historical evidence, generated dashboards, release records, and old handoff context. Not active implementation source. |
| `artifacts/` | Runtime outputs, rendered exports, and durable fixtures. Not active behavior source. |
| `docs/archive/` | Archived source snapshots for archaeology only. |
