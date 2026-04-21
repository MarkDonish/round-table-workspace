# Room Runtime Status

> Purpose: lock the current `/room` implementation boundary after the Windows-to-GitHub migration, so Mac-side continuation does not treat historical reports as executable source.
> Last reviewed: 2026-04-21

---

## Source Of Truth

The current source-of-truth files for `/room` in this repository are:

- `README.md`
- `AGENTS.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `docs/room-chat-contract.md`
- `docs/room-runtime-bridge.md`
- `docs/room-runtime-status.md`
- `docs/DECISIONS-LOCKED.md`
- `prompts/room-selection.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/room-chat.md`
- `examples/room-examples.md`
- `.codex/skills/room-skill/SKILL.md`
- `.codex/skills/room-skill/WORKFLOW.md`

If a report or session note conflicts with the files above, the files above win.

---

## What Is Already Completed

The repository already contains a largely complete protocol layer for `/room`:

- state model, ownership, and command semantics in `docs/room-architecture.md`
- selection and scheduling policy in `docs/room-selection-policy.md`
- `/room -> /debate` handoff schema in `docs/room-to-debate-handoff.md`
- a checked-in agent registry in `docs/agent-registry.md`
- an implementation-facing runtime bridge contract in `docs/room-runtime-bridge.md`
- active prompt contracts for selection, summary, and upgrade in `prompts/`
- a clean fallback contract for chat in `docs/room-chat-contract.md`
- a rebuilt and readable `prompts/room-chat.md`
- a checked-in `/room` source entry aligned with the registry and bridge contract in `.codex/skills/room-skill/SKILL.md`
- a checked-in runtime workflow playbook in `.codex/skills/room-skill/WORKFLOW.md`
- repository-level entrypoints now aligned so `/room` is first-class in `README.md`, `AGENTS.md`, and `examples/room-examples.md`
- architecture decisions confirming the dual-mode product (`/room` + `/debate`) in `docs/DECISIONS-LOCKED.md`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open design sketch.

---

## What Is Not Yet Completed In This Repo

The final incomplete part is no longer the `/room` workflow description. It is the host-side portable execution and live validation layer.

The main gaps are:

1. The checked-in runtime playbook now exists, but the host-side state persistence and execution path still have not been proven end to end on Mac.
2. Some active prompt files still contain Windows-local absolute links in legacy header references, especially `prompts/room-selection.md`, `prompts/room-summary.md`, and `prompts/room-upgrade.md`.
3. The `/room` flow still needs a real `/room -> /summary -> /upgrade-to-debate` validation run before production use.

In short:

`/room` is protocol-complete, workflow-checked-in, entry-aligned, but not yet host-validated as a portable runnable feature.

---

## How To Treat Reports

`reports/` is historical evidence, not the runtime source.

Use reports to understand:

- why a decision was made
- what was validated
- what existed on the Windows machine

Do not use reports as the only source for:

- current prompt contracts
- path references
- runtime entrypoints
- implementation truth

The same rule applies to `artifacts/`: they are outputs, not authoring source.

---

## Current Risks

- Windows-local absolute links still remain in a few active prompt headers, which can create cross-machine confusion even when the underlying protocol is correct.
- The host-side `/room` execution path is now specified, but still not live-validated on this Mac.
- Reports still reference external Windows runtime paths that are not present in this repository, which can create a false impression that the runtime is already checked in.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. finish normalizing the remaining Windows-local links in active `/room` prompts
2. connect the host-side `/room` execution path to the checked-in `WORKFLOW.md`
3. run a first end-to-end `/room -> /summary -> /upgrade-to-debate` validation flow
4. only after that, continue deeper runtime-level implementation

This keeps the current repository structure stable:

- `docs/`, `prompts/`, `examples/`, `.codex/skills/` stay as source
- `reports/` remains historical
- `artifacts/` remains generated output

---

## Non-Goals

- Do not move historical reports into source directories.
- Do not treat old session notes as stronger than current docs/prompts.
- Do not redesign `/debate`.
- Do not rewrite repo structure unless a concrete source/runtime conflict requires it.
