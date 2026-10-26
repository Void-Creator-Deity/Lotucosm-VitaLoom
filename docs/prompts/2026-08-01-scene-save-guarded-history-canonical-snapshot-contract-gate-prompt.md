# E198 Fresh-Session Prompt -- Scene Save Guarded-History Canonical Snapshot Contract Gate

E198 completed guarded history for canonical `scene.save`. It uses exact `.pond` pre/post snapshots, `scene.restore_snapshot` as a stale-guarded internal inverse, timestamp-stable redo, memory undo/redo, fresh-registry durable project undo/redo, and project-scoped audit replay. Both history results use `history_rehydrate_scene=false`; they must not invoke `scene.open`, SceneManager loading, or manifest writes.

Evidence: `tests/test_scene_save_guarded_history.py`; wider relevant set `117 passed, 10 subtests passed in 6.53s`; audit schema remains v4 and `unified_undo_redo_runtime=false`.

The next gate is E199: add/test an explicit UI-host canonical snapshot mirror for successful scene-save history only. Do not solve it with generic rehydrate or a host-owned disk mutation.
