# E194 Project Active Scene Canonical-Only and Terminal-Rejection Authority Repair Gate

Date: 2026-08-01
Status: complete

## Previous gate

E193 proved that `project.set_active_scene` was not history-ready because one handler combined manifest mutation with optional SceneManager loading.

## Delivered contract

- `project.set_active_scene` validates a project-local `.pond` and writes only the selected project manifest `active_scene`.
- Legacy `context["load_scene"]` is ignored. The compatibility result retains `scene_loaded: false`; the command neither imports nor calls SceneManager.
- `ProjectPanel._set_active_scene()` explicitly calls `scene.open` only after canonical success. A failed open is logged, not misreported as loaded and never replaced by fallback mutation.
- Tests prove canonical success has no SceneManager, editor-context, EventBus, or CommandStack effect. Rejected outside-project input has no write, audit, host/context/fallback, success-event, or rehydration effect.
- No undo metadata, inverse, durable replay selector, audit schema, or fallback contract changed. `project.set_active_scene` remains non-undoable.

## Evidence

- Changed-file compilation passed.
- Focused command/UI/boundary suite: `20 passed in 1.69s`.
- Wider representative history suite: `60 passed, 10 subtests passed in 4.54s`.
- Audit/core/GUI checks passed; audit stays `schema_version: 4` with `unified_undo_redo_runtime: false`.
- Repository-wide pytest, native acceleration, and OpenGL default readiness were not claimed.

## Next gate

E195 must re-evaluate guarded history separately, including isolation from generic undo/redo UI rehydration and independent `scene.open` host effects.
