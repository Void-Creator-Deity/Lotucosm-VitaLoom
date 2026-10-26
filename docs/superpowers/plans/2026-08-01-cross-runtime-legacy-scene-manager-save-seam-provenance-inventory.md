# E203 Cross-Runtime Legacy SceneManager Save-Seam Provenance Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E201 inventoried direct callers inside the VitaLoom version runtime; E202 made its latent `save_scene_as()` helper failure-atomic and kept it outside semantic history/audit. Both `save_scene()` and `save_scene_as()` remain public legacy adapter seams that another active package, host integration, or extension could reference without appearing in the inner-runtime AST inventory.

## Active scope and decision

The active non-test cross-runtime scope is deliberately limited to the 16 Python files under `FrameCore` outside `versions/1.0.0/runtime`, 27 tool Python files, and the two root launchers (`main.py`, `player.py`). Historical backups, temporary recovery scripts, workspace project data, documentation, and tests are excluded from runtime-caller claims.

AST inspection found **no active cross-runtime reference** to either legacy save seam: no `save_scene` / `save_scene_as` attribute access, no `getattr(..., "save_scene")`, no SceneManager module import, and no `import_module(...scene_manager)` use. The sole textual `.save_scene(` match outside the runtime is the intentional forbidden-snippet rule in `tools/check_project_plugin_model.py`; it is a guard declaration, not an invocation.

Therefore no additional persistence, host synchronization, history, or audit behavior was introduced. The established decisions remain in force: Standard UI explicit save is Registry `scene.save`; Project-World flush is lifecycle persistence excluded from history/audit; the latent Save As helper is failure-atomic but not user semantic.

## Contract implemented

`tests/test_cross_runtime_scene_manager_save_seam_inventory.py` AST-scans the declared active scope and fails on direct, aliased attribute, reflective `getattr`, static import, or `import_module` reference to the legacy save seams. Its scope test makes the excluded runtime/tests boundary explicit, so a future cross-boundary use needs a classification change rather than silently bypassing the inventory.

## Evidence

- Focused E203 inventory/regression set passed: `7 passed in 11.85s`.
- Wider relevant persistence/history/UI suite passed: `129 passed, 10 subtests passed in 22.62s`.
- `py_compile` passed for the new static regression. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. Diff output contained only existing LF/CRLF warnings.
- Repository-wide pytest was intentionally deferred to E204's whole-refactor evidence refresh. Schema version `4` and `unified_undo_redo_runtime=false` remain unchanged; this gate does not claim global unified undo/redo, native acceleration completion, or OpenGL default readiness.

## Next gate

E204 must refresh the whole-refactor completion evidence against the current worktree: run the broadest feasible suite and active architecture guards, reconcile the results with the E166 completion matrix, and identify exactly one material remaining architecture gap. Do not equate passing focused persistence gates with whole-refactor completion.
