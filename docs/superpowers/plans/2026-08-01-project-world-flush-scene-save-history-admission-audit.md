# E200 Project-World Flush Scene Save History Admission Audit

Date: 2026-08-01
Status: complete

## Previous gate

E197 unified the bytes-on-disk primitive used by the command and legacy SceneManager. E198/E199 then added guarded user-facing command history plus UI-host snapshot parity. Project-world session transitions still invoke `SceneManager.save_scene()` for automatic dirty-scene flushing.

## Decision

Automatic Project-World scene flush is **lifecycle persistence**, not a user semantic command. It remains excluded from both user-visible undo/redo history and command audit.

This boundary is intentional because a flush may occur while switching or closing worlds, couples scene persistence to the subsequent `project.json` active-scene commit, and has no independent exact pre/post user-command witness. Routing it through `scene.save` would add surprising undo records, mix host commit/signal paths, and risk duplicated effects without providing a safe replay contract.

## Contract implemented

1. `project_world_session.AUTOMATIC_SCENE_FLUSH_HISTORY_BOUNDARY` explicitly declares:
   - `kind=automatic_lifecycle_flush`;
   - `history_admission=excluded`;
   - `audit_admission=excluded`.
2. `prepare_project_world_flush()` places a detached copy of that classification in `scene_persistence_boundary`; `ProjectManager.apply_project_world_flush()` preserves a detached boundary in its final report.
3. The stale-world no-op path in `_flush_before_project_switch()` reports the same boundary, so all automatic-flush outcomes have unambiguous admission provenance.
4. The persistence sequence is unchanged: validate project/scene context, persist through the legacy Host adapter backed by the E197 Qt-free primitive, then atomically persist the manifest. A scene-save failure remains fail-closed before manifest replacement.

## Evidence

- `tests/test_project_world_session_transition.py` now proves both Qt-free preparation classification and a real Host automatic dirty-scene flush: the `.pond` is persisted, the report explicitly excludes history/audit, no project `command_audit.jsonl` is created, and `command.undo` remains `undo_empty`.
- Focused regression set passed: `50 passed in 2.50s`.
- Wider relevant history/persistence/UI suite passed: `122 passed, 10 subtests passed in 7.29s`.
- `tools/check_ai_command_audit_status.py` passed with schema version `4`, representative durable scene-save history, and `unified_undo_redo_runtime=false`.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. The diff check emitted only existing LF/CRLF warnings.
- Repository-wide pytest was intentionally not run. This gate does not claim global unified undo/redo, native acceleration readiness, or OpenGL default readiness.

## Next gate

E201 must inventory every remaining direct legacy `SceneManager.save_scene()` caller outside the Standard UI Registry route and the now-classified Project-World lifecycle route. Each caller needs an explicit provenance/admission decision before any further history expansion.