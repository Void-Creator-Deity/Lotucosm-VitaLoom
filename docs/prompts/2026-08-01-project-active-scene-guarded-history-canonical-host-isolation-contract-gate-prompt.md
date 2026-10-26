# E195 Fresh-Session Handoff -- Project Active Scene Guarded-History Canonical/Host-Isolation Contract Gate

E195 is complete. `project.set_active_scene` has manifest-only guarded memory and durable history with `project.restore_active_scene_snapshot`; stale manifest witnesses reject before writes or replay audit entries. History results explicitly set `history_rehydrate_scene: false`, and both generic UI history adapters honor that opt-out. Direct ProjectPanel activation still owns its separate success-gated `scene.open`.

Keep audit schema v4 and `unified_undo_redo_runtime=false`. Do not turn the successful representative history proof into a claim of global undo/redo, nor migrate `scene.save` without a separate authority audit. Continue at E196.
