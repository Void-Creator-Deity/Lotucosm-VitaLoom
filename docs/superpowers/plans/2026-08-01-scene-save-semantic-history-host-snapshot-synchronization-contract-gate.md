# E199 Scene Save Semantic-History Host Snapshot Synchronization Contract Gate

Date: 2026-08-01
Status: complete

## Previous gate

E198 made `scene.save` a guarded memory/durable history command while deliberately setting `history_rehydrate_scene=false`: scene history may not call `scene.open`, because `SceneManager.load_scene()` can write project `active_scene` and would regain persistence authority.

## Objective

Provide a UI-host adapter mirror for successful scene-save history results without writing the `.pond`, loading a scene, or mutating `project.json`.

## Contract implemented

1. Scene-save execute and internal restore results now carry `history_sync_host_scene=true` together with the exact canonical `scene_path`, `scene_data`, and `history_rehydrate_scene=false`.
2. New Qt-free UI helper `core.VitaLoom.ui.semantic_history.mirror_scene_save_history_snapshot()` accepts only that narrow result contract. It JSON-detaches the returned snapshot and calls the existing host-only `SceneManager.commit_persisted_scene()` seam.
3. Core command actions and Standard UI invoke the helper only after successful Registry undo/redo. It never calls `scene.open`; default rehydrate behavior for other semantic history results remains unchanged.
4. Stale Registry rejection never reaches the helper. A host mirror exception is contained as a post-canonical adapter failure and never becomes a `scene.open` fallback, disk rewrite, or manifest mutation.

## Evidence

- `tests/test_scene_save_guarded_history.py` now asserts the exact history marker on execute, undo, and redo results.
- `tests/test_ui_command_actions.py` covers shortcut/menu behavior, success-only detached mirror, stale rejection, and contained host-mirror failure.
- `tests/test_standard_ui_semantic_history_rehydrate_contract.py` proves Standard UI mirrors snapshots without calling `scene.open`.
- Wider relevant regression set: `121 passed, 10 subtests passed in 6.10s`.
- `tools/check_ai_command_audit_status.py` passed with schema version `4`, representative `scene.save`, and `unified_undo_redo_runtime=false`.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. The diff check printed only pre-existing CRLF/LF warnings.
- Repository-wide pytest was intentionally not run.

## Next gate

E200 must audit the remaining automatic project-world flush route. It still enters legacy `SceneManager.save_scene()` rather than the user-facing semantic command path, so its history/audit admission must be explicitly accepted or bounded instead of inferred from E197's shared write primitive.
