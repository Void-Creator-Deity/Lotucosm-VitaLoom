# E185 Scene Prefab Placement Durable-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E184 retained script-property compatibility behavior because scripts have alias selectors rather than a serialized stable identity and its broad nested-property inverse lacks expected-current protection.

## Decision

**No durable-history migration in E185.** `prefab.place` is a real scene-owned SceneViewport path, but its failure authority and history record are incomplete.

## Audit evidence

- SceneViewport handles a `.pond` drop with “Apply” by calling `prefab.place`, then rehydrates via `scene.open` only when it succeeds. This is not a hypothetical CLI-only surface.
- Its failure branch publishes the legacy `create_entity` EventBus event. That is a scene-owned semantic rejection fallback, directly violating the terminal-rejection rule inherited from E174. It must be repaired before a history migration can be trusted.
- `prefab.place` is marked `undoable=True`, but Registry has no `prefab.place` inverse record branch. It cannot participate in the representative in-memory or fresh-Registry durable undo/redo path.
- The runtime reads the prefab source at execution time, shallow-copies it, forces the requested entity id, applies optional position, stores a relative `prefab_path`, and appends the entity. Its result returns only scene path, entity id, and prefab path: it does not record the exact placed entity, entity index, ordered pre/post entity lists, ordered connections, or source snapshot/digest.
- Re-executing `prefab.place` would read the current prefab file, so a source edit, rename, relocation, or changed resolution can make redo non-deterministic. Reusing guarded `entity.delete`/`entity.create` is possible only after the placement command records exact canonical entity and ordered-scene witnesses; that proof does not exist today.

## Compatibility retained

No runtime, Registry, SceneViewport, `.pond`, manifest, or audit-schema behavior changed in this inventory gate. Audit remains schema v4 with `unified_undo_redo_runtime=false`; no native acceleration, OpenGL-default, WorldBridge, or unified-history claim is made.

## Verification and documented blocker

Existing focused bridge/isomorphic tests establish that SceneViewport routes successful placement through `prefab.place` and that the command writes an entity. They do not prove terminal rejection or durable history. E185 records the hard blocker rather than claiming a partial migration.

Repository-wide pytest was not run because E185 made no runtime change. E183/E184's latest scoped result remains `31 passed, 3 subtests passed in 2.57s`; its compile, audit-status, core-boundary, and GUI-boundary checks passed.

## Fallback and concrete unblock path

First remove the scene-owned `.pond` prefab-apply fallback to legacy `create_entity`, and add a regression proof that failure produces no local mutation, success side effect, or rehydrate. Only then may a later gate add a placement record with immutable execution entity/index and full ordered-scene witnesses, derive undo through guarded deletion, derive deterministic redo through exact entity creation rather than rereading a changed prefab, and prove same-process plus fresh-Registry durable stale/retry behavior.

## Completion and next gate

E185 closes with no migration because terminal failure authority is currently broken and the command does not record a deterministic inverse.

Exactly one next gate: **E186 -- SceneViewport Prefab-Apply Terminal-Rejection Authority Repair Gate**.