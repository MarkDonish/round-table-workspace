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
- `.codex/skills/room-skill/runtime/room_runtime.py`
- `.codex/skills/room-skill/runtime/README.md`
- `.codex/skills/room-skill/runtime/fixtures/canonical/`

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
- a checked-in host bridge implementation in `.codex/skills/room-skill/runtime/room_runtime.py`
- a checked-in canonical fixture pack in `.codex/skills/room-skill/runtime/fixtures/canonical/`
- repository-level entrypoints aligned so `/room` is first-class in `README.md`, `AGENTS.md`, and `examples/room-examples.md`
- a clean fallback chat contract in `docs/room-chat-contract.md`
- rebuilt and portable active prompts in:
  - `prompts/room-chat.md`
  - `prompts/room-summary.md`
  - `prompts/room-upgrade.md`
  - `prompts/room-selection.md`
- a Mac-local canonical replay path that writes evidence bundles to `artifacts/runtime/rooms/<room_id>/`

The `/debate` side is also structurally complete enough to be treated as an implemented source area, not an open sketch.

---

## What Is Not Yet Completed In This Repo

The remaining unfinished part is no longer the checked-in bridge itself.

The remaining gap is the live host integration layer:

1. the checked-in bridge is fixture-validated on Mac, but not yet proven against a real prompt-calling host loop
2. the first live `/room -> /summary -> /upgrade-to-debate` run with actual prompt execution still has not been completed
3. debate handoff is currently contract-validated through the checked-in skill entry, not yet through a live multi-agent `/debate` execution chain

In short:

`/room` is protocol-complete, prompt-cleaned, workflow-checked-in, bridge-checked-in, and fixture-validated on Mac, but not yet fully live-validated against a real prompt host.

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

- The host-side `/room` execution path now exists and is fixture-validated, but still not live-validated with actual prompt calls.
- Historical reports still reference old Windows runtime paths, which can mislead future continuation if read as implementation truth.
- The generated room bundles under `artifacts/runtime/rooms/` are outputs and must not be treated as new source-of-truth files.

---

## Recommended Next Cut

The most reasonable continuation path is:

1. point the real prompt-calling host at `.codex/skills/room-skill/runtime/room_runtime.py`
2. run the live flow from `docs/room-e2e-validation.md`
3. verify the resulting handoff packet is accepted by a real `/debate` execution, not only by contract check
4. after the live host flow passes, treat `/room` as runtime-ready instead of only bridge-ready

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
