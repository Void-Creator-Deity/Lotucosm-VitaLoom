# E201 Legacy SceneManager Save Provenance and History-Admission Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E200 classified automatic Project-World flush as non-history/non-audit lifecycle persistence and proved that it neither consumes Registry undo history nor creates project command-audit records. Standard UI explicit save already routes its canonical payload through Registry `scene.save`.

## Inventory decision

The runtime has exactly three direct attribute calls to legacy `SceneManager.save_scene()`:

| Caller | Provenance and ordering | Host effects | History / audit decision |
|---|---|---|---|
| `ProjectManager._persist_viewport_scene()` | Automatic Project-World flush when a legacy `SceneViewport` is present. It passes the visible viewport snapshot to the legacy adapter; `apply_project_world_flush()` does not commit `project.json` until this scene write succeeds. | The E197 shared `.pond` writer persists a detached snapshot; `commit_persisted_scene()` then mirrors it to the legacy host and emits its existing save/modified signals. | **Excluded.** E200 reports `automatic_lifecycle_flush`, `history_admission=excluded`, `audit_admission=excluded`. |
| `ProjectManager.apply_project_world_flush()` | Automatic Project-World flush fallback for a modified SceneManager when no SceneViewport is available. It validates the prepared project and active scene, saves the scene, and only then atomically replaces the manifest. | Same detached persistence and success-only legacy-host commit path. A failed save remains fail-closed before manifest replacement. | **Excluded.** Same E200 lifecycle boundary; it is not an independent user semantic command. |
| `SceneManager.save_scene_as()` | A latent legacy helper that saves its current in-memory scene to a target path. Runtime search found no caller of `save_scene_as()`; it has no typed command owner, canonical target ownership, pre/post witness, stale inverse, or audit provenance. | It delegates to `save_scene()` and has the legacy host-side synchronization behavior of that adapter. Its failure atomicity is the next focused concern. | **Excluded and quarantined.** Do not add Registry history or audit merely because it writes a `.pond`. |

`StandardUIPlugin.save_scene()` is not in this inventory: it dispatches the user-owned canonical `scene.save` Registry command and only mirrors the already-persisted result into the legacy host on success.

## Contract implemented

1. `tests/test_scene_manager_save_provenance_inventory.py` AST-scans every runtime Python file (UTF-8 BOM-safe) and pins the three direct `save_scene` callers including their class/method owners.
2. The same guard proves there are no runtime `save_scene_as()` callers, keeping the helper visibly latent instead of silently promoting it to a user route.
3. The guard also pins the E200 lifecycle exclusion markers and prohibits the Standard UI explicit-save body from directly calling `.save_scene(`.
4. No automatic or latent legacy route was routed into user undo/redo or command audit. Schema version `4` and `unified_undo_redo_runtime=false` remain unchanged.

## Evidence

- Focused E201 regression set passed: `51 passed in 4.12s`.
- Wider relevant persistence/history/UI set passed: `125 passed, 10 subtests passed in 9.01s`.
- `tools/check_ai_command_audit_status.py` passed with schema version `4` and `unified_undo_redo_runtime=false`.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. The diff check emitted only pre-existing LF/CRLF warnings.
- Repository-wide pytest was intentionally not run: this gate adds a narrow static inventory and documentation only. It does not claim global unified undo/redo, native acceleration readiness, or OpenGL default readiness.

## Next gate

E202 must harden the latent `SceneManager.save_scene_as()` helper's failure atomicity while retaining its public legacy seam and keeping it outside user history/audit. A later user-facing Save As migration requires a typed canonical command, target ownership, stale-safe witness/inverse, durable-audit policy, and explicit UI-host synchronization proof.
