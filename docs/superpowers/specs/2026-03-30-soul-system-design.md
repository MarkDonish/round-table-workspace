# Soul System Design

Date: 2026-03-30

## Intent

Build a personal Soul system that preserves a continuous, evidence-backed record of a person's identity, shifts, patterns, and high-value expressions across time.

The system is not a chat summary tool and not a personal branding engine.
It exists to help a human preserve their distinctiveness inside an AI-saturated information environment.

## Core Goals

1. Preserve identity continuity across conversations, months, and platforms.
2. Protect individual distinctiveness from flattening, templating, or beautifying.
3. Support gradual understanding instead of one-shot profiling.
4. Distill durable Soul Assets from large volumes of output.
5. Keep the record alive through ongoing updates and interviews.

## Two-Skill Architecture

### soul-keeper

The active operator.
It ingests new material, runs interviews, creates Soul Entries, promotes observations through the memory ladder, and decides whether durable files should change.

### soul-record

The storage contract.
It keeps the archive human-readable, preserves time and evidence boundaries, and defines how files and folders should be maintained.

## Archive Model

### Core Layer

Stable traits, values, themes, direction, and expressive signatures that should change slowly.

### Dynamic Layer

Current tensions, desires, conflicts, moods, and recent focus areas that should remain time-bound.

### Asset Layer

Representative writings, phrases, questions, and ideas that feel distinctly like the owner and deserve long-term retention.

### Protocol Layer

Rules for ingestion, promotion, update thresholds, evidence handling, and anti-template discipline.

## Memory Ladder

1. Conversation Memory
2. Candidate Memory
3. Soul Memory

Default pattern:
observe -> candidate -> confirm -> write

## Evidence Constraints

- preserve source evidence
- separate self-claims from agent inference
- require stronger proof before declaring a shift
- keep contradictions visible instead of resolving them away

## Token Strategy

Use three operating modes:

- `Light`: daily capture only
- `Review`: periodic consolidation
- `Deep Update`: monthly interviews, historical ingestion, major shifts

Use the lightest mode that preserves quality.

## Human vs Agent Files

### Human-Facing

- `Soul.md`
- `timeline/Soul.timeline.md`
- `shifts/Phase.Map.md`
- `monthly/*.md`
- `questions/Open Questions.md`

### Agent-Facing

- `Soul.protocol.md`
- `Soul.schema.md`
- skill metadata and reference files

## Initial Deliverables

1. `soul-keeper` skill
2. `soul-record` skill
3. starter Soul archive at `C:\Users\CLH\soul`
4. initial protocol and schema files
5. starter timeline, questions, and phase map files
