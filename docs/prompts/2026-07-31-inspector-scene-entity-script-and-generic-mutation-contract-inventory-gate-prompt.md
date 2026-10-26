# E179 Completion Handoff — Inspector Scene-Entity Script and Generic Mutation Contract Inventory Gate

E179 is complete. It audited the active-scene Inspector `script_*` and generic public entity-property routes and deliberately selected **no migration**.

## What E179 proved

- `script.set_property` has a stable entity ID but not a stable script selector: it accepts `name`, `type` or `path` and chooses the first match. Its dotted property path can materialize JSON objects, its value is untyped, and its inverse unconditionally rewrites the old/new value.
- `entity.set_property` accepts arbitrary dot paths and values. Its history inverse is `entity.restore_snapshot`, which replaces the whole entity without an expected-current witness and can overwrite later canonical edits.
- Both commands participate in audit selection and representative fresh-registry durable replay, but this does not make their inverse operations stale-safe.
- The Inspector preserves the correct authority boundary: successful semantic writes request `scene.open`; rejected semantic calls are terminal and never fall back to local `CommandStack` mutation.

## Evidence

- Focused offscreen suite: `46 passed, 9 subtests passed in 2.76s`.
- `py_compile` passed for the relevant runtime, Inspector and test modules.
- AI-command audit-status, core-boundary and GUI-boundary checks passed.
- Audit status remains schema version 4 and `unified_undo_redo_runtime=false`.

## Not completed or claimed

- Neither broad script nor generic entity property mutation now has a complete typed, identity-safe, stale-guarded history contract.
- Unified runtime undo/redo, WorldBridge, native acceleration and OpenGL default readiness remain incomplete.
- E175/E177 ownerless/non-scene Inspector local fallback remains required.

## Read before continuing

- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-script-and-generic-mutation-contract-inventory-gate.md`
- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-name-mutation-contract-discovery-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`

## Exactly one next gate

**E180 — Inspector Scene-Entity Name Mutation Contract Discovery Gate.** Restrict the investigation to the canonical active-scene entity `name` field. Do not add or broaden a generic setter. Only migrate if a concrete string schema/normalization rule, field-specific expected-current inverse, durable stale replay evidence and canonical rehydration proof all exist.