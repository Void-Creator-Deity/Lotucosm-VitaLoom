# E179 Inspector Scene-Entity Script and Generic Mutation Contract Inventory Gate

Date: 2026-07-31
Status: complete

## Previous gate

E178 completed a deliberately narrow guarded-history contract for Inspector `position_x` / `position_y` through `transform.set`. It did not broaden generic entity mutation or script mutation authority.

## Objective

Inventory the remaining broad active-scene Inspector mutation families (`script_*` and generic public entity fields) and decide, using evidence, whether any one field family has a safe semantic contract. This is primarily a decision gate; implementation is permitted only for one independently proven narrow family.

## Source trace

`InspectorPanel._on_property_changed()` first establishes that the selected object is owned by the active `.pond` scene, sends its mutation through `_sync_scene_entity_data_via_command()`, and treats every unsuccessful semantic call as `_SCENE_ENTITY_REJECTED`. A successful call still requests `scene.open`; a rejected one never reaches the local `CommandStack`, legacy scene sync, success signals, or rehydration.

The remaining active-scene branches are intentionally broad:

- `script_*` parses an Inspector key into `(script_name, dotted_property_path)` and calls `script.set_property` with an untyped JSON `value`.
- Every other public non-private property calls `entity.set_property` with its raw property name and untyped JSON `value`.

## Authority decision matrix

| Candidate family | Owner / identity | Canonical path and selector | Value domain / mutation grammar | History and durable replay | Inspector rehydrate / rejection | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `script_*` via `script.set_property` | Active `.pond` ownership plus stable entity `id` exists. | The script selector accepts any matching `name`, `type`, or `path`, and selects the first matching list item. It is therefore not one stable script identity. Properties use a dot path beneath `scripts[*].properties`; `_set_nested_property()` can materialize missing intermediate dictionaries. | `CommandSpec` has no narrow `value` schema. Property tokens are only broadly rejected for leading/trailing/doubled dots; values may be arbitrary JSON-compatible data. | Registry's inverse writes old/new values unconditionally with the same broad selector and path. The command is audit-selected and fresh-registry replay is available, but no expected-current witness prevents stale undo/redo from replacing a later value. | Existing successful route calls `scene.open`; an unsuccessful semantic result is terminal. These are necessary but do not repair selector, type, or inverse defects. | **No migration.** Do not widen this command or selector. Unblock only with an unambiguous serialized script identity, a fixed canonical property path, a narrow value schema, expected-current guarded inverse and stale same-process/fresh-registry proof. |
| Generic public entity field via `entity.set_property` / `entity.restore_snapshot` | Active `.pond` ownership plus stable entity `id` exists. | The public `property_path` is arbitrary dot notation inside the entity. `_set_nested_property()` creates missing dictionaries and permits writes to structural fields; malformed paths are not a narrow field contract. | `CommandSpec` does not define a narrow `value` schema. The Inspector forwards every non-private property name, rather than a field-specific command/domain. | The inverse uses `entity.restore_snapshot` to replace the entire prior entity without an expected-current witness. The command is audit-selected and fresh-registry durable undo/redo exists, but a replay can overwrite unrelated later canonical edits. | Existing successful route calls `scene.open`; a semantic failure remains terminal and does not fall back locally. | **No migration.** Do not expand generic setter behavior. Unblock only by extracting a single field-specific command with exact schema and guarded field-level inverse; snapshot replacement is not an acceptable generic inverse. |

## Result

Neither candidate satisfies the required matrix. E179 therefore selects **zero** behavior changes and preserves all compatibility paths:

- Existing script and generic command surfaces remain available for their current callers, without claiming they are stale-safe semantic-history contracts.
- E174's terminal semantic-rejection invariant remains in force for scene-owned entities.
- E175/E177 ownerless or non-scene local fallback remains unchanged.
- `unified_undo_redo_runtime=false` remains authoritative.

## Verification

The audit made no runtime behavior change. The focused offscreen regression suite passed:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_inspector_property_mapping.py `
  tests\test_scene_viewport_semantic_node_history.py `
  tests\test_scene_viewport_semantic_connection_history.py `
  tests\test_ai_command_durable_project_undo.py `
  tests\test_ai_command_audit_status_tool.py `
  tests\test_ai_command_undo_redo_command_path.py `
  tests\test_ai_command_undo_redo_bridge.py `
  tests\test_ai_command_audit_history.py
```

Result: `46 passed, 9 subtests passed in 2.76s`.

`py_compile` passed for the Inspector, command runtime/registry and focused test modules. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. The audit remains schema version 4 with `unified_undo_redo_runtime: false`.

Repository-wide pytest was intentionally not run: this phase was a source-contract inventory with no runtime change, and the focused suite covers the relevant Inspector, command-history, durable-replay, audit and boundary seams.

## Fallback and unblock path

Do not repair either family by adding a better generic setter, relaxing script matching, or routing a rejected semantic mutation to local history. A future narrow field must be separately owned by the active scene, have a stable field-specific command and canonical JSON location, restrict its JSON value domain, carry expected-current witnesses on undo and redo, survive a fresh Registry replay test, and rehydrate through `scene.open`.

## Exactly one next gate

**E180 — Inspector Scene-Entity Name Mutation Contract Discovery Gate.** Audit the one concrete active-scene `name` field as a possible field-specific replacement for generic entity mutation. First prove its canonical string domain, normalization, identity separation, expected-current history semantics, durable stale replay behavior, rehydration and compatibility impact; make no change unless each proof exists.