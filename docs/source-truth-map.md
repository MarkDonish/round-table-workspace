# Source Truth Map

This document maps repository areas to their intended authority level.

Use it when continuing development, validating release scope, or handing the
repository to another local agent host.

## Authority Levels

| Area | Authority | Use For | Do Not Use For |
|---|---|---|---|
| `AGENTS.md` | Repository operating rules | Startup rules, source boundaries, `/room` and `/debate` trigger guardrails | Detailed runtime contracts |
| `LAUNCH.md` | Clone/user launch entry | Shortest safe self-check and runtime path selection for new local users or agent hosts | Replacing detailed architecture, release, or protocol docs |
| `README.md` | Project overview and entry index | Current state, capability summary, entrypoint discovery | Replacing detailed protocol docs |
| `docs/` | Active protocol and release source | Architecture, release scope, host adapters, provider readiness, sync protocol | Historical session archaeology unless under `docs/archive/` |
| `schemas/` | Active protocol schemas | Machine-checkable session, result, and handoff shapes | Runtime output storage or historical reports |
| `roundtable_core/` | Active reusable runtime source | Host-neutral protocol, runtime, path, evidence, and validation helpers | Host-specific prompt execution or generated artifacts |
| `prompts/` | Active prompt source | `/room`, `/debate`, and daily-mode prompt contracts | Runtime state persistence |
| `examples/` | Active usage examples | Human-readable examples and expected usage patterns | Release or live validation proof |
| `.codex/skills/` | Codex skill and runtime source | Canonical skill manifests, runtime bridges, validators, fixtures | Machine-local secrets or host-specific state |
| `.claude/skills/` | Claude Code adapter layer | Project-skill discovery that points back to canonical sources | Forking protocol implementation |
| `reports/` | Historical evidence | Old progress reports, setup notes, validation records, handoff context | Active protocol, runtime entrypoints, release authority |
| `artifacts/` | Generated outputs and durable fixtures | Runtime evidence, rendered exports, intentional fixtures | Active behavior source or release authority |
| `.env.*.example` | Safe config templates | Documenting required environment variables | Real secrets |
| `.env`, `.env.room`, `.env.debate` | Local-only config | Local provider/live experiments | Git-tracked source or public claims |

## Development Rule

When a report or artifact reveals a useful rule, bug, or decision:

1. Move the still-valid rule into `docs/`, `schemas/`, `roundtable_core/`, `prompts/`, `examples/`, or `.codex/skills/`.
2. Add or update a repo-local validation command when possible.
3. Cite the active source file in future work.
4. Keep the original report or artifact as historical evidence only.

Do not fix the system by editing a historical report or generated artifact.

## Release Claim Rule

Release claims are controlled by:

- `docs/release-readiness.md`
- `docs/release-candidate-scope.md`
- `.codex/skills/room-skill/runtime/release_readiness_check.py`
- `.codex/skills/room-skill/runtime/release_candidate_report.py`

Fixture, mock-provider, and readiness-preflight evidence must not be described as
real third-party host-live or provider-live support.

## Runtime Output Rule

Runtime outputs under `artifacts/runtime/` are evidence. They are not source.

New generated room output under `artifacts/runtime/rooms/` is ignored by Git by
default. Commit runtime output only when it is intentionally promoted into a
durable fixture, rendered export, or human-reviewed evidence file.

## Boundary Audit

When historical material may be confused with active source, run:

```bash
python3 .codex/skills/room-skill/runtime/source_boundary_audit.py --output-json /tmp/round-table-source-boundary-audit.json
```

The audit is read-only. Basename collisions between `reports/` or `artifacts/`
and active source files are expected historical-risk signals, not release
failures by themselves. Use `docs/historical-materials-audit.md` to interpret
the output.
