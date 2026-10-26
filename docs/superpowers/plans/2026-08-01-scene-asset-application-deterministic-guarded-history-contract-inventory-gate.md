# E189 Scene Asset Application Deterministic Guarded-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E188 repaired the SceneViewport current-scene asset Apply authority boundary. Failure is terminal, but `asset.apply_to_scene` was still metadata-undoable only and had no deterministic inverse or stale-state protection.

## Inventory result

- `_asset_apply_to_scene()` resolves the `.pond` and containing project, validates only that `asset_path` identifies an existing project file, and never reads the asset bytes, metadata, or file format.
- It constructs exactly one entity from payload/default values: `id`, `name`, `type`, `position`, `radius`, project-relative `asset_path`, matching `sr_visual.asset_path` / `sr_visual.sprite_path`, and empty `scripts`.
- The entity is always appended to `entities`; its exact slot is therefore the pre-append entity-list length. The handler only updates scene modified metadata and writes the scene. It does not mutate `connections`, `components`, or any other `.pond` collection.
- This is a narrow, safe reuse of the existing guarded `entity.delete` / `entity.create` contracts: the execute result can capture the exact serialized entity, append index, and complete post-apply entity/connection witnesses without changing direct asset-apply compatibility.

## Completed migration

- `asset.apply_to_scene` now returns `entity`, `entity_index`, `history_undo_expected_entities`, and `history_undo_expected_connections` alongside its established result fields and event.
- `CommandRegistry._build_undo_record()` gives asset application the same source-independent guarded recipe as prefab placement: undo is guarded `entity.delete`; redo is `entity.create` with the captured serialized entity, original index, and `preserve_entity_snapshot=True`.
- Successful undo captures the canonical post-delete witness for redo; both in-memory and fresh-registry durable replay reject stale entity or connection state before `_write_json()` and do not append rejected replay audit entries.
- `asset.apply_to_scene` is now eligible for latest durable-project replay and is included in the representative audit-status inventory. Audit schema remains version 4 and `unified_undo_redo_runtime=false`.

## Proof

- New `tests/test_ai_command_asset_apply_guarded_history.py` proves exact in-memory and durable replay after the original asset is deleted; the redo never resolves or rereads that source.
- It also proves stale undo rejection after an applied-entity mutation, stale redo rejection for independently changed entity and connection lists, zero `_write_json()` calls on every rejection, no rejected durable replay audit, and successful retry after canonical restoration.
- Focused command-history suite passed `43 passed, 10 subtests passed in 3.91s`.
- `py_compile`, `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. The audit checker reports `schema_version: 4` and `unified_undo_redo_runtime: false`. Repository-wide pytest was intentionally not run.

## Non-goals retained

- This does not claim global unified undo/redo, migrate unrelated non-undoable mutations, change direct asset-apply source validation, or alter E175/E177 fallback behavior.
- It does not change generic/script setters, prefab history, native acceleration, or OpenGL readiness.

## Next gate

Exactly one next gate: **E190 -- Mutating Command Undoability Classification Inventory Gate**.
