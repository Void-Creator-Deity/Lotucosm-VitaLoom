# E180 Fresh-Session Prompt — Inspector Scene-Entity Name Mutation Contract Discovery Gate

E179 is complete. It selected no broad script or generic entity mutation migration because their selector/value/inverse contracts are insufficient.

## Read first

- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-script-and-generic-mutation-contract-inventory-gate.md`
- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-name-mutation-contract-discovery-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`

## Rules

- Audit only active-scene entity `name`; `entity_id` remains the stable identity and must never be made mutable through this slice.
- Build the complete owner/path/string-schema/history/rehydration matrix before changing behavior.
- Do not use `entity.set_property` or `entity.restore_snapshot` as proof that a field-specific inverse is safe.
- Semantic rejection must remain terminal: no local `CommandStack` fallback for a scene-owned entity.
- Preserve E175/E177 local fallback for non-scene or ownerless objects.
- Do not expand `script.set_property` or a generic Registry setter.
- `unified_undo_redo_runtime=false` remains authoritative.

## Completion expectation

Select one name-only migration only if canonical serialization, narrow deterministic string rules, guarded same-process and durable replay behavior, Inspector rehydration and legacy compatibility are all proven. Otherwise document the narrow blocker and leave runtime behavior unchanged.
## Recorded outcome

E180 completed with zero migration: the active-scene entity Inspector has no editable name field, and `.pond` exposes no existing narrow name-string contract. Do not reopen it by routing a hypothetical control through `entity.set_property`; start a feature-design gate only if product requirements explicitly introduce an editable display-name surface.