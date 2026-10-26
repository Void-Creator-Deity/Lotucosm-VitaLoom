# E182 Scene Entity Delete-Restore Guarded-History Contract Design Gate

Date: 2026-08-01
Status: complete

## Previous gate

E181 guarded `entity.create -> undo entity.delete -> redo entity.create`, but the reverse `entity.delete -> entity.restore_deleted_snapshot -> redo entity.delete` route still had no full expected-current witness.

## Decision and implemented contract

E182 demonstrated a complete expected-current witness without changing `.pond` ownership or ordering, then implemented the route.

- `entity.delete` now records exact post-delete ordered entity and connection lists as `history_restore_expected_entities` and `history_restore_expected_connections`.
- Registry passes those values to `entity.restore_deleted_snapshot` as optional `expected_entities` and `expected_connections` witnesses. Restore compares the complete canonical lists before any duplicate-ID, endpoint, index, mutation, or `_write_json()` path; divergence rejects as `stale_entity_restore_deleted_snapshot`.
- A successful restore records its exact full post-restore lists as the paired `entity.delete` redo witness. Registry attaches them in both same-process history and fresh-Registry durable replay.
- `entity.delete` now accepts optional full-scene witnesses in addition to E181's target snapshot/index/incident-connection witnesses. Redo therefore rejects survivor edits/reorders, connection changes/reorders, endpoint removal, and any target divergence as `stale_entity_delete` before write.
- Direct legacy delete/restore calls remain compatible because all full-scene witness inputs are optional. Existing restore validation for snapshot ID, entity slot, connection index uniqueness/range, and endpoint availability remains active once a witness matches.

## Required evidence and result

1. **Post-delete restore guard — passed.** Same-ID recreation, survivor edit, connection reorder, and endpoint removal all reject before write.
2. **Post-restore redo guard — passed.** Survivor edit, connection reorder, and endpoint removal all reject before write; restoring the exact canonical witness permits retry.
3. **Fresh durable replay — passed.** Durable undo rejects same-ID recreation without a durable-undo audit. Rejected durable redo retains replay eligibility and succeeds after the canonical scene is restored.
4. **Authority and compatibility — preserved.** Scene-owned semantic failure remains terminal with no local `CommandStack` fallback, legacy sync, success effect, or scene rehydrate. E175/E177 non-scene and ownerless fallback remains unchanged.
5. **Status — preserved.** Audit stays schema v4 with `unified_undo_redo_runtime=false`; no Inspector domain expansion, manifest, WorldBridge, native acceleration, or OpenGL-default claim was made.

## Verification proof

Focused lifecycle suite:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_ai_command_undo_redo_bridge.py `
  tests\test_ai_command_durable_project_undo.py
# 21 passed, 10 subtests passed in 2.13s
```

Expanded E180-E182 scoped suite:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_inspector_property_mapping.py `
  tests\test_scene_viewport_semantic_node_history.py `
  tests\test_scene_viewport_semantic_connection_history.py `
  tests\test_ai_command_durable_project_undo.py `
  tests\test_ai_command_audit_status_tool.py `
  tests\test_ai_command_undo_redo_command_path.py `
  tests\test_ai_command_undo_redo_bridge.py `
  tests\test_ai_command_audit_history.py
# 55 passed, 16 subtests passed in 5.45s
```

`py_compile` for runtime, Registry, and lifecycle tests passed. `check_ai_command_audit_status.py`, `check_core_boundaries.py`, and `check_gui_boundaries.py` passed. Repository-wide pytest was intentionally not run.

## Non-goals retained

- Do not widen `entity.set_property`, `script.set_property`, or generic snapshot authority.
- Do not alter Inspector field inventory, local non-scene fallback, `.pond` schema, manifests, WorldBridge, native acceleration, or OpenGL default readiness.
- Do not claim unified engine undo/redo; `unified_undo_redo_runtime=false` remains authoritative.

## Completion and next gate

The full `entity.delete -> undo entity.restore_deleted_snapshot -> redo entity.delete` inverse is stale-safe for same-process and fresh-Registry durable replay. Both entity lifecycle directions are guarded, but broad generic entity-property history remains unguarded.

Exactly one next gate: **E183 -- Scene Entity Generic-Property Guarded-History Contract Decision Gate**.