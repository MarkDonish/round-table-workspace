# Protocol Versioning

> Purpose: separate release, protocol, schema, runtime artifact, prompt, and
> fixture versions so migration checks do not treat different layers as the same
> thing.
>
> Status: active governance source for v0.2.1.

## Version Layers

| Layer | Example | Meaning | Source |
|---|---|---|---|
| Release version | `v0.2.0-alpha` | Product/repo release label shown in README, LAUNCH, changelog, and release notes. | `README.md`, `LAUNCH.md`, `CHANGELOG.md`, `docs/releases/` |
| Protocol version | `v0.2` | Human protocol family for `/room`, `/debate`, and handoff behavior. | `docs/protocol-spec.md`, architecture docs |
| Schema version | `0.1.0` | Portable JSON artifact schema version. Must remain semver-like and should not include a leading `v`. | `schemas/*.schema.json`, portable fixtures |
| Runtime artifact version | `v0.1` | Legacy checked-in runtime packet or launch bundle version. May use historical labels until migrated. | runtime scripts and canonical fixtures |
| Prompt version | `room-chat v0.1` | Prompt contract version embedded in prompt outputs or prompt docs. | `prompts/*.md` |
| Fixture version | `0.1.0` | Test fixture shape version; usually follows the schema version it exercises. | `examples/fixtures/`, `tests/fixtures/` |

## Rules

1. Release versions may use prerelease labels such as `v0.2.0-alpha`.
2. Portable schema versions use `0.1.0` style values.
3. Legacy runtime artifacts may keep `v0.1` only when a projection or migration
   function converts them into portable schema objects.
4. New portable artifacts should not introduce `v0.1` unless they are explicitly
   marked legacy.
5. `docs/protocol-spec.md` owns the current protocol family, while individual
   schemas own exact artifact fields.

## Handoff Migration Plan

The legacy `/room -> /debate` packet uses `schema_version: "v0.1"` inside the
runtime bridge. The portable handoff schema uses `schema_version: "0.1.0"`.

Current migration path:

1. Runtime may still emit or consume legacy `v0.1` packets for compatibility.
2. `roundtable_core.protocol.handoff.runtime_packet_to_portable_handoff`
   projects legacy packets into portable `0.1.0` handoff objects.
3. CLI/runtime projection writes portable handoff artifacts into standard
   `runs/<run_id>/` directories.
4. Release checks validate portable artifacts, not raw legacy packets.

Deprecation rule: legacy `v0.1` should remain accepted until a future release
notes an explicit breaking change. Any new runtime field must first appear in
the portable schema and fixture set before removing the legacy projection.

## Release Check Expectations

`scripts/check_source_truth_consistency.py` checks that README/LAUNCH agree on
the release label and warns on obvious authority confusion. It should not reject
valid schema `0.1.0` values simply because the current release is
`v0.2.0-alpha`.
