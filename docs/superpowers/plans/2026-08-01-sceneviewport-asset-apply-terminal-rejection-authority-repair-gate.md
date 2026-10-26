# E188 SceneViewport Asset-Apply Terminal-Rejection Authority Repair Gate

Date: 2026-08-01
Status: complete

## Previous gate

E187 completed deterministic guarded history for `prefab.place`. The active SceneViewport ordinary asset-drop route still ran `asset.apply_to_scene` and published legacy `create_entity` when the current-scene command failed.

## Completed repair

- Removed the current-scene `asset.apply_to_scene` failure fallback that published EventBus `create_entity`.
- Extracted `_apply_scene_asset_placement()` as a focused UI-host seam. It invokes `asset.apply_to_scene`, returns terminally on failure, and rehydrates canonical `.pond` once only after success.
- Retained the Open/prefab branches, unrelated non-scene/ownerless E175/E177 fallback, `.pond`, manifests, command audit schema, Inspector/AI command flows, and SR2D public seams.

## Proof

- Focused regression coverage exercises the production helper without constructing a native `QDropEvent`: failure has no EventBus create event, local mutation, project-modified/command-executed success effects, or rehydrate; success makes one command call and one rehydrate.
- Focused offscreen suite passed `18 passed in 1.09s` for SceneViewport terminal-rejection, command bridge, semantic node history, and audit-status tests.
- `py_compile`, audit-status, core-boundary, and GUI-boundary checks passed. Audit remains schema version 4 with `unified_undo_redo_runtime=false`; no repository-wide pytest was run.

## Non-goals retained

- This authority-only repair does not add durable asset-placement history.
- It does not alter generic/script setters, prefab history, native acceleration, or OpenGL readiness.

## Next gate

Exactly one next gate: **E189 -- Scene Asset Application Deterministic Guarded-History Contract Inventory Gate**.
