# E192 Project Evolution Defaults Deterministic Guarded-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E191 completed exact guarded history for `project.set_ps_experiment_preset`, establishing the narrow project-manifest witness pattern without a generic manifest setter.

## Inventory result

- `project.set_evolution_defaults` resolves only the project contract, requires a mapping payload, and replaces exactly `project.json["evolution_defaults"]`. It does not read an external source or invoke a host adapter.
- The PS experiment panel derives defaults from its current form, calls the Registry, and updates only its status label after success/failure. Project-open service paths may later load the saved defaults, but the save command itself has no runtime configuration mutation.
- The direct field may have been absent or hold legacy JSON that is not a mapping. Prior state is therefore captured as an exact JSON-safe value plus a presence bit. New nested mappings/lists/scalars are detached through JSON-safe serialization before they become the field snapshot or replay payload.
- Complete canonical `project.json` witnesses prevent undo/redo from silently overwriting independent project edits. A narrow inverse remains sufficient because it changes only this one field.

## Implemented contract

- `project.set_evolution_defaults` is now `undoable=True`; its optional `expected_project` guard preserves direct-call compatibility while allowing replay to reject stale manifests before writing.
- Added the internal non-undoable inverse `project.restore_evolution_defaults_snapshot`. It requires the complete post-execute manifest, restores the exact former value or field absence, and returns its full post-undo manifest for redo guarding.
- The Registry builds an owned evolution-defaults record, attaches the inverse post-state to redo in memory and from durable audit replay, and includes the direct command in the replay selector and audit-status representative inventory.
- The E190 inventory remains exactly 31 non-undoable commands: direct evolution-defaults mutation leaves the deferred set and its internal inverse enters the explicit history-control category.

## Proof

- Added `tests/test_ai_command_project_evolution_defaults_guarded_history.py`, proving detached nested defaults snapshots, absent-field restoration, fresh-registry durable undo/redo, stale undo/redo rejection before write/audit, retry after canonical restoration, exact restore of a legacy non-mapping value, and direct compatibility without `expected_project`.
- Focused cross-history suite passed: `56 passed, 10 subtests passed in 4.20s`.
- `py_compile` passed for changed production/test/audit files. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. Audit remains schema version 4 with `unified_undo_redo_runtime=false`.
- Repository-wide pytest was intentionally not run.

## Non-goals retained

- No generic project-manifest setter, `project.set_active_scene` migration, scene-save migration, project lifecycle inverse, global unified undo/redo, native acceleration completion, or OpenGL-default claim was introduced.

## Next gate

Exactly one next gate: **E193 -- Project Active Scene Guarded-History and Host-Side-Effect Feasibility Audit**.