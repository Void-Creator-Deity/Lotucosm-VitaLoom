# E177 Inspector Remaining Legacy Mutation Owner-Contract Inventory Gate

Date: 2026-07-31
Status: complete

## Previous gate

E176 migrated only the provably scene-owned `ConnectionLine.weight` edit. It established a nonserialized `SceneViewport` owner witness, ordered-list-plus-snapshot connection identity, a typed JSON-only `connection.set_weight` command, guarded inverse history, and canonical `scene.open` rehydration. It did not make all Inspector local history durable.

## Objective

Inventory every remaining Inspector local property-mutation family and decide whether it currently proves all six semantic-authority prerequisites: durable owner, stable serialized identity, canonical read/write path, narrow typed schema, stale-safe inverse, and canonical rehydration. Select no migration candidate unless all six are independently evidenced.

This is an authority-inventory gate. It does not claim complete refactoring, unified runtime-wide undo/redo, WorldBridge completion, native readiness, or OpenGL default readiness.

## Source trace and routing result

`InspectorPanel._on_property_changed()` first attempts the active-scene entity route, then the exact scene-owned connection-weight route, and builds a local `CommandStack` command only when both are not applicable. A semantic rejection is terminal: it does not execute a local command, refresh, or emit success signals.

The local builder remains deliberately broad because it is a UI-host compatibility adapter:

- `ModifyConnectionPropertyCommand` stores a Python connection reference and changes one attribute with `setattr()`.
- `ModifyNodePropertyCommand` stores a Python object reference and changes one attribute with `setattr()`.
- `_PropertyWriteCommand` stores a Python target and closure pair for positional holders, script holders, and dictionaries.

Those object-reference commands are not JSON payloads, do not prove durable ownership, and cannot themselves supply a safe project-history inverse.

## Authority decision matrix

| Family / selected source | Editable fields currently routed here | Durable owner witness | Stable serialized identity | Canonical persistence/read-write path | Narrow typed schema | Stale-safe inverse | Canonical rehydrate | Decision, fallback, unblock |
|---|---|---|---|---|---|---|---|---|
| Active `.pond` entity with an ID present in `SceneManager.get_scene_data().entities` | `position_x` / `position_y`, valid `script_*`, other public property keys | Yes: active scene membership by entity ID | Yes: entity `id` | Yes: `transform.set`, `script.set_property`, or existing `entity.set_property` then `scene.open` | **No for the generic family**: `entity.set_property` accepts arbitrary `property_path` and unconstrained `value`; transform/script schemas are narrower only at their command boundary | **No for the existing generic inverse**: `entity.restore_snapshot` restores a prior entity snapshot without expected-current-state guarding | Yes: successful Inspector route runs `scene.open` | Not a remaining local fallback: semantic route precedes the builder and rejection is terminal. It is **not** a new E177 migration candidate because generic entity authority needs schema/inverse hardening. E178 owns that audit/design; do not make rejected scene entity edits local. |
| Scene-owned `ConnectionLine.weight` | finite numeric `weight` | Yes: nonserialized `SceneViewport` witness plus exact membership | Yes: ordered connection index plus expected serialized snapshot | Yes: `connection.set_weight` mutates only canonical `.pond.connections[index].weight` | Yes: finite non-boolean numeric validation | Yes: old/new exact snapshots guard undo and redo | Yes: `scene.open` | Complete in E176; excluded from remaining-local candidates. |
| Scene-owned `ConnectionLine` non-weight display/legacy attributes | e.g. `color`, `width`, any mutable attribute exposed by legacy UI | Partial: E176 owner witness exists | Partial only: ordered index plus snapshot identifies the serialized row, but row contains endpoint/weight data only | **No**: `ConnectionLine.to_dict()` / scene export persist endpoints and `weight`, not UI display attributes; Registry has no corresponding field command | No | No | No canonical value exists to rehydrate | Retain one local `ModifyConnectionPropertyCommand` fallback. Unblock only by first defining an intentional serialized property, exact identity, typed per-property command, guarded inverse, and renderer rehydrate; do not overload structural connection commands. |
| Unowned or non-scene connection | `weight` and any other mutable connection attribute | No: no current authoritative scene/canvas ownership proof | No durable identity; endpoints may repeat and Python identity is process-local | No | No | No | No | Retain local connection command. E175/E177 tests prove it produces no Registry write. Unblock requires a named owner domain and durable serialized connection identity before any command migration. |
| Legacy/non-scene object attributes | `x`, `y`, `radius`, `name`, and generic `hasattr(obj, prop_name)` attributes | No active `.pond` ownership proof, even when a legacy object happens to expose `id` | No: object reference and fallback `id(obj)` are not serialized identity | No canonical target; local node command is `setattr()` only | No | No | No | Retain local `ModifyNodePropertyCommand`. E175 guard prevents an unrelated active scene from being mutated. Unblock requires explicit owner binding, serializer and a field-specific command contract. |
| Position holder / dict position adapter | `position_x`, `position_y` through `.position`, `.x/.y`, or dict `position` | No for non-scene holders | No durable identity for holder or dict slot | No canonical target outside a proven entity; closures mutate object/list in memory | No: adapters coerce values locally | No: closure rollback can overwrite later local mutation | No | Retain local `_PropertyWriteCommand` or local node command. The active-scene entity counterpart is already semantic; only ownerless adapters remain local. Unblock requires a serialized transform owner and typed finite vector contract. |
| Identity-less script holder | valid `script_<name>_<dotted-path>` keys on a legacy object/dict | No active entity ownership | Script name/path alone is not an entity identity | No canonical `.pond` entity/script target; local code snapshots a Python holder's scripts | No durable per-value schema beyond local coercion | No: restoring a whole local scripts snapshot has no expected-current guard | No | Retain local `_PropertyWriteCommand`. E177 regression proves no Registry write. Unblock requires entity ownership plus stable script selector/path, typed value rules, expected-current inverse and rehydrate. |
| Arbitrary dictionary field | generic dict keys and position adapter values | No | No: dictionary address/key is process-local, not project identity | No canonical writer for arbitrary dicts | No | No | No | Retain local `_PropertyWriteCommand`. Do not create a generic Registry property setter. Unblock is a domain-specific serialized model, not a dictionary adapter. |

## Focused regression evidence

`tests/test_inspector_property_mapping.py` now additionally proves two authority boundaries that were easy to blur in the UI adapter:

1. a scene-owned connection's nonserialized `color` edit performs exactly one local command and no Registry mutation; and
2. an identity-less script holder's valid `script_*` edit performs exactly one local command and no Registry mutation.

Existing focused coverage continues to prove that active scene entities route through Registry without local `CommandStack` execution, scene semantic rejection does not fall back, scene-owned `ConnectionLine.weight` rehydrates through Registry, and an unowned connection stays on the local path.

## Result and next candidate decision

No remaining local family satisfies all six prerequisites. Therefore E177 deliberately selects **zero** migration candidates. The nearest superficially similar family—generic active-scene entity property editing—is already semantic, but its arbitrary property/value surface and unguarded snapshot inverse fail this gate's schema and stale-safety criteria. It must be hardened independently rather than used to justify a generic local-family migration.

## Verification

- Changed test module compilation passed.
- Focused offscreen Inspector/property, connection history, durable project undo, audit-status and undo/redo command-path suite passed: `31 passed, 3 subtests passed`.
- `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed.
- Scoped tracked-file `git diff --check` passed apart from Git's existing LF/CRLF working-copy warning. Full suite was intentionally skipped because this gate adds focused authority-boundary coverage and documentation only.

## Fallback and unblock path

The local `CommandStack` remains intentional compatibility behavior for all ownerless/nonserialized families in the matrix. It is not durable project history and does not change `unified_undo_redo_runtime=false`.

The next gate must first audit and design the already-semantic scene-entity property authority: restrict the generic surface into field/domain-specific contracts where justified, add expected-current guarding to inverses, preserve canonical rehydration, and retain E174's terminal-rejection invariant. It must not solve this by adding another generic setter or by routing rejected semantic edits into local mutation.

## Exactly one next gate

**E178 — Inspector Scene-Entity Semantic Mutation Schema and Guarded-History Authority Gate.**