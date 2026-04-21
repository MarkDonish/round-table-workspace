# Room Runtime Status

> Purpose: lock the current `/room` implementation boundary after the Windows-to-GitHub migration, so Mac-side continuation does not treat historical reports as executable source.
> Last reviewed: 2026-04-21

---

## Source Of Truth

The current source-of-truth files for `/room` in this repository are:

- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/DECISIONS-LOCKED.md`
- `prompts/room-selection.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/room-chat.md`

If a report or session note conflicts with the files above, the files above win.

---

## What Is Already Completed

The repository already contains a largely complete protocol layer for `/room`:

- state model, ownership, and command semantics in `docs/room-architecture.md`
- selection and scheduling policy in `docs/room-selection-policy.md`
- `/room -> /debate` handoff schema in `docs/room-to-debate-handoff.md`
- active prompt contracts for selection, summary, and upgrade in `prompts/`
- architecture decisions confirming the dual-mode product (`/room` + `/debate`) in `docs/DECISIONS-LOCKED.md`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open design sketch.

---

## What Is Not Yet Completed In This Repo

The final incomplete part is not the `/room` protocol itself. It is the checked-in runtime bridge and Mac-ready execution layer.

The main gaps are:

1. `.codex/skills/room-skill/SKILL.md` is missing from the repository.
2. The orchestrator/runtime entry that should consume the `/room` docs and prompts is not present as checked-in source.
3. `docs/agent-registry.md` is absent, even though reports and plans assume a registry/runtime layer exists.
4. Active `/room` prompt files still contain Windows-local absolute links such as `/C:/Users/CLH/...`, which should not remain in source.
5. `prompts/room-chat.md` contains import-time encoding damage in its main body. The trailing English addendum is readable, but the main Chinese contract text is not safe to treat as healthy source without repair.

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

- Windows absolute links in source prompts create cross-machine breakage and confusion.
- `prompts/room-chat.md` cannot be trusted as-is for future maintenance until its corrupted body is repaired.
- Reports reference external Windows runtime paths that are not present in this repository, which can create a false impression that the runtime is already checked in.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. normalize Windows absolute links in active `/room` source prompts
2. repair or reconstruct `prompts/room-chat.md` from `docs/room-architecture.md`
3. add the missing `.codex/skills/room-skill/SKILL.md`
4. only after that, continue runtime-level implementation

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
