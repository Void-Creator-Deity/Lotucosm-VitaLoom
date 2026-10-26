# Phase E169 -- SceneViewport Remaining Node/Connection Semantic Command-History Migration

Date: 2026-07-31
Status: complete

## Previous gate

E168 completed one durable vertical slice: single-node SceneViewport drag uses the Qt-free `transform.set` Registry command and global semantic history. It also made focused-keyboard ownership explicit: local history is consumed only for remaining unmigrated local records, then keyboard falls through to Registry history. The audit remains `unified_undo_redo_runtime=false` because the histories are not merged.

## Objective

Remove the remaining SceneViewport **durable project-semantic** `CommandStack` paths for multi-node movement, connection creation/deletion, and legacy event-driven node create/delete. Replace them with JSON-safe Registry commands, durable inverses, canonical `.pond` refresh, and interaction proof. Do not serialize QWidget/QPainter objects or claim a merged history until each competing project mutation route is removed.

## Connection create/delete slice (complete within E169)

- Added Qt-free `connection.create` and `connection.delete` Registry commands. Both validate a JSON-safe snapshot and endpoints before one `.pond` write; deletion checks the exact list index and normalized endpoint/weight snapshot so duplicate connections cannot be removed ambiguously.
- Registry in-memory and fresh durable project history now build exact create/delete inverses that preserve list position and legacy endpoint aliases. SceneViewport connection create and right-click deletion now use the Registry, call `scene.open` to rehydrate canonical state, and emit success signals only after command success.
- `load_scene_data()` now restores numeric connection `weight`, closing a discovered `.pond` rehydrate asymmetry that otherwise caused a valid non-default-weight deletion snapshot to fail stale protection.
- Evidence: offscreen connection interaction, failure-atomicity, stale-snapshot, and fresh-Registry durable replay tests, together with prior viewport/history bridge coverage, passed `22 passed in 1.87s`; `tools/check_ai_command_audit_status.py` reports `viewport_connection_semantic_route=true` and still reports `unified_undo_redo_runtime=false`.

## Multi-node drag slice (complete within E169)

- Added the Qt-free `transform.batch_set` Registry command. It requires a non-empty JSON-safe transform list, rejects duplicate IDs, invalid/non-finite coordinates, and missing entities, validates every target before mutation, then performs one canonical `.pond` write with old/new position snapshots.
- Registry constructs deterministic `transform.batch_set` inverse/redo records for both in-memory and fresh-Registry durable project history. The command is an explicit representative durable-history path; it does not make history unified.
- SceneViewport captures the whole selection at press, previews each selected node from that immutable start snapshot, and commits one batch command at release. Success rehydrates via `scene.open` before success signals; failure restores every preview coordinate and emits no success signal. This also removes the former multi-move double-delta risk and does not call `CommandStack.execute`.
- Evidence: offscreen interaction proves the exact two-node result, canonical `.pond` rehydrate, global undo/redo, zero local-stack execution, preview rollback, duplicate/missing entity atomicity, and one-write success. Fresh-Registry durable undo/redo is covered. The wider targeted collection passed `27 passed in 2.38s`; audit, core/GUI boundary checks, and `git diff --check` passed. Audit reports `viewport_multi_node_drag_semantic_route=true`, `viewport_connection_semantic_route=true`, and remains `unified_undo_redo_runtime=false`.

## Event-driven node add/delete slice (complete within E169)

- SceneViewport `_add_node()` and event-driven `create_entity_node()` now commit `entity.create`; `_delete_node()` and `_delete_node_by_instance()` now commit `entity.delete`. Every successful mutation reopens the canonical `.pond` with `scene.open`, maps selection onto rehydrated instances, and only then sends the existing UI/object/event success side effects. A Runtime command failure neither emits success signals nor republishes the legacy `create_entity` event when a current scene exists.
- `entity.create` now declares `entity_index` as genuinely optional rather than inheriting the generic all-fields-required schema. `entity.delete` atomically removes every incident connection and returns the original entity slot plus connection snapshots with exact `connection_index` values. Its inverse is the internal `entity.restore_deleted_snapshot`, which validates entity index, duplicate connection indices, and both connection endpoints before any write; valid undo/redo restores original entity and connection ordering.
- Tests keep `EditorContext.event_bus` as the kernel-injected UI-host seam: direct viewport fixtures attach a temporary mock only for the test and restore it afterward. Production ownership did not move into Runtime authority.
- Evidence: targeted E169 suite passed `33 passed, 3 subtests passed in 3.31s`; Runtime compile passed; audit reports `viewport_event_node_semantic_route=true` and includes `entity.delete` as a durable representative command. `tools/check_core_boundaries.py` and `tools/check_gui_boundaries.py` passed; `git diff --check` passed with only pre-existing LF/CRLF warnings.
## Required discovery before production edits

- Inventory every `CommandStack.execute`, `undo`, and `redo` route in SceneViewport, including event-bus subscribers, keyboard handling, context menu, toolbar, drag/drop, and parent-widget integration.
- Map `.pond` entity and connection schema variants, duplicate/invalid reference behavior, selection updates, signal/event contracts, SceneManager reload behavior, and any consumers of `ConnectionLine.to_dict()`.
- Audit Registry inverse generation for `entity.create`, `entity.delete`, `transform.set`, and any new batch transform/connection commands. Forward and inverse payloads must be deterministic, JSON-safe, and valid from a fresh Registry where durable replay is supported.
- Decide whether multi-node movement is one atomic batch semantic command or explicitly split only if selection semantics make that unavoidable. It must not create partial scene writes or one UI-object record per node.

## Implementation requirements

- Add or extend Qt-free runtime commands and Registry undo records for each selected remaining semantic slice. Validate the whole payload before writing and preserve `.pond` compatibility.
- Convert each corresponding SceneViewport interaction to command -> canonical `scene.open` rehydrate. Never execute a duplicate local `CommandStack` mutation after semantic success.
- Preserve selection, event-bus, project-modified, and command-executed behavior only after success. Define failure rollback/rehydration behavior explicitly.
- Remove the focused-keyboard local fallback only if no remaining SceneViewport durable project semantics use local stack. Otherwise keep it and record exact ownership.
- Keep the legacy `CommandStack` public seam only where no durable project mutation remains or compatibility requires it; do not make it Registry authority.

## Completion evidence

- Offscreen interaction tests cover multi-node drag, connection create/delete, and each migrated add/delete entry as applicable: forward `.pond` result, `scene.open` rehydrate, global undo/redo, no duplicate local stack call, invalid input, and failure atomicity.
- Fresh-Registry durable undo/redo proof exists for every newly declared durable command that claims support.
- Targeted and relevant wider suites, audit/core/GUI checks, `git diff --check`, and an explicit full-suite/environment fallback record pass.
- `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and a completed fresh-session prompt record the exact remaining history boundary and one next gate.

## Constraints

- Preserve `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` as the product runtime boundary, Qt-free L0-L4, `.pond`, AI command registry, Inspector bindings, SR2D seams, and manifests.
- QPainter remains default. Do not claim full runtime unified undo/redo, unified Pond, replay authority, WorldBridge readiness, native acceleration, or OpenGL default-readiness without separate evidence.
- Preserve unrelated dirty work. Do not stage, commit, push, reset, restore, clean, or delete it.

## Phase completion and one next gate

E169 is complete. This phase migrated the selected SceneViewport project-semantic node, connection, and drag paths into Qt-free Runtime commands with canonical rehydration and representative durable history evidence. It did **not** merge all histories: `unified_undo_redo_runtime=false`, and the legacy `CommandStack` remains for other unmigrated operations.

The only next gate is: **inventory the remaining SceneViewport operations that still depend on the local `CommandStack`, then establish their entry-point list and boundary evidence before selecting another migration slice.** Do not begin a new mutation migration before recording its plan and fresh-session prompt.