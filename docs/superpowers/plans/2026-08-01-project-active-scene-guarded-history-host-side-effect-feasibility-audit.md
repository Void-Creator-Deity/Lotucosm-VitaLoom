# E193 Project Active Scene Guarded-History and Host-Side-Effect Feasibility Audit

Date: 2026-08-01
Status: complete (blocked for history migration)

## Previous gate

E192 completed guarded durable history for `project.set_evolution_defaults`. The next remaining persistent candidate was `project.set_active_scene`.

## Audit result

`project.set_active_scene` is **not currently safe to migrate as a deterministic guarded-history operation**. Its canonical field write and host scene-loading behavior have two competing authorities:

1. The command validates the requested `.pond`, writes `project.json["active_scene"]`, then, when `context["load_scene"]` is true, calls `SceneManager.load_scene()`.
2. `SceneManager.load_scene()` mutates editor context/current scene, emits scene-loaded signals/events, and independently rewrites `project.json["active_scene"]` for `editor_context.current_project_path`.
3. If the load returns `False` or raises, the command currently leaves the manifest write in place and returns a successful envelope with `scene_loaded=False`. The command therefore cannot provide a terminal rejection or a single canonical before/after witness for host-coupled replay.
4. `LibraryBrowser` is the direct UI caller and explicitly passes `context={"load_scene": True}`. The non-host direct command path remains covered by `test_project_set_active_scene_updates_project_contract`, which deliberately observes `scene_loaded=False` without that context.

This violates the precondition for safe history migration: no inverse can reliably distinguish canonical project state from host state, and an undo/redo load could write the wrong current editor project or emit success effects around a failed operation.

## Blocker, fallback, and unblock path

- **Blocker:** `project.set_active_scene` combines canonical manifest mutation with a legacy `SceneManager` host action that has its own manifest writer and emits runtime/UI side effects.
- **Fallback retained:** keep the command non-undoable and do not add it to the durable replay selector. Existing direct/LibraryBrowser behavior remains unchanged in this audit gate.
- **Unblock path:** first make the command canonical-only, remove the `load_scene` context authority from it, and move any UI rehydration into an explicit, success-gated `scene.open` step whose failure remains terminal and cannot create local fallback/EventBus mutation/success effects. Only then can a later gate evaluate guarded history from one manifest authority.

## Evidence

- Source trace: `runtime_commands._project_set_active_scene`, `docks/library_browser.py`, and `scene/scene_manager.py::SceneManager.load_scene` establish the write-before-load, second independent writer, current-context mutation, and event emission sequence.
- Existing direct command regression confirms the canonical no-context route and `.pond` boundary behavior; the E192 focused representative suite remains green at `56 passed, 10 subtests passed in 4.20s`.
- No production code was changed in E193; repository-wide pytest was intentionally not run. Audit schema remains v4 with `unified_undo_redo_runtime=false`.

## Next gate

Exactly one next gate: **E194 -- Project Active Scene Canonical-Only and Terminal-Rejection Authority Repair Gate**.