# E202 Latent SceneManager Save-As Failure-Atomicity and Quarantine Gate

Date: 2026-08-01
Status: complete

## Previous gate

E201 established that `SceneManager.save_scene_as()` is a latent legacy helper: there is no runtime caller, while Standard UI explicit save already uses the user-owned Registry `scene.save` path. The helper remains outside history/audit because it lacks a typed semantic command contract.

## Decision and implementation

`save_scene_as(scene_path)` retains its public legacy name and `bool` return contract, but it is now failure-atomic:

1. It verifies that the current legacy payload is a non-empty dictionary.
2. It deep-copies that payload into a detached candidate and derives the candidate `name` from the target filename.
3. It delegates the candidate to existing `save_scene(scene_path, data=candidate)`, which uses the E197 shared `.pond` persistence primitive and commits legacy host state only after persistence succeeds.
4. Only after that call returns success does it retarget `_current_scene_path`.

Consequently, a write failure leaves the original in-memory scene object, scene name, path, modified state, editor-context reference, and save/modified signals untouched. A success creates the target bytes, synchronizes the legacy host with the persisted candidate, emits the existing success signals, and then changes the current path. This remains a compatibility helper, not a Registry command.

## Evidence

- `tests/test_scene_manager_save_as_quarantine.py` proves failed persistence cannot mutate the legacy host; successful Save As writes the named detached target, preserves the source file, synchronizes the host/signals, creates no command-audit file, and leaves a fresh Registry undo stack at `undo_empty`.
- The E201 static inventory was updated for the detached-candidate delegation and continues to prove there are no runtime callers of `save_scene_as()`.
- Focused regression set passed: `10 passed in 2.51s`.
- Wider relevant persistence/history/UI set passed: `127 passed, 10 subtests passed in 9.21s`.
- `py_compile` passed for the changed runtime and regression modules. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `git diff --check` passed. Diff output contained only existing LF/CRLF warnings.
- Repository-wide pytest was intentionally not run. This gate does not claim a user-facing Save As command, global unified undo/redo, native acceleration readiness, or OpenGL default readiness. Schema version `4` and `unified_undo_redo_runtime=false` remain unchanged.

## Next gate

E203 must inventory cross-runtime and extension-layer references to the public legacy `SceneManager.save_scene` / `save_scene_as` seams. It must classify any caller outside this version runtime before a future command migration or additional persistence contract is considered.
