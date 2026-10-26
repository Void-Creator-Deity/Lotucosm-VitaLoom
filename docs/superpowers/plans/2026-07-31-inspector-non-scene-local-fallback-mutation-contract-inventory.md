# E173 Inspector Non-Scene Local-Fallback Mutation-Contract Inventory

Date: 2026-07-31
Status: complete

## Previous gate

E172 retired the stale Standard UI `context.command_stack` dispatcher. Standard UI undo/redo now dispatch `command.undo` / `command.redo` through the Qt-free shared Registry and rehydrates a successful scene result through `scene.open`. `unified_undo_redo_runtime=false` remains deliberate: `InspectorPanel` is the only production Runtime UI-host that still constructs and executes its own legacy `CommandStack`.

E171 established that scene-backed Inspector entity edits already use semantic Registry mutations (`transform.set`, `script.set_property`, `entity.set_property`) followed by canonical rehydration. The remaining Inspector local stack must therefore be understood as a compatibility fallback, not removed by assertion.

## Objective

Create an evidence-backed contract inventory for every Inspector mutation path that can still reach the legacy local `CommandStack`, especially non-scene-backed connection, ordinary node, positional, script-holder, generic object, and generic dictionary edits. For every route record:

- mutation entry point and object-shape predicate;
- current command implementation and undo/redo behavior;
- whether the shared Registry has an equivalent semantic contract;
- `.pond` persistence and canonical-rehydration consequences;
- UI/canvas and Inspector side effects;
- migration class: directly migratable, needs a new semantic contract, or intentionally outside the local-stack path.

Choose exactly one safe, small next retirement slice. Do not delete the Inspector stack in this phase.

## Protected contracts and non-goals

- Preserve `.pond` scene semantics, AI command Registry flows, Inspector command binding, SR2D public seams, package/project manifests, and Qt-free L0-L4 contracts.
- Do not treat Registry `connection.create` / `connection.delete` as a property-write contract for legacy canvas connection objects without proving compatible identity, payload, persistence, undo inverse, and rehydration semantics.
- Do not invent stable scene identities for arbitrary node/connection/object instances in the Qt host.
- Do not claim unified whole-editor undo/redo, overall refactor completion, native/OpenGL readiness, WorldBridge readiness, or default unified Pond/replay.
- Do not alter, recreate, or infer missing `CONTEXT.md` content.
- Do not stage, commit, reset, restore, clean, delete, or disturb unrelated worktree changes.

## Investigation and implementation plan

1. Write this plan and a fresh-session prompt before changing Runtime behavior.
2. Trace Inspector selection presentation, `_on_property_changed`, `_apply_scene_entity_property_command`, `_build_property_command`, and all legacy `Command` classes used by the fallback.
3. Trace Registry command specifications and handlers to compare actual payload/identity/persistence contracts, rather than matching command names alone.
4. Record an explicit mutation matrix, including the Inspector add-component/add-script/drop event paths as non-stack entries so the inventory has a clear boundary.
5. Add or update focused regression evidence only when it proves the inventory boundary or a selected next slice.
6. Run focused Inspector/command-history/audit/boundary checks, record proof and skips, then update the status board, index, and prompt with exactly one next gate.

## Acceptance evidence

- Every path that can invoke `InspectorPanel.command_stack.execute()` is classified by object shape and command type.
- Connection and node paths are distinguished from `.pond` connection/entity semantic commands.
- The inventory makes explicit why an existing Registry command is or is not a safe replacement.
- Any scene-backed semantic-first residual fallback risk is identified independently from true non-scene legacy fallback.
- The selected next slice is narrow, testable, and does not remove the non-scene stack before a contract exists.
- Focused tests, audit/boundary tools, static searches, and a scoped whitespace check pass or are explicitly documented.

## Verification commands

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_inspector_command_binding.py `
  tests\test_inspector_property_mapping.py `
  tests\test_script_property_edit.py `
  tests\test_command_stack_behavior.py `
  tests\test_ai_command_audit_status_tool.py
& '.\.venv\python.exe' -B tools\check_ai_command_audit_status.py
& '.\.venv\python.exe' -B tools\check_core_boundaries.py
& '.\.venv\python.exe' -B tools\check_gui_boundaries.py
rg -n 'CommandStack\(|command_stack\.execute|Modify(Connection|Node)PropertyCommand|_PropertyWriteCommand' FrameCore\plugins\lotucosm-vitaloom\versions\1.0.0\runtime\core\VitaLoom\docks\inspector.py
```

## Completion record

### Authoritative local-stack boundary

`InspectorPanel._on_property_changed()` is the sole production local-stack execution site: after a property has not been accepted by `_apply_scene_entity_property_command()`, it calls `_build_property_command()` and then `self.command_stack.execute(command)`. Static Runtime inventory shows Inspector is the only production constructor/executor of this stack; the legacy `memory_editor` comments/reference do not add an Inspector execution path.

### Mutation-contract matrix

| Inspector route | Object predicate / entry field | Current local command and undo | Existing Registry contract | Persistence / rehydration | UI side effect | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| Scene-backed entity | `entity_id_from_inspector_obj(obj)` plus current scene path; `position_x`, `position_y`, `script_*`, or other public fields | On Registry success none; on Registry failure current boolean control flow can still fall through to a local command | `transform.set`, `script.set_property`, `entity.set_property`; all require `.pond` `scene_path` and `entity_id` | Registry writes canonical `.pond`; Inspector runs `scene.open` only after success | canonical rehydrate, then standard modified/executed signals | Already semantically migrated on success; **E174 must retire its rejected-command local fallthrough** |
| Legacy canvas connection property | `start_node`, `end_node`, and editable existing attribute | `ModifyConnectionPropertyCommand`; sets arbitrary object attribute and undo restores it; refreshes `connection.canvas.update()` | `connection.create` / `connection.delete` only | Registry contracts create/delete a JSON `.pond` connection requiring complete `connection` object and exact `connection_index`; no set-property inverse exists | canvas repaint only | Needs a new `connection.set_property` contract and proven scene mapping; not directly migratable |
| Legacy node explicit property | editable `x`, `y`, `radius`, or `name` | `ModifyNodePropertyCommand`; set/restore attribute; `canvas.update_visualization()` when available | No node-property command | `entity.set_property` / `transform.set` require a `.pond` entity ID and scene path, which arbitrary node objects do not supply | visualisation refresh | Needs a node/object semantic contract or an explicit mapping; not directly migratable |
| Position adapter | `position_x` / `position_y` on an object `position`, an `x/y` node, or a dictionary | `_PropertyWriteCommand` for `position` object/dict, `ModifyNodePropertyCommand` for x/y; restores snapshot/value on undo | `transform.set` exists only for a scene entity | Non-scene holders have no verified `.pond` entity identity; serialising one would change authority and persistence semantics | optional node/canvas refresh depends on branch | Scene entity branch already semantic; all non-scene shapes need identity/contract design |
| Script-holder property | `script_<script>_<dotted.path>` where `scripts_holder()` resolves | `_PropertyWriteCommand` snapshots entire scripts collection, applies/coerces value, restores snapshot on undo | `script.set_property` exists for a `.pond` entity, named script, and property path | A non-scene script holder is not proven to be a persisted entity; no canonical rehydrate target exists | optional `canvas.update_visualization()` | Scene entity branch already semantic; legacy holder needs a runtime-object or persistence contract |
| Generic object property | any `hasattr(obj, prop_name)` after special cases | `ModifyNodePropertyCommand`; generic `setattr`/restore | No generic object property command | Python object identity (or `id()` fallback) is process-local and cannot become durable command identity | optional canvas visualisation refresh | Needs a new scoped semantic contract; never map blindly to entity command |
| Generic dictionary property | `isinstance(obj, dict)` after special cases | `_PropertyWriteCommand`; `__setitem__` new/old values | No generic dictionary command | Dictionary may be detached/ephemeral; entity dictionary is already captured by the scene-backed route before reaching here | no mandatory repaint | Needs ownership/persistence classification before migration |

### Out-of-band Inspector mutations (not CommandStack routes)

- `_show_add_component_dialog()` and `_show_add_script_dialog()` publish editor-event-bus requests; they do not invoke `_build_property_command()` or `command_stack.execute()`.
- `dropEvent()` publishes `add_script_to_entity` and `set_entity_sprite_path`; likewise it is outside the local property-history path.
- These event-bus mutations require their own semantic-command authority audit, but they are not evidence for removing the Inspector local property stack and are intentionally excluded from E174.

### Contract comparison result

The Registry exposes durable representative history for entity, transform, script, and **structural** scene connection commands. It does **not** expose an arbitrary legacy node/connection/object/dictionary property-write contract. In particular, `connection.create` / `connection.delete` take serialized `.pond` connection records (and deletion needs an exact index); they are not substitute setters for canvas connection attributes.

The one minimal safe retirement slice is therefore not a wholesale stack deletion: **E174 — Inspector scene-backed semantic-rejection hard stop**. It will make the scene-backed route tri-state (not applicable / semantic success / semantic rejection) so a Registry-rejected scene entity edit cannot mutate locally, cannot get a second Registry attempt through legacy sync, and cannot produce a second history authority. Non-scene node/connection/object fallbacks remain unchanged until their contracts exist.

### Verification record

- Focused offscreen evidence passed: `26 passed in 1.46s` for Inspector binding/property/script coverage, legacy `CommandStack`, and audit-status regression.
- `tools/check_ai_command_audit_status.py` passed at schema v4; it still truthfully reports `unified_undo_redo_runtime=false` and identifies Inspector as the remaining local stack surface.
- `tools/check_core_boundaries.py` and `tools/check_gui_boundaries.py` passed.
- Static Inspector inventory found one construction site (`:232`) and one execute site (`:1617`), with six local command-build branches. Full suite was intentionally not run because this phase changed no Runtime behavior.
- Whole-worktree `git diff --check` remains unsuitable as a phase proof due to pre-existing `docs/INDEX.md` trailing whitespace; no unrelated cleanup was performed. `CONTEXT.md` was not touched.

## Exactly one next gate

**E174 — Inspector Scene-Backed Semantic-Rejection Local-Fallback Retirement.**

