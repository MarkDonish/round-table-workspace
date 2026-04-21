# Room Runtime Status

> Purpose: lock the real `/room` implementation boundary after the Windows-to-GitHub migration, so Mac-side continuation uses checked-in source instead of historical reports.
> Last reviewed: 2026-04-21

---

## Source Of Truth

The current source-of-truth files for `/room` are:

- `README.md`
- `AGENTS.md`
- `docs/room-architecture.md`
- `docs/room-selection-policy.md`
- `docs/room-to-debate-handoff.md`
- `docs/agent-registry.md`
- `docs/room-chat-contract.md`
- `docs/room-runtime-bridge.md`
- `docs/room-runtime-status.md`
- `docs/room-e2e-validation.md`
- `docs/DECISIONS-LOCKED.md`
- `prompts/room-selection.md`
- `prompts/room-summary.md`
- `prompts/room-upgrade.md`
- `prompts/room-chat.md`
- `examples/room-examples.md`
- `.codex/skills/room-skill/SKILL.md`
- `.codex/skills/room-skill/WORKFLOW.md`

If a report, checkpoint, or session artifact conflicts with the files above, the files above win.

---

## What Is Already Completed

The repository already contains a largely complete source layer for `/room`:

- state model, ownership, command semantics, and host responsibilities in `docs/room-architecture.md`
- selection policy and scoring rules in `docs/room-selection-policy.md`
- `/room -> /debate` handoff schema in `docs/room-to-debate-handoff.md`
- a checked-in portable agent registry in `docs/agent-registry.md`
- an implementation-facing runtime bridge contract in `docs/room-runtime-bridge.md`
- a checked-in runtime workflow playbook in `.codex/skills/room-skill/WORKFLOW.md`
- a checked-in `/room` runtime entry in `.codex/skills/room-skill/SKILL.md`
- a checked-in end-to-end validation guide in `docs/room-e2e-validation.md`
- repository-level entrypoints aligned so `/room` is first-class in `README.md`, `AGENTS.md`, and `examples/room-examples.md`
- a clean fallback chat contract in `docs/room-chat-contract.md`
- rebuilt and portable active prompts in:
  - `prompts/room-chat.md`
  - `prompts/room-summary.md`
  - `prompts/room-upgrade.md`
  - `prompts/room-selection.md`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open sketch.

---

## What Is Not Yet Completed In This Repo

The remaining unfinished part is no longer the checked-in source definition.

The remaining gap is the host-side portable execution and validation layer:

1. the checked-in workflow and bridge still need a real host-side state persistence path that is proven end to end on Mac
2. the first real `/room -> /summary -> /upgrade-to-debate` validation run still has not been completed against a live host flow
3. the local terminal Git chain on this Mac is still not fully usable until GitHub trusts the prepared SSH key

In short:

`/room` is protocol-complete, prompt-cleaned, workflow-checked-in, validation-specified, and entry-aligned, but not yet host-validated as a portable runnable feature.

---

## How To Treat Reports

`reports/` is historical evidence, not runtime source.

Use reports to understand:

- why a decision was made
- what was validated at the time
- what existed on the Windows machine

Do not use reports as the sole authority for:

- current prompt contracts
- runtime entrypoints
- path references
- portable implementation truth

The same rule applies to `artifacts/`: they are outputs, not authoring source.

---

## Current Risks

- The host-side `/room` execution path is specified, but still not live-validated on this Mac.
- Historical reports still reference old Windows runtime paths, which can mislead future continuation if read as implementation truth.
- Local terminal Git is still one GitHub-side trust step away from working end to end on this machine.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. wire the host-side `/room` execution path to the checked-in `WORKFLOW.md`
2. run the first real flow from `docs/room-e2e-validation.md`
3. verify the resulting handoff packet is accepted by `debate-roundtable-skill`
4. after the host flow passes, treat `/room` as runtime-ready instead of only source-ready

This keeps the repository structure stable:

- `docs/`, `prompts/`, `examples/`, `.codex/skills/` stay as source
- `reports/` remains historical
- `artifacts/` remains generated output

---

## Non-Goals

- Do not move historical reports into source directories.
- Do not treat old session notes as stronger than current docs and prompts.
- Do not redesign `/debate`.
- Do not rewrite repo structure unless a concrete source/runtime conflict requires it.