# E175 Inspector Non-Scene Semantic Mutation-Contract Decision and Migration Gate

Date: 2026-07-31
Status: complete

## Previous gate

E174 closed the scene-backed authority boundary: when the active `.pond` owns an Inspector entity and Registry rejects its semantic mutation, Inspector stops rather than falling through to local `CommandStack`. The audit fact remains `unified_undo_redo_runtime=false`.

## Objective and decision

E175 audited every remaining Inspector non-scene local property-mutation family. None has a complete durable semantic-command contract today, so none migrates merely to reduce local `CommandStack` use. E175 instead preserves compatible local undo/redo behavior and closes a specific owner-boundary hole: a local fallback must not send a legacy object that is not owned by the active `.pond` to Registry or `SceneManager.update_scene_data()`.

This is **not** unified undo/redo completion, WorldBridge completion, default unified Pond completion, native acceleration completion, or OpenGL default-readiness.

## Protected contracts and non-goals

- Preserve the plugin runtime boundary, `.pond` semantics, Registry command IDs, Inspector bindings, SR2D seams, package/project manifests, and Qt-free L0-L4 contracts.
- Do not create a Registry fa?ade around transient Qt-host Python object identity.
- Do not misuse structural `connection.create` / `connection.delete` as arbitrary property setters.
- Do not remove Inspector's local stack or claim `unified_undo_redo_runtime=true` without a complete owner, serialization, inverse, and rehydration design.
- Do not modify `CONTEXT.md`, or stage, commit, reset, restore, clean, delete, or disturb unrelated worktree changes.

## Decision matrix

| Family | Current local mechanism | Source-backed finding | E175 decision |
|---|---|---|---|
| Non-scene canvas connection property | `ModifyConnectionPropertyCommand` | Registry exposes structural `connection.create` / `connection.delete`, not a property setter; legacy canvas connections lack a durable unique connection ID and serialized property/inverse contract. | Retain local fallback. A future migration needs durable connection identity, property schema, `.pond` serialization, inverse and rehydration. |
| Non-scene legacy node `x/y/radius/name` | `ModifyNodePropertyCommand` | `.pond`-owned IDs already use the semantic route. A legacy canvas node outside active `.pond` has no proven durable owner or reload contract. | Retain local fallback. |
| Non-scene positional holder | `_PropertyWriteCommand` or node command | `transform.set` requires a `.pond` scene plus `entity_id`; holder position alone is not a durable Registry payload. | Retain local fallback. |
| Non-scene script holder | `_PropertyWriteCommand` | `script.set_property` requires a persisted `.pond` entity, script identity and property path; arbitrary holders do not prove those contracts. | Retain local fallback. |
| Generic Python object or dictionary | `_PropertyWriteCommand` / node command | In-memory Python identity has no authoritative persistence target, serializer, canonical rehydration or durable inverse. | Retain local fallback. |

## Implemented owner-boundary tightening

`InspectorPanel._sync_scene_entity_data()` now obtains the active scene path and data, then returns unless `_current_scene_contains_entity(scene_data, entity_id)` is true. Therefore a non-scene legacy node can still execute exactly one local command, but it cannot issue a Registry mutation or call `SceneManager.update_scene_data()` against an unrelated active `.pond`.

The existing E174 three-state semantic route remains intact:

- `not_applicable`: use a compatible local fallback only when no active `.pond` owns the target.
- `applied`: do not create a local command.
- `rejected`: do not fall through to local mutation, retry Registry, refresh, or success signals.

## Recovery note

During this gate an accidental text-anchor edit truncated `inspector.py`. Before continuing E175, the file was restored from the local pre-edit Python 3.11 bytecode plus the shipped source baseline, preserving the newer E174 semantic methods and WorldBridge projection helpers. Recovery proof is compilation plus an import/method-inventory smoke check; no unrelated worktree item was restored, staged, or deleted.

## Evidence

- `py_compile` passed for `inspector.py` and `tests/test_inspector_property_mapping.py`.
- Inspector recovery import smoke confirmed `_scene_snapshot_for_pond`, Pond/entity UI helpers, both WorldBridge helpers, E174 semantic routing, owner guard, and command adapter methods are present.
- Focused offscreen suite passed: `30 passed in 1.80s` across Inspector command/property/script mapping, command-stack behavior and audit history coverage.
- The new regression proves a non-scene legacy node with an unrelated active `.pond` still uses one local command but produces no Registry call and no `SceneManager.update_scene_data()` call.
- `tools/check_ai_command_audit_status.py` passed with schema v4 and `unified_undo_redo_runtime=false`; core and GUI boundary checks passed.
- `inspector.py` is an existing untracked runtime artifact, so `git diff --check` cannot represent its full source. Exact changed/recovered method ranges were checked for trailing whitespace; known legacy whitespace in recovered baseline code and pre-existing `docs/INDEX.md` whitespace debt were not cleaned incidentally.

## Skips, fallback, and unblock path

- Full-suite execution was intentionally skipped: this gate changes one Inspector owner guard and documents migration preconditions; the focused suite and architecture checks cover the touched contracts.
- The correct fallback is local UI-host `CommandStack` mutation for the five families above. It is intentional compatibility behavior, not shared durable history.
- The unblock path for any semantic migration is a per-family owner contract: stable ID, authoritative persistence, serialized payload, durable inverse, canonical rehydration, and explicit Qt-free command boundary. Connection properties additionally require a real property command instead of overloading structural connection commands.

## Exactly one next gate

**E176 ? Inspector Legacy Local-Mutation Owner-Contract Design Gate:** design and evidence the first durable owner contract (starting with legacy canvas connection identity/property schema) before any Registry migration is attempted.
