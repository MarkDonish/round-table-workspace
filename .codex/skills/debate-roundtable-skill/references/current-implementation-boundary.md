# /debate Current Implementation Boundary

This reference holds long-form implementation status that used to live in
`SKILL.md`. The skill entrypoint keeps only trigger, routing, reviewer, and
source rules.

## Claimable Local-First Source

- `/debate` protocol, prompts, schemas, reviewer rules, and runtime bridge are
  source-controlled.
- `debate_packet_validator.py`, `debate_runtime.py`, and
  `debate_e2e_validation.py` remain the canonical debate runtime entrypoints.
- `/room -> /debate` handoff consumes a packet, not a raw room log.
- Generic local CLI and Claude Code routes may use the fixture agent to validate
  adapter shape, but fixture validation is not host-live support.
- Release readiness and release candidate reports distinguish claimable local
  mainline support from provider-live and host-live gaps.

## Boundary

- `/debate` is not a live multi-agent executor claim by itself.
- Real Claude Code or third-party local-agent host-live support requires matching
  live validation evidence.
- Real provider-live support requires valid `.env.room` / `.env.debate` and live
  validation success.
