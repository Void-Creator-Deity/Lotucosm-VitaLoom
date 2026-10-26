# E183 Fresh-Session Prompt — Scene Entity Generic-Property Guarded-History Contract Decision Gate

E183 is complete with **no migration**. Both entity lifecycle directions are stale-safe, but `entity.set_property -> entity.restore_snapshot -> redo entity.set_property` remains compatibility-only rather than a guarded scene-history contract.

## Recorded outcome

- Inspector position axes use `transform.set`; script keys use `script.set_property`; every remaining non-private entity field, including tested `energy`, reaches generic `entity.set_property`.
- The generic command accepts arbitrary dotted paths and unbounded values. Its helper can create dictionaries or replace scalar/list intermediates, including in structural regions such as `id`, `position`, and `scripts`.
- Its undo inverse replaces the whole pre-mutation entity through `entity.restore_snapshot`; there is no expected-current guard on undo or redo.
- A full-scene witness alone would not establish a narrow field schema or make broad snapshot replacement a suitable public semantic inverse. No runtime behavior changed.
- Scene-owned semantic rejection stays terminal; E175/E177 local fallback remains only for non-scene/ownerless cases. Audit is schema v4 and `unified_undo_redo_runtime=false`.

## Next work boundary

Proceed only with E184: audit `script.set_property` for a possible serialized-identity, field-specific guarded-history contract. Do not expand the generic entity setter or bypass the E183 blocker.

Read:

- `docs/superpowers/plans/2026-08-01-scene-entity-generic-property-guarded-history-contract-decision-gate.md`
- `docs/superpowers/plans/2026-08-01-scene-script-property-serialized-identity-guarded-history-contract-inventory-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/command_binding.py`

Do not touch `CONTEXT.md`, unrelated dirty work, manifests, `.pond` semantics, the Qt-free L0-L4 boundary, WorldBridge, native acceleration, or OpenGL-default status. Never route a rejected scene-owned semantic mutation back to local history.