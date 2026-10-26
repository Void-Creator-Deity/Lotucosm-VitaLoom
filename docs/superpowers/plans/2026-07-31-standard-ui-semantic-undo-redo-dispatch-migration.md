# E172 Standard UI Semantic Undo/Redo Dispatch Migration

Date: 2026-07-31
Status: complete

## Previous gate

E171 completed a Runtime-wide UI-host local-history owner inventory. It proved that `InspectorPanel` is the only remaining production UI-host that constructs and executes the legacy `CommandStack`. The existing Standard UI Ctrl+Z/Ctrl+Y menu contributions are runtime-reachable, but their `StandardUIPlugin.undo()` and `.redo()` handlers only query `context.command_stack`; no versioned Runtime production code injects that attribute. This is a stale dispatcher, not a second history owner.

The E171 focused baseline passed: `32 passed in 2.39s` across Inspector binding/mapping/script behavior, legacy stack behavior, and Standard UI contribution lifecycle. `CONTEXT.md` remains accidentally truncated and must not be recreated from inference.

## Objective

Migrate the existing Standard UI undo/redo command handlers to the Qt-free shared Command Registry:

- dispatch `command.undo` and `command.redo` directly;
- retain the semantic envelope, including empty-history failures;
- after a successful history result that declares `result.scene_path`, invoke canonical `scene.open` rehydration;
- prove actual menu contribution actions enter this semantic route;
- update the AI command audit status without claiming unified whole-editor undo/redo.

## Non-goals and protected contracts

- Do not remove or redesign the Inspector local `CommandStack`; its non-scene-backed fallback needs a separate mutation-contract inventory.
- Do not alter `.pond` semantics, semantic command IDs, AI command registry flows, Inspector bindings, SR2D seams, manifests, or Runtime L0-L4 Qt-free contracts.
- Do not claim `unified_undo_redo_runtime=true`, whole-refactor completion, native/OpenGL readiness, WorldBridge readiness, or default unified Pond/replay.
- Do not modify, reconstruct, or infer missing content for `CONTEXT.md`.
- Do not stage, commit, reset, restore, clean, delete, or otherwise disturb unrelated existing worktree changes.

## Implementation plan

1. Record this plan and a fresh-session prompt before production migration.
2. Change `StandardUIPlugin.undo()` and `.redo()` to obtain the shared registry, run the matching semantic command, and return the Registry envelope unchanged.
3. Add a small private rehydration helper that only calls `scene.open` after `ok=true` and a nonblank returned `scene_path`; do not rehydrate after a failed history operation.
4. Replace test-only `context.command_stack` positive assertions with a recording semantic registry and exercise both direct plugin calls and the existing menu contribution action bridge.
5. Raise the audit schema only if static evidence is added, asserting Standard UI uses `command.undo`, `command.redo`, and canonical `scene.open`, while no longer containing `context.command_stack`.
6. Run focused pytest, audit, boundary, static-search, and whitespace checks. Record all commands, results, skips, and one next gate in the status board, plan, prompt, and index.

## Acceptance evidence

- Standard UI contains no `context.command_stack` compatibility path.
- `plugin.standard_ui.undo` dispatches `command.undo`; `plugin.standard_ui.redo` dispatches `command.redo`.
- Successful operations with a scene path dispatch exactly one canonical `scene.open` using that path.
- Failed/empty operations preserve their Registry failure envelope and do not dispatch `scene.open`.
- A real menu contribution action exercises the semantic path.
- Audit, targeted semantic undo/redo, durable project undo, core boundary, GUI boundary, static search, and `git diff --check` all pass or are explicitly documented as blocked/skipped.

## Verification commands

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_standard_ui_menu_toolbar_contribution_lifecycle.py `
  tests\test_ai_command_audit_status_tool.py `
  tests\test_ai_command_undo_redo_command_path.py `
  tests\test_ai_command_durable_project_undo.py
& '.\.venv\python.exe' -B tools\check_ai_command_audit_status.py
& '.\.venv\python.exe' -B tools\check_core_boundaries.py
& '.\.venv\python.exe' -B tools\check_gui_boundaries.py
rg -n 'context\.command_stack|command_stack' FrameCore\plugins\lotucosm-vitaloom\versions\1.0.0\runtime\builtin\editor_extensions\standard_ui_plugin.py
git diff --check
```

## Completion record

- `StandardUIPlugin.undo()` and `.redo()` now delegate directly to `get_command_registry().run("command.undo"|"command.redo", {})` through `_run_semantic_history_command()`; their Registry envelopes are returned unchanged.
- A successful history result with nonblank `result.scene_path` invokes canonical `scene.open`. Failed history envelopes, including `undo_empty`, are returned without rehydration.
- Standard UI lifecycle tests no longer inject `context.command_stack`. They prove direct undo/redo dispatch, success-only rehydration, failure passthrough, and a real Ctrl+Z contribution action path through `LegacyEditorPluginAdapter`.
- Audit schema v4 adds `standard_ui_semantic_history_dispatch`; it passed with that field true while `unified_undo_redo_runtime` remains false.
- Final targeted proof passed: `17 passed, 3 subtests passed in 1.28s` for Standard UI lifecycle, audit status, semantic undo/redo, and durable project undo tests. Audit, core-boundary, GUI-boundary, and Standard UI static no-local-stack searches passed. Scoped `git diff --check` for E172 code/test/audit files passed.
- Full-suite execution was intentionally skipped for this focused migration. Whole-worktree `git diff --check` remains nonzero because pre-existing `docs/INDEX.md` changes contain large trailing-whitespace sets; they were not modified or cleaned. `CONTEXT.md` remains untouched pending external-history recovery.

## Exactly one next gate

**E173 -- Inspector Non-Scene Local-Fallback Mutation-Contract Inventory.** Before retiring Inspector's remaining local `CommandStack`, inventory every non-scene-backed connection/node/object mutation entry point, determine whether a semantic Registry contract exists or must be designed, and select only one evidence-backed retirement slice.
