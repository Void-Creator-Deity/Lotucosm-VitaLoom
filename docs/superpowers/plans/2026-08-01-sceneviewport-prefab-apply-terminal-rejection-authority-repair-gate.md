# E186 SceneViewport Prefab-Apply Terminal-Rejection Authority Repair Gate

Date: 2026-08-01
Status: complete

## Previous gate

E185 established that a real `.pond` prefab-apply SceneViewport command calls `prefab.place`, but its failure branch published legacy `create_entity`. This violated terminal scene-owned semantic rejection and blocked guarded placement history.

## Completed repair

- Removed the `.pond` prefab Apply failure fallback that published the legacy `create_entity` EventBus event.
- Extracted `_apply_scene_prefab_placement()` as the narrow UI-host adapter seam. It calls `prefab.place`, returns immediately on rejection, and runs canonical `scene.open` rehydration only after command success.
- Kept the Open branch, non-prefab asset-drop behavior, E175/E177 non-scene/ownerless fallback, `.pond` semantics, package/project manifests, command-audit schema, and the existing Qt-free command authority unchanged.

## Proof

- Focused tests cover rejected and successful prefab placement without constructing a native `QDropEvent`: rejection invokes `prefab.place` once but produces no legacy create event, no rehydrate, no local scene mutation, and no project-modified or command-executed success effects; success invokes the same command path and rehydrates exactly once.
- Focused offscreen suite: `16 passed in 1.24s` for `test_scene_viewport_semantic_event_node_history.py`, `test_scene_viewport_command_bridge.py`, `test_scene_viewport_semantic_node_history.py`, and `test_ai_command_audit_status_tool.py`.
- `py_compile` passed for the changed production and test modules. `check_ai_command_audit_status.py`, `check_core_boundaries.py`, and `check_gui_boundaries.py` all passed. Audit remains schema version 4 with `unified_undo_redo_runtime=false`.
- The previous direct native `QDropEvent` test approach was removed because it triggered a Windows Qt access violation under offscreen execution. The replacement tests the extracted production command seam deterministically; it is not a claim of whole drop-widget native-event coverage.

## Non-goals retained

- This gate does not add durable prefab undo/redo.
- It does not repair the unrelated `asset.apply_to_scene` fallback.
- It does not change generic/script setters, prefab serialization, native acceleration, OpenGL readiness, or the global undo/redo status.

## Next gate

Exactly one next gate: **E187 -- Scene Prefab Placement Deterministic Guarded-History Contract Design Gate**.
