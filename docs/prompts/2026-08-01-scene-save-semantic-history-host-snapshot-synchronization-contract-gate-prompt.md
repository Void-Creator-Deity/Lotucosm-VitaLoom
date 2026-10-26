# E199 Fresh-Session Prompt -- Scene Save Semantic-History Host Snapshot Synchronization Contract Gate

E199 is complete. `scene.save` and `scene.restore_snapshot` set `history_sync_host_scene=true` with `history_rehydrate_scene=false`. `core.VitaLoom.ui.semantic_history` mirrors only that successful canonical snapshot through `SceneManager.commit_persisted_scene`; command actions and Standard UI use it after Registry history success. The helper does not write disk, call `scene.open`, or mutate manifests, and a host adapter exception has no rehydrate fallback.

Evidence: relevant regression set `121 passed, 10 subtests passed in 6.10s`; audit schema remains v4 and `unified_undo_redo_runtime=false`.

The next gate is E200: audit the automatic project-world flush route through legacy `SceneManager.save_scene()` and explicitly decide its semantic history/audit admission boundary.
