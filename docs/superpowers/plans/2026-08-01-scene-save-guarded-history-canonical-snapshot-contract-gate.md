# E198 Scene Save Guarded-History Canonical Snapshot Contract Gate

Date: 2026-08-01
Status: complete

## Previous gate

E197 extracted an explicit, audited project-local scene persistence operation with detached pre/post snapshots and terminal rejection before host effects.

## Objective

Implement representative guarded memory/durable undo-redo for `scene.save` using exact `.pond` snapshots without reintroducing SceneManager or UI rehydrate authority.

## Contract implemented

1. `scene.save` is now undoable. Direct calls keep the legacy `modified_at` touch; history redo carries the already-canonical execute snapshot with internal `history_preserve_modified_at=true`, preventing timestamp drift.
2. The execute result records the complete post-write witness as `history_undo_expected_scene` and sets `history_rehydrate_scene=false`.
3. The internal non-undoable `scene.restore_snapshot` inverse requires an exact `expected_scene`, performs the Qt-free atomic persistence transition, then returns `history_redo_expected_scene` and `history_rehydrate_scene=false`.
4. Registry memory undo and fresh-registry durable redo attach the inverse's precise post-undo witness to the save redo. `scene.save` is now selected as a representative durable replay command.
5. Rejected stale undo/redo performs no target `os.replace`, adds no rejected history audit, imports no host, and does not call `scene.open` or rewrite project manifests.

## Evidence

- New `tests/test_scene_save_guarded_history.py` covers detached nested caller data, exact timestamp-stable memory history, fresh-registry durable history, terminal stale undo, stale redo retry, and project isolation.
- Focused compile plus regression set: `26 passed in 1.64s`.
- Wider relevant regression set: `117 passed, 10 subtests passed in 6.53s`.
- `tools/check_ai_command_audit_status.py` passed with schema version `4` and `unified_undo_redo_runtime=false`.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. The latter printed only pre-existing CRLF/LF warnings.
- Repository-wide pytest was intentionally not run.

## Next gate

E199 must close the remaining UI-host parity gap: semantic scene-save history intentionally suppresses `scene.open`, so adapters need an explicit success-only canonical snapshot mirror path rather than a host reload or manifest rewrite.
