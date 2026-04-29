# Project Roadmap

> Status: active planning source for the next local-first releases.
> Last updated: 2026-04-29.

This roadmap keeps version planning separate from historical reports. It is
claim-safe by default: fixture validation, wrapper presence, and config
readiness are not host-live or provider-live support.

## Release Direction

| Horizon | Goal | Primary Documents |
|---|---|---|
| `v0.2.0-alpha` | Establish a cleaner product entry, protocol schema base, reusable core package, and milestone plan. | `docs/milestones/v0.2.0.md` |
| `v0.2.0` | Ship the v0.2 protocol/runtime foundation with schema validation, source consistency, and regression fixtures. | `docs/protocol-spec.md`, `schemas/`, `roundtable_core/` |
| after `v0.2.0` | Broaden host adapters and interactive experience only after the core contracts are stable. | `docs/host-adapter-architecture.md`, `docs/generic-local-agent-adapter.md` |

## v0.2.0 Themes

| Theme | Scope |
|---|---|
| Product entry | Make the repository understandable and usable from `./rtw`, README, transcripts, command discovery, and a golden demo. |
| Protocol kernel | Keep `/room`, `/debate`, and `/room -> /debate` schemas and quality rules explicit and testable. |
| Runtime core | Move reusable logic out of host-specific skill runtime folders into `roundtable_core/` without breaking old entrypoints. |
| Skill architecture | Generate and slim host skill files while keeping canonical protocol content in source docs and code. |
| Validation | Standardize decision quality checks, self-check output, claim dashboards, and regression fixtures. |
| Documentation governance | Keep source-of-truth boundaries, docs index, and release checks aligned with implementation. |
| Vibe experience | Add interactive affordances and a golden demo after the protocol/runtime base is testable. |

## Current v0.2.0-alpha Progress

| Task | Status | Source |
|---|---|---|
| RTW-001 unified CLI | done | `roundtable/cli.py` |
| RTW-002 README 5-minute path | done | `README.md` |
| RTW-003 transcripts | done | `examples/transcripts/` |
| RTW-005 protocol spec | done | `docs/protocol-spec.md` |
| RTW-006 room schema | done | `schemas/room-session.schema.json` |
| RTW-007 debate schema | done | `schemas/debate-session.schema.json`, `schemas/debate-result.schema.json` |
| RTW-010 `roundtable_core` initial abstraction | done | `roundtable_core/` |
| RTW-027 v0.2.0 milestone docs | done | `docs/milestones/v0.2.0.md` |

## Out Of Scope For Roadmap Claims

- Do not claim universal third-party host-live support.
- Do not require provider-live support for the local mainline.
- Do not describe fixture pass, mock-provider pass, wrapper existence, or config
  readiness as live support.
- Do not treat `reports/` or generated `artifacts/` as active roadmap source.

## Planning Links

- `docs/milestones/v0.2.0.md`
- `docs/release-candidate-scope.md`
- `docs/source-truth-map.md`
- `docs/host-adapter-architecture.md`
- `docs/protocol-spec.md`
