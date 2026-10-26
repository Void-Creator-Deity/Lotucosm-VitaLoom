# E195 Project Active Scene Guarded-History Canonical/Host-Isolation Contract Gate

Date: 2026-08-01
Status: complete

## Previous gate

E194 made `project.set_active_scene` canonical-only and moved host loading to a separate success-gated `scene.open` request.

## Decision and implementation

E195 found guarded history feasible only after making generic UI rehydration an explicit result contract rather than an unconditional reaction to any returned `scene_path`.

- `project.set_active_scene` is now undoable and accepts an optional full-manifest `expected_project` witness. It records exact prior `active_scene` key presence/value (including arbitrary legacy JSON), the post-execute manifest witness, and `history_rehydrate_scene: false`.
- The owned non-undoable inverse `project.restore_active_scene_snapshot` checks the complete expected manifest before any write, restores the exact old value or removes the absent key, and returns the post-undo redo witness plus the same explicit no-rehydrate marker.
- Registry memory and durable replay construct the inverse record, carry the restore-produced witness to redo, and include active scene in the representative durable-replay inventory.
- `ui.command_actions` and Standard UI now rehydrate only when a successful history result has a nonblank `scene_path` and does not explicitly set `history_rehydrate_scene` to `false`. Existing scene-entity history retains its default rehydration behavior; direct ProjectPanel activation remains its independent success-gated `scene.open` flow.

## Proof

- New `tests/test_ai_command_project_active_scene_guarded_history.py` proves memory and fresh-registry durable undo/redo, pre-write/pre-audit stale undo and redo rejection, canonical retry, absent-key deletion, exact legacy-value restoration, cross-project isolation, and no injected host/EventBus/CommandStack/load callback effect.
- New Standard UI contract tests and UI action coverage prove opt-out history does not issue `scene.open`, while default scene history still does.
- Targeted bridge/history suite: `74 passed, 10 subtests passed in 5.21s`.
- `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. `git diff --check` exited successfully with existing line-ending warnings only.

## Constraints retained

Audit schema remains v4 and `unified_undo_redo_runtime=false`. This is representative guarded history, not a claim of a global undo/redo runtime. `scene.save`, native acceleration, and OpenGL default readiness remain outside this gate.

## Exactly one next gate

**E196 -- Scene Save Canonical-State Guarded-History Feasibility Audit.**
