# E185 Fresh-Session Prompt — Scene Prefab Placement Durable-History Contract Inventory Gate

E185 is complete with no history migration. `prefab.place` is an active SceneViewport command, but it has no Registry inverse and its `.pond` “Apply prefab” failure branch still publishes the legacy `create_entity` event.

## Recorded outcome

- Successful SceneViewport prefab application uses `prefab.place` and rehydrates canonical scene state.
- Rejection currently falls back to a legacy EventBus mutation path, so it is not terminal.
- The command records no placed entity snapshot/index/scene witnesses or prefab source snapshot/digest, and Registry has no inverse recipe. Replaying it would reread a potentially changed prefab source.

## Next work boundary

Proceed only with E186: repair terminal rejection for the SceneViewport `.pond` prefab-apply failure branch and prove the rejection makes no fallback mutation, success side effect, or rehydrate. Do not attempt prefab durable undo/redo in that gate.

Keep generic entity/script compatibility unchanged, do not touch `CONTEXT.md` or unrelated dirty work, and keep audit schema v4 with `unified_undo_redo_runtime=false`.