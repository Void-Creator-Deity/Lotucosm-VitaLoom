# E187 Scene Prefab Placement Deterministic Guarded-History Contract Design Gate

Date: 2026-08-01
Status: complete

## Previous gate

E186 repaired SceneViewport `.pond` prefab Apply authority: failed `prefab.place` is terminal and success rehydrates once. `prefab.place` still had metadata-only undoability with no inverse recipe or stale-state protection.

## Contract implemented

- `prefab.place` now captures the exact serialized expanded entity, its appended entity-list index, and the ordered post-place entities/connections lists in its command result and durable execute audit. The handler still only appends one entity; it does not alter connections or components.
- Registry builds a `prefab.place` history operation whose undo is guarded `entity.delete` with the exact entity, index, empty incident-connection proof, and ordered post-place entity/connection witnesses. Divergence is rejected before `_write_json()`.
- Redo is a guarded `entity.create` using the captured entity and index, never `prefab_path`. The new `preserve_entity_snapshot=True` option makes that replay insert the already-serialized entity exactly, without interactive entity-create defaults that could otherwise alter a sparse prefab snapshot. Direct ordinary `entity.create` behavior is unchanged.
- Successful guarded undo observes the canonical post-delete scene and attaches it as the redo witness for both in-memory and fresh-registry durable replay. `prefab.place` is included in the representative durable-project replay selection and audit status inventory.

## Proof

- New `tests/test_ai_command_prefab_guarded_history.py` proves in-memory and fresh-registry durable undo/redo preserve the exact placed snapshot after the prefab is replaced with invalid JSON; therefore redo does not reread the source.
- The same suite proves durable undo rejects a mutated placed entity, durable redo rejects an independently appended entity after undo, both failures make zero `_write_json()` calls and append no failed replay audit; redo succeeds after canonical state is restored.
- Focused offscreen suite passed `38 passed, 10 subtests passed in 3.02s`: prefab guarded-history, registry undo/redo bridge, durable project undo, audit-status, and isomorphic scene-command tests. `py_compile`, audit-status, core-boundary, and GUI-boundary checks passed.
- Audit remains schema version 4 with `unified_undo_redo_runtime=false`. This is a representative command migration, not global unified history completion. Repository-wide pytest was intentionally not run.

## Compatibility and scope

- Existing direct `prefab.place` execute behavior remains source-based and appends one prefab entity. The exact snapshot path is history-only.
- `.pond`, Inspector/AI registry flows, SR2D public seams, package/project manifests, E175/E177 fallback behavior, native acceleration status, and OpenGL readiness are unchanged.
- Generic entity/script setter migration and the unrelated asset-drop fallback remain out of scope.

## Next gate

Exactly one next gate: **E188 -- SceneViewport Asset-Apply Terminal-Rejection Authority Repair Gate**.
