# E197 Fresh-Session Handoff -- Scene Save Authority Decomposition and Terminal-Rejection Repair Gate

E197 is complete. `scene.save` now receives an explicit project-local target and snapshot, validates/persists through Qt-free `scene_persistence`, and has terminal rejection before host/audit effects. SceneManager and Standard UI only commit host state after canonical persistence success; project-world flush calls the same primitive through SceneManager.

Do not call this undo-ready by itself. E198 must add exact snapshot guarded history and fresh-registry replay proof, while preserving schema v4 and `unified_undo_redo_runtime=false`.
