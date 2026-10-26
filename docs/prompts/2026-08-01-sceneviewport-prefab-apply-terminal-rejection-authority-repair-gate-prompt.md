# E186 Fresh-Session Completion Prompt -- SceneViewport Prefab-Apply Terminal-Rejection Authority Repair Gate

E186 is complete. The SceneViewport `.pond` prefab Apply branch now delegates to `_apply_scene_prefab_placement()`. That adapter calls `prefab.place`; a rejected command returns terminally without a legacy `create_entity` EventBus publish, local fallback, success effects, or `scene.open` rehydrate. A successful command rehydrates once from canonical `.pond`.

Evidence: the focused offscreen SceneViewport/audit suite passed `16 passed in 1.24s`; compilation plus audit-status, core-boundary, and GUI-boundary checks passed. Audit is still schema v4 with `unified_undo_redo_runtime=false`. Do not claim global unified undo/redo, full-suite pytest, native acceleration completion, or OpenGL default readiness.

The next and only gate is E187: design a deterministic guarded-history contract for `prefab.place`. Start by establishing whether the current command can capture exact placed entity payload/index, ordered pre/post entities and connections, and a source-independent redo recipe. Do not reread a mutable prefab source for redo, do not broaden generic setters, and preserve E175/E177 fallback behavior.
