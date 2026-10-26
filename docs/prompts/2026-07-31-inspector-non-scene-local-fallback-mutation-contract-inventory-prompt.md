# VitaLoom fresh-session prompt — E173 Inspector non-scene local-fallback mutation-contract inventory

Continue the VitaLoom mainline refactor from E172.

## Current truthful state

- E170 retired SceneViewport-local `CommandStack` and routes focused Ctrl+Z/Ctrl+Y through Registry semantic history.
- E171 identified `InspectorPanel` as the only production Runtime UI-host that constructs and executes a legacy local `CommandStack`.
- E172 retired Standard UI's stale `context.command_stack` dispatcher. Standard UI uses Registry `command.undo` / `command.redo`, and performs `scene.open` only after a successful scene-path result.
- `unified_undo_redo_runtime=false` remains correct. Never claim it is true, nor claim the entire refactor is complete.
- `CONTEXT.md` is an accidentally truncated untracked file. Do not edit, recreate, or infer it.

## E173 objective

Before any Inspector stack deletion, inventory all `InspectorPanel` local fallback mutation contracts. Cover connection, node, `position_x`/`position_y`, script-holder, generic object, and generic dictionary paths. For each, identify:

1. object predicate and field entry point;
2. legacy command type and execute/undo side effects;
3. available or missing Registry semantic command;
4. stable identity and `.pond` persistence/rehydration compatibility;
5. UI/canvas side effects;
6. migration classification.

Also list Inspector add-component/add-script/drop actions as out-of-band event-bus mutation routes if they do not reach `command_stack.execute()`.

## Known code landmarks

- Runtime boundary: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`
- Inspector: `core/VitaLoom/docks/inspector.py`
  - local stack construction near line 232;
  - semantic entity route near 1343–1487;
  - local fallback construction near 1489–1603;
  - sole local execute near 1617.
- Legacy commands: `core/VitaLoom/commands/command.py`
- Registry inverse/history logic: `core/VitaLoom/commands/registry.py`
- Registry specs/handlers: `core/VitaLoom/commands/runtime_commands.py`
- Tests: `tests/test_inspector_command_binding.py`, `tests/test_inspector_property_mapping.py`, `tests/test_script_property_edit.py`, `tests/test_command_stack_behavior.py`.

## Constraints

- Follow `AGENTS.md`: plan before substantial code, then implementation, verification, `docs/mainline_status.md`, and an updated fresh-session prompt.
- Do not equate `connection.create`/`connection.delete` with property updates for in-memory legacy canvas connections.
- Do not give arbitrary objects invented semantic IDs or silently persist them into `.pond`.
- Preserve existing dirty worktree; do not stage/commit/reset/restore/clean/delete unrelated files.
- Use Simplified Chinese for docs/status and user updates.
- Use evidence, not static intent. Document full-suite skips.

## Expected result of E173

Produce a completed plan with a mutation matrix, add evidence sufficient to show the inventory boundary, update the mainline status/index, and name exactly one next gate. The expected next gate must be an incremental retirement slice; do not remove the Inspector local stack wholesale.
