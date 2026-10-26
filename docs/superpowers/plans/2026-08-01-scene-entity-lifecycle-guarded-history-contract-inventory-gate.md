# E181 Scene Entity Lifecycle Guarded-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E180 completed with zero migration. The active-scene entity Inspector has no editable `name` control and `.pond` has no pre-existing narrow name-string contract, so a name command would be speculative API expansion.

## Objective

Audit the existing scene entity lifecycle commands (`entity.create`, `entity.delete`, `entity.restore_deleted_snapshot`, and related Registry inverse recipes) for a safe, narrow guarded-history improvement. Determine whether their stable identity, ordered scene ownership, snapshot preconditions and fresh-registry durable replay can be made stale-safe without changing `.pond` semantics or widening generic property authority.

## Decision and implemented contract

E181 completed one deliberately narrow migration: the inverse pair for `entity.create` is now guarded.

- `entity.create` accepts optional `expected_entities` and `expected_connections` witnesses. Before a guarded redo writes, it compares the complete canonical ordered lists and rejects divergence as `stale_entity_create_scene`.
- `entity.delete` accepts optional `expected_entity`, `expected_entity_index`, and `expected_incident_connections` witnesses. Before a guarded create-undo writes, it validates the full entity JSON snapshot, its ordered entity-list slot, and indexed incident connection rows. A mismatch rejects as `stale_entity_delete`; malformed optional witnesses reject explicitly.
- The `entity.create` Registry inverse now supplies those delete witnesses. On a successful guarded delete, the command records the actual post-undo canonical entities/connections as redo witnesses. Registry attaches those witnesses to the same operation for both in-memory `undo_last()` and fresh-Registry `redo_project()` replay.
- Direct legacy `entity.create` and `entity.delete` calls remain compatible because all new witness fields are optional. Entity and connection ordering and `.pond` data ownership remain unchanged.

This is not a general lifecycle completion. `entity.delete -> entity.restore_deleted_snapshot` is still not stale-safe: its restoration inverse has no expected-current full-scene witness and must not be described as guarded.

## Required evidence and result

1. **Canonical ownership and order — passed.** The guarded delete compares the canonical entity snapshot and exact entity index, and captures incident connections with their ordered list indices before removal.
2. **Stable identity and stale mutation — passed for the create inverse.** External entity JSON mutation, entity reordering, and newly incident connections each reject before `_write_json()`.
3. **Redo current-state guard — passed.** The successful delete's observed post-undo entities/connections become the exact redo precondition; external list changes cause redo rejection before write.
4. **Fresh-Registry durable replay — passed.** Durable undo restores the redo witness from the undo audit result. A rejected durable redo does not consume the replay selection, so restoring canonical state permits retry.
5. **UI/history authority — preserved.** This change is command/Registry scoped; it preserves the existing rule that scene-owned semantic failures are terminal and do not fall back to local history.
6. **Compatibility and audit status — passed.** Schema remains v4 and `unified_undo_redo_runtime=false`; no generic-property, Inspector, manifest, WorldBridge, native, or OpenGL authority change was made.

## Verification proof

Focused lifecycle suite:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_ai_command_undo_redo_bridge.py `
  tests\test_ai_command_durable_project_undo.py
# 17 passed, 3 subtests passed in 1.67s
```

Expanded E180/E181 scoped suite:

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
# 51 passed, 9 subtests passed in 3.54s
```

`py_compile` for Inspector/binding/runtime command/Registry modules and `check_ai_command_audit_status.py`, `check_core_boundaries.py`, and `check_gui_boundaries.py` also passed. Repository-wide pytest was intentionally not run; this evidence does not claim a full-suite result.

## Non-goals retained

- Do not alter `entity.set_property`, `script.set_property`, display-name UI, or non-scene local fallback.
- Do not claim a whole-engine unified undo/redo implementation.
- Do not change WorldBridge, native acceleration, OpenGL default, package/project manifests, or the Qt-free L0-L4 boundary.

## Completion and next gate

The `entity.create -> undo entity.delete -> redo entity.create` contract is guarded for same-process and fresh-Registry durable replay. The remaining `entity.delete -> entity.restore_deleted_snapshot -> redo entity.delete` inverse is intentionally outside this migration.

Exactly one next gate: **E182 -- Scene Entity Delete-Restore Guarded-History Contract Design Gate**.