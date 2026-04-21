# Router Mode Overrides

> Purpose: define how explicit `/room` and `/debate` commands override the default daily router, so mode routing stays stable across hosts.
> Last reviewed: 2026-04-21

---

## Role

`docs/router.md` describes the default daily routing behavior.

This document defines the explicit mode overrides that take priority when the user intentionally enters a structured mode.

It exists to remove ambiguity between:

- the default daily router
- the stateful `/room` flow
- the explicit `/debate` flow

---

## Precedence Order

When deciding what system should handle the next user input, use this order:

1. explicit slash mode command
2. existing active mode context
3. default daily router in `docs/router.md`

That means:

- `/room ...` overrides the default router
- `/debate ...` overrides the default router
- once the conversation is already inside an active `/room` context, `/focus`, `/summary`, `/upgrade-to-debate`, `/add`, and `/remove` stay inside `/room`
- the default router should only be used when the user is not explicitly entering or continuing a structured mode

---

## `/room` Override

If the user explicitly enters `/room`, routing must hand control to `.codex/skills/room-skill/SKILL.md`.

While `/room` is active:

- `/focus <focus text>` remains in `/room`
- `/summary` remains in `/room`
- `/upgrade-to-debate` starts from `/room` and can only leave via a valid handoff packet
- `/add <agent>` remains in `/room`
- `/remove <agent>` remains in `/room`

The default daily router must not intercept these commands.

---

## `/debate` Override

If the user explicitly enters `/debate`, routing must hand control to `.codex/skills/debate-roundtable-skill/SKILL.md`.

While `/debate` is active:

- debate-specific follow-ups stay in `/debate`
- the daily router must not silently remap the issue back into a casual daily skill set

---

## Cross-Mode Rule

`/room` and `/debate` are siblings, not aliases.

Rules:

1. do not auto-convert `/room` into `/debate`
2. do not auto-convert `/debate` into `/room`
3. `/room -> /debate` is allowed only through the checked-in handoff contract
4. a raw room transcript must not be used as a direct `/debate` input substitute

---

## Source References

This override document depends on:

- `docs/router.md`
- `docs/room-runtime-bridge.md`
- `docs/room-to-debate-handoff.md`
- `.codex/skills/room-skill/SKILL.md`
- `.codex/skills/debate-roundtable-skill/SKILL.md`

If there is a conflict, explicit mode contracts win over the default daily router.

---

## Non-Goals

- This document does not replace `docs/router.md`.
- This document does not redefine the internal logic of `/room`.
- This document does not redefine the internal logic of `/debate`.
- This document does not claim the host runtime is already complete.