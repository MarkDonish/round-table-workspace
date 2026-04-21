# Room Runtime Status

> Purpose: lock the current `/room` implementation boundary after the Windows-to-GitHub migration, so Mac-side continuation does not treat historical reports as executable source.
> Last reviewed: 2026-04-21

---

## Source Of Truth

The current source-of-truth files for `/room` in this repository are:

- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `docs/room-chat-contract.md`
- `docs/room-runtime-status.md`
- `docs/DECISIONS-LOCKED.md`
- `prompts/room-selection.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/room-chat.md`
- `.codex/skills/room-skill/SKILL.md`

If a report or session note conflicts with the files above, the files above win.

---

## What Is Already Completed

The repository already contains a largely complete protocol layer for `/room`:

- state model, ownership, and command semantics in `docs/room-architecture.md`
- selection and scheduling policy in `docs/room-selection-policy.md`
- `/room -> /debate` handoff schema in `docs/room-to-debate-handoff.md`
- a checked-in agent registry in `docs/agent-registry.md`
- active prompt contracts for selection, summary, and upgrade in `prompts/`
- a clean fallback contract for chat in `docs/room-chat-contract.md`
- a rebuilt and readable `prompts/room-chat.md`
- a checked-in source entry for `/room` in `.codex/skills/room-skill/SKILL.md`
- architecture decisions confirming the dual-mode product (`/room` + `/debate`) in `docs/DECISIONS-LOCKED.md`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open design sketch.

---

## What Is Not Yet Completed In This Repo

The final incomplete part is not the `/room` protocol itself. It is the checked-in runtime bridge and Mac-ready execution layer.

The main gaps are:

1. `.codex/skills/room-skill/SKILL.md` now exists as a source entry, but the orchestrator/runtime entry behind it is still not present as checked-in source.
2. Active `/room` source files still contain Windows-local absolute links such as `/C:/Users/CLH/...`, which should not remain in source.
3. The `/room` prompt layer is now structurally usable, but it still needs runtime-level integration and live validation before production use.

In short:

`/room` is protocol-complete, but repo-incomplete as a portable runnable feature.

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

- Windows absolute links in source prompts and skills create cross-machine breakage and confusion.
- The runtime bridge behind `/room` is still implied by source, not implemented as checked-in orchestrator code.
- Reports reference external Windows runtime paths that are not present in this repository, which can create a false impression that the runtime is already checked in.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. normalize remaining Windows absolute links in active source files and skill references
2. implement the runtime bridge behind `.codex/skills/room-skill/SKILL.md` using `docs/agent-registry.md` + `prompts/`
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
