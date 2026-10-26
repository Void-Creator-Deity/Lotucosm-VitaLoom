# E178 Inspector Scene-Entity Semantic Mutation Schema and Guarded-History Authority Gate

Date: 2026-07-31
Status: complete

## Previous gate

E177 completed the remaining Inspector local-mutation inventory. No local family met all six prerequisites for semantic migration. It also identified a separate authority debt in the already-semantic active-scene entity route: `entity.set_property` accepts arbitrary property paths/values and its `entity.restore_snapshot` inverse restores without expected-current-state guarding.

## Objective

Audit and, only where a field/domain contract can be proven, harden Inspector active-scene entity mutation authority so semantic history is typed, stale-safe and canonically rehydrated. Preserve the existing terminal rejection rule: a semantic rejection must never fall through to local mutation.

## Scope

- Trace Inspector entity routing for transforms, scripts and generic public properties.
- Trace `entity.set_property`, `entity.restore_snapshot`, `transform.set`, `script.set_property`, Registry history recipes and durable replay selection.
- Establish a decision table per active-scene entity field family: identity, canonical JSON path, schema, exact expected-current guard, inverse, rehydrate, compatibility behavior and rejection handling.
- Implement at most one narrow hardening migration only after its field contract and stale behavior are testable.

## Active-scene field-family authority matrix

| Inspector family | Existing semantic route | Owner and canonical identity/path | Schema and inverse status | Decision |
| --- | --- | --- | --- | --- |
| `position_x` / `position_y` | `transform.set` with `scene_path`, `entity_id`, `position: [x, y]` | Active `.pond` scene plus stable entity `id`; canonical `entities[id].position` JSON field | The handler previously accepted arbitrary arrays and history replay overwrote the current position. The field is a provable finite 2D-vector domain. | **Select this one narrow candidate.** Validate and normalize `position`, accept optional exact `expected_position`, and make position history undo/redo use the opposite canonical position as its expected-current witness. |
| Other `transform.set` fields (`rotation`, `scale`) | Public command surface, not an Inspector property mapping in this route | Entity ID exists, but field-domain and canonical shape rules are not established by this Gate | Existing command schema remains broad; its non-position history remains compatibility behavior. | Do not expand this Gate beyond position. Record as follow-up authority debt. |
| `script_*` | `script.set_property` | Scene/entity ID exists; selected script is matched by `name` / `type` / `path`, then nested property path | Script selector and property path are broad, value is untyped, and inverse has no expected-current guard. | Defer; no generic script setter expansion. |
| Other public entity fields | `entity.set_property`, inverse `entity.restore_snapshot` | Scene/entity ID exists, but field selection is arbitrary | Arbitrary property/value schema; snapshot inverse lacks expected-current guard and can overwrite later canonical edits. | Defer; do not broaden a generic Registry setter. |

## Selected position contract

- Boundary payload remains Qt-free and JSON-only: `scene_path`, `entity_id`, `position`, optional `expected_position`.
- `position` and `expected_position` are exactly two finite non-boolean numbers and are normalized to JSON `[float, float]` vectors.
- Before writing, a supplied `expected_position` must exactly equal the entity's current canonical `position`; a mismatch returns deterministic `stale_transform_position` without a write.
- For a `transform.set` result that changes `position`, Registry history emits guarded inverse payloads: undo writes the old position only if the current position is the new position; redo writes the new position only if the current position is the old position.
- Inspector's existing successful `scene.open` path remains the canonical rehydration proof. A rejected semantic response remains terminal and never falls through to local `CommandStack` mutation.

## Non-goals

- Do not add or broaden a generic Registry property setter.
- Do not claim unified runtime-wide undo/redo, WorldBridge completion, native readiness or OpenGL default readiness.
- Do not migrate ownerless legacy Inspector objects; E175/E177 local fallback remains required.
- Do not claim the unrelated `rotation`, `scale`, script, or generic entity-property contracts are complete.

## Required proof

1. JSON-only Qt-free payload at the runtime boundary;
2. active `.pond` entity identity and canonical path validation;
3. position-specific finite 2D numeric validation;
4. same-process undo/redo rejection on stale current canonical position, without a write;
5. fresh-registry durable undo/redo rejection on the same stale witness, without a write;
6. successful Inspector canonical rehydrate; and
7. regression that a rejected Inspector entity semantic command still does not invoke local fallback.

## Fallback and unblock

If the current `transform.set` compatibility surface cannot preserve a typed position sub-contract without breaking `.pond` semantics, leave it unchanged and record the exact caller/data incompatibility. Do not solve missing evidence by local fallback after semantic rejection.


## Implementation completed

- `transform.set` now accepts an optional `expected_position` payload member. `position` and `expected_position` are normalized only when they are exactly two finite, non-boolean numeric coordinates; malformed payloads are rejected before any `.pond` write.
- A supplied witness must equal the entity's current canonical `position`. A mismatch returns `stale_transform_position` with entity, expected and actual values, and leaves the `.pond` unchanged.
- The `transform.set` history recipe now guards the selected position path only: undo writes the old position with the new position as its witness; redo writes the new position with the old position as its witness. `rotation` and `scale` remain explicitly outside this narrow contract.
- Inspector `position_x` / `position_y` continues to issue `transform.set`, and the pre-existing successful `scene.open` rehydrate remains the canonical UI refresh path. A semantic rejection remains terminal with no legacy `CommandStack` fallback.

## Evidence

- Initial compatibility subset: `27 passed, 3 subtests passed` for `test_ai_command_undo_redo_command_path.py`, `test_ai_command_durable_project_undo.py`, `test_scene_viewport_semantic_node_history.py`, and `test_inspector_property_mapping.py`.
- New focused regressions prove invalid position/witness payloads reject without `_write_json`; same-process stale undo and redo preserve the later canonical position and retain their history record; fresh-registry durable undo and redo reject the same stale witness without overwriting later state; Inspector position success rehydrates for global undo/redo, while a `stale_transform_position` response triggers neither local fallback nor success side effects.
- New-regression subset: `30 passed, 9 subtests passed`.
- Full E178 focused suite: `42 passed, 9 subtests passed` for Inspector mapping, semantic node/connection history, durable project undo, audit-status tool and command undo/redo path tests.
- `py_compile` passed for the two runtime modules and the three changed test modules. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. Audit output remains `schema_version: 4` and `unified_undo_redo_runtime: false`.

## Skips and boundaries

- The repository-wide pytest suite was not run: this gate changes only the position contract, guarded history recipe, focused tests and documentation; the listed suite covers the affected Inspector, Registry, durable-history and SceneViewport seams.
- This is not a unified undo/redo migration. It does not complete WorldBridge, native acceleration or OpenGL default readiness, and it does not certify script, generic entity, rotation or scale mutation contracts.
- `CONTEXT.md` was not modified. Existing unrelated dirty/untracked work was preserved; no staging, commit, reset, restore, clean or deletion was performed.

## Fallback and unblock

Keep script and generic entity fields on their current semantic compatibility paths, and retain E175/E177 ownerless local fallback. Any future migration must first prove a per-family canonical path, selector/identity, finite or otherwise narrow value schema, expected-current inverse and rehydrate behavior; it must not broaden a generic Registry setter or turn a semantic rejection into local mutation.

## Exactly one next gate

**E179 — Inspector Scene-Entity Script and Generic Mutation Contract Inventory Gate.** Audit the still-broad `script.set_property` and `entity.set_property` surfaces to produce a per-family decision matrix. It may select at most one separately provable narrow contract; absent that proof, it must document the compatibility boundary and make no migration.
