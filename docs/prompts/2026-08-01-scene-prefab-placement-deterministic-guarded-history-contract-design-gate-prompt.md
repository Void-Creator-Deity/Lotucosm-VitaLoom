# E187 Fresh-Session Completion Prompt -- Scene Prefab Placement Deterministic Guarded-History Contract Design Gate

E187 is complete. `prefab.place` durable history captures its exact expanded serialized entity, append index, and ordered post-place entities/connections witnesses. Undo is guarded `entity.delete`; redo is guarded `entity.create` with `preserve_entity_snapshot=True`, so it never rereads the mutable prefab path and does not apply interactive creation defaults. Both in-memory and fresh-registry durable replay reject stale state before writes.

Evidence: focused prefab/history/audit/isomorphic suite passed `38 passed, 10 subtests passed in 3.02s`; compile, audit-status, core-boundary, and GUI-boundary checks passed. Audit remains schema v4 with `unified_undo_redo_runtime=false`. No global unified-history, full-suite pytest, native acceleration, or OpenGL-default claim is valid.

The next and only gate is E188: repair the active SceneViewport `asset.apply_to_scene` failure fallback so a rejected scene-owned asset placement does not publish legacy `create_entity`, mutate locally, emit success effects, or rehydrate. Keep non-scene/ownerless E175/E177 compatibility behavior unchanged.
