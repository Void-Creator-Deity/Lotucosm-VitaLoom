# E196 Scene Save Canonical-State Guarded-History Feasibility Audit

Date: 2026-08-01
Status: complete -- blocked for history migration

## Previous gate

E195 completed manifest-only guarded history for `project.set_active_scene` and introduced the explicit history UI rehydrate opt-out contract.

## Audit result

`scene.save` is not history-ready and was deliberately left non-undoable.

1. Its public Registry input accepts only optional `data`; it has no canonical `scene_path`, project path, expected scene snapshot, or expected project witness. The Registry audit root is derived from the **payload**, so the current save result's scene path is too late for a durable audit entry.
2. `_scene_save()` calls the singleton legacy `SceneManager.save_scene()`. When `data` is supplied, that method mutates `_current_scene_data` and `editor_context.current_scene` before it validates/writes the current scene path. It then writes the `.pond`, clears the dirty flag, emits Qt/signal-bus success effects, and only returns a boolean. That prevents a failed path from being terminal and leaves no exact pre-write scene witness for an inverse.
3. Standard UI sends viewport data through `scene.save`, but project-world flush/switch flows call `SceneManager.save_scene()` directly. Thus changing only the Registry command would leave a parallel authority path and cannot establish representative command history truth.
4. `SceneManager.load_scene()` independently updates the current project manifest's `active_scene`, so any eventual undo/redo rehydrate must remain explicitly separated from scene serialization authority as in E195.

## Decision

No history metadata, inverse command, durable replay entry, or audit-schema change was added. The current non-undoable classification is retained.

## Fallback and unblock path

- **Fallback now:** retain `scene.save` as a legacy host-bound persistence boundary; do not advertise it as durable or reversible.
- **Unblock:** E197 must first decompose scene-save preparation from persistence: obtain an explicit project-local scene target plus detached canonical snapshot, perform stale checks before editor-context/disk/signal mutation, return an inspectable persistence result, and route project-world flush through the same authority or prove its equivalent contract. Only after that repair may a later gate design a guarded inverse.

## Proof

- Source/caller dataflow audit across `runtime_commands.py`, `registry.py`, `scene_manager.py`, `standard_ui_plugin.py`, and `project_manager.py` found the four authority conflicts above.
- Existing focused save/session inventory: `34 passed in 1.10s` across project-world session transition, Standard UI contribution lifecycle, and non-undoable classification.
- Audit/core/GUI checks passed, preserving audit schema v4 and `unified_undo_redo_runtime=false`.

## Exactly one next gate

**E197 -- Scene Save Authority Decomposition and Terminal-Rejection Repair Gate.**
