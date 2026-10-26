# Phase E171 -- UI-Host Local-History Owner Inventory and Authority-Retirement Slice Selection

Date: 2026-07-31
Status: complete

## Previous gate

E170 retired SceneViewport-local `CommandStack` ownership. Its completion proof showed focused Ctrl+Z/Ctrl+Y now reaches the Qt-free Registry history route directly, while `unified_undo_redo_runtime=false` remains accurate because Inspector and potentially other UI-host adapters still own local history.

## Objective

Produce an exact, evidence-backed inventory of every remaining UI-host local-history owner and its project-mutation entry points. Classify each entry point as semantic Runtime authority, legacy local authority, or transient UI state, then choose exactly one smallest safe authority-retirement slice for a later implementation phase.

## Scope and invariants

- This is an inventory and decision phase. Do not migrate Inspector or change `.pond` semantics unless a minimal evidence test is needed to establish current behavior.
- Search all versioned VitaLoom Runtime UI-host code and direct callers for `CommandStack`, `execute`, `undo`, `redo`, command-object subclasses, and history-related shortcut/action seams.
- For each owner, record construction site, writer/mutation entry points, keyboard/menu/toolbar bindings, semantic Registry bridge usage, project-state impact, focused tests, and whether it is in SceneViewport scope (already retired), Inspector scope, or another adapter.
- Keep Runtime L0-L4 Qt-free and preserve `.pond`, AI command registry, Inspector command binding, SR2D seams, package manifests, and project manifests.
- Preserve unrelated dirty work. Do not stage, commit, reset, restore, clean, or delete it.

## Required evidence

1. Reproducible source inventory with paths and line references for all remaining local-history ownership.
2. AST or equivalent call-site evidence distinguishing construction, `execute`, `undo`, and `redo` paths from comments/tests.
3. Focused existing-test evidence for the selected next slice, including its current semantic boundary or lack thereof.
4. A written decision naming exactly one next implementation gate, with a bounded file/test scope and an explicit reason other owners are out of scope.
5. Update `docs/mainline_status.md`, `docs/INDEX.md`, and this fresh-session prompt when the inventory decision closes. Do not modify `CONTEXT.md` until its original historical content is externally restored.

## Completion evidence

### Reproducible Runtime inventory (fresh 2026-07-31)

- An AST pass over every versioned Runtime Python module, decoding BOM-bearing sources with `utf-8-sig`, found exactly one production `CommandStack()` construction and one direct legacy call:
  - `core/VitaLoom/docks/inspector.py:232` assigns `self.command_stack = CommandStack()`.
  - `core/VitaLoom/docks/inspector.py:1617` calls `self.command_stack.execute(command)`.
- The same AST pass found no production Runtime assignment or constructor for `context.command_stack`. Its only Runtime reads are `builtin/editor_extensions/standard_ui_plugin.py:508` and `:516`; those are compatibility reads for `undo()`/`redo()`, not an owned stack.
- `memory_editor.py` and `docks/memory_editor.py` contain only descriptive `CommandStack` text. `commands/command.py` is the legacy stack definition; Registry `_undo_stack`/`_redo_stack` remains the separate Qt-free semantic authority and is not classified as a UI-host local owner.

### Authority map

| Surface | Construction / dispatch | Mutation authority and scope | Evidence-backed classification |
|---|---|---|---|
| SceneViewport | Retired in E170 | Focused Ctrl+Z/Ctrl+Y directly runs `command.undo` / `command.redo` and rehydrates with `scene.open` | No local owner remains |
| InspectorPanel | Owns `CommandStack` at `inspector.py:232`; fallback executes at `:1617` | Scene-backed entity fields first run Registry commands: `transform.set` for position axes, `script.set_property` for script fields, and `entity.set_property` otherwise (`:1426-1487`), then refresh canonical `.pond` through `scene.open` (`:1343-1368`) | Mixed adapter: semantic for identified loaded-scene entities; legacy local fallback for connection/node/non-scene-backed object writes (`:1489-1603`) |
| StandardUIPlugin Undo/Redo | Menu contributions `standard_ui.menu.undo`/`.redo` bind Ctrl+Z/Ctrl+Y to `plugin.standard_ui.undo`/`.redo` (`standard_ui_plugin.py:103-110`); LegacyEditorPluginAdapter invokes their Registry command IDs (`legacy_editor_plugin_adapter.py:505-531`) | The plugin handlers read `getattr(self.context, "command_stack", None)` and call `undo`/`redo` (`standard_ui_plugin.py:507-521`). No production Runtime injects this attribute; current positive behavior is test-only injected `Stack` (`test_standard_ui_menu_toolbar_contribution_lifecycle.py:295-331`) | Runtime-reachable stale dispatcher with no owned/injected production authority; selected next slice |

### Focused proof

- `QT_QPA_PLATFORM=offscreen .venv/python.exe -B -m pytest -q tests/test_inspector_command_binding.py tests/test_inspector_property_mapping.py tests/test_script_property_edit.py tests/test_command_stack_behavior.py tests/test_standard_ui_menu_toolbar_contribution_lifecycle.py` passed: **32 passed in 2.39s**.
- This proves the current Inspector command-binding shapes, current legacy stack behavior, and the real Standard UI contribution lifecycle before any migration. It does not prove whole-editor unified history.
- No code migration occurred in E171. Full-suite execution was intentionally not run for this bounded inventory phase. `CONTEXT.md` remains untouched because its former content needs external-history recovery.

## Decision and one next gate

Exactly one next gate: **E172 -- Standard UI Semantic Undo/Redo Dispatch Migration**.

Bounded implementation scope: replace `StandardUIPlugin.undo()` and `.redo()` local `context.command_stack` compatibility dispatch with direct Qt-free Registry `command.undo` / `command.redo` dispatch, preserve canonical `scene.open` rehydration after successful history operations, update the Standard UI lifecycle tests and AI command audit schema/status as needed, then prove the real menu contribution action reaches semantic history. Inspector remains explicitly out of scope: it is the only remaining real local-stack owner, but its non-scene-backed connection/node fallback requires a separate mutation-contract inventory rather than a speculative broad retirement.
