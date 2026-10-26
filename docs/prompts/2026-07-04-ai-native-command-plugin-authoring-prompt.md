# VitaLoom Phase 5 AI-Native Command And Plugin Authoring Prompt

You are continuing VitaLoom's long-term mainline as the lead engineer. Do not load old C0dex threads unless the user explicitly asks. Use repository truth, current tests, and current command output.

## Read First

1. `AGENTS.md`
2. `docs/mainline_status.md`
3. `docs/superpowers/plans/2026-07-04-ai-native-command-plugin-authoring.md`
4. `docs/ai_native_command_layer.md`
5. `docs/plugin_command_contract.md`
6. `tests/test_plugin_command_contributions.py`
7. `tools/check_project_plugin_model.py`
8. `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
9. `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
10. `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json`

## Current Truth

- Architecture remains plugin-shaped: FrameCore hosts the `lotucosm-vitaloom` product plugin, and the runtime lives under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt6 remains the editor shell. QPainter remains default. OpenGL remains opt-in.
- SR2D native C++/Rust is not accelerated on this machine until extensions build/import and pass parity plus benchmark.
- Phase 5 is about command semantics and plugin authoring: UI, CLI, MCP, and agents must share the VitaLoom Command Registry.
- Do not let UI code, MCP adapters, or scripts bypass the command registry for project, scene, asset, or plugin mutations.
- Current MCP scene edit proof: `mcp_adapter.create_entity(scene_path, entity)` is a thin wrapper over `entity.create`; tests compare CLI/MCP normalized `.pond` output for `entity.create`.
- Current MCP transform proof: `mcp_adapter.set_transform(...)` is a thin wrapper over `transform.set`; tests compare CLI/MCP normalized `.pond` output and Inspector payload binding for `transform.set`.
- Current MCP script proof: `mcp_adapter.set_script_property(...)` is a thin wrapper over `script.set_property`; tests compare CLI/MCP normalized `.pond` output and Inspector payload binding for `script.set_property`.
- Current audit proof: representative project-scoped mutating commands write `.vitalloom/command_audit.jsonl` and return `audit_id`/`audit_path`.
- Current undo proof: `CommandRegistry` has a representative in-memory `undo_last()` / `redo_last()` bridge for `entity.create`, `transform.set`, and `script.set_property`; undo/redo actions also append audit entries.
- Current command-facing proof: `command.undo` and `command.redo` delegate to the representative registry bridge in the current registry session; MCP helpers `undo_last()` and `redo_last()` wrap those command ids.
- Current UI proof: `ui.command_actions.register_editor_command_actions(...)` binds `edit.undo` / `edit.redo` shortcuts, `Edit/Undo` and `Edit/Redo` menu actions, and toolbar `Undo` / `Redo` actions to `command.undo` / `command.redo`; `EditorKernel` calls the hook after `LayoutManager` is constructed.
- Current durable replay proof: `command.undo_project` / `mcp_adapter.undo_project(project_path)` can replay the latest representative project-scoped execute audit as `action=durable_undo` across a fresh `CommandRegistry`; `command.redo_project` / `mcp_adapter.redo_project(project_path)` can replay the latest representative durable undo as `action=durable_redo`.
- Current status proof: `tools/check_ai_command_audit_status.py` reports `durable_audit_with_representative_undo`, `command_undo_redo_path=true`, `ui_undo_redo_action_binding=true`, `ui_menu_toolbar_undo_redo_binding=true`, `representative_undo_redo_runtime=true`, `representative_durable_project_undo=true`, `representative_durable_project_redo=true`, and `unified_undo_redo_runtime=false`. `CommandStack` exists but is not integrated with the registry bridge.

## Phase 5 Loop

For every substantial step:

1. Audit current truth from docs and command output.
2. Summarize the previous gate.
3. Update the phase plan if scope changes.
4. Use TDD for behavior changes.
5. Run focused verification.
6. Record evidence in `docs/mainline_status.md`.
7. Update this prompt or create the next phase prompt if the next session needs new instructions.

## First Gate

Keep the registry/catalog consistency gate green:

- Every command declared in `runtime/builtin/package_index.json` must be describable through the Command Registry.
- Every registered command capability used by declared builtin commands must resolve to a builtin package id.
- The standalone checker `python -B tools/check_project_plugin_model.py` must enforce this, not just the pytest suite.

## Next Recommended Gate

Choose the next undo frontier:

- Either design the next history boundary beyond representative durable project undo/redo, or start Phase 6 runtime unification/replay.
- Keep durable audit history, command-facing undo/redo, UI shortcut action binding, and representative registry bridge evidence intact.
- Do not claim full unified undo, branching durable history, conflict resolution, CLI subprocess workflow polish, or legacy UI `CommandStack` integration until each is separately tested.

## Verification Commands

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_command_path.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py
python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py
python -B tools/check_ai_command_audit_status.py
python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tests/test_plugin_command_contributions.py tools/check_project_plugin_model.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
```

## Reporting Rules

In the final response, distinguish:

- Implemented code/docs
- Tests actually run
- Skipped or unavailable checks
- Architecture impact
- Remaining Phase 5 risks
- One concrete next gate
