# E197 Scene Save Authority Decomposition and Terminal-Rejection Repair Gate

Date: 2026-08-01
Status: complete

## Previous gate

E196 established that `scene.save` could not receive history while singleton SceneManager owned opaque preparation, context mutation, persistence, signals, and direct bypass callers.

## Implementation

- Added Qt-free `core/VitaLoom/scene/scene_persistence.py`. It validates an explicit existing project-local `<project>/scenes/*.pond` target, detaches and JSON-validates a snapshot, optionally checks the exact current on-disk snapshot, then atomically replaces the target. It performs no Qt, SceneManager, editor-context, EventBus, manifest, or audit work.
- `scene.save` now requires explicit `scene_path` and `data`; it uses only that canonical helper, exposes prior and persisted detached snapshots, returns `history_rehydrate_scene=false`, and can be audited because its project-local path is present in payload.
- The legacy `SceneManager.save_scene()` now persists a detached copy first and updates editor context, dirty state, and signals only after persistence succeeds. `commit_persisted_scene()` is the success-only host mirror used by Standard UI after Registry save success.
- Standard UI supplies its explicit current scene path and snapshot to Registry; it commits the returned canonical snapshot only after a successful command. Project-world flush continues to call SceneManager, which now delegates its disk operation through the same persistence primitive.

## Proof

- New `tests/test_scene_save_canonical_persistence_authority.py` covers canonical audit-bearing success; stale/non-JSON rejection before target replacement or audit; no SceneManager call on Registry rejection; legacy host state remaining unchanged after persistence failure; and Standard UI success-only host commit.
- Targeted cross-gate suite: `112 passed, 10 subtests passed in 8.87s`.
- Audit/core/GUI boundaries passed. `git diff --check` passed with existing LF/CRLF warnings only. Schema remains v4 and `unified_undo_redo_runtime=false`.

## Constraints retained

This gate repairs persistence authority; it does **not** claim `scene.save` undo/redo yet. No global history, native acceleration, or OpenGL completion is claimed.

## Exactly one next gate

**E198 -- Scene Save Guarded-History Canonical Snapshot Contract Gate.**
