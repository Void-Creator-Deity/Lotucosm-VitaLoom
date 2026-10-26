# Phase E170 -- SceneViewport Local CommandStack Retirement

Date: 2026-07-31
Status: complete

## Previous gate

E169 moved the remaining SceneViewport durable project mutations (node create/delete, single and multi-node transforms, connection create/delete, and event-driven node creation) to Qt-free Registry commands with canonical `.pond` rehydration. Its one next gate was an exact inventory of any remaining SceneViewport local `CommandStack` ownership before selecting another migration.

## Discovery evidence

- An AST inventory of `scene_viewport.py` finds exactly four runtime calls on `self.command_stack`: `can_undo`, `undo`, `can_redo`, and `redo` at the focused-keyboard fallback. There is no `self.command_stack.execute(...)` call.
- Repository search finds no external production writer to `SceneViewport.command_stack`. The remaining `CommandStack.execute` hit in the editor is Inspector-owned and outside this phase.
- Current tests prove semantic viewport commands do not execute the local stack. The sole local-history test manually injects a synthetic `_LegacyHistoryRecord`; it is a compatibility simulation, not proof of a current production mutation entry point.
- Non-project interactions (selection, pan, zoom, grid/snap display, hover, connection preview) remain UI state, not durable `.pond` project history. Asset drop already uses `asset.import` and `scene.open`.

## Objective

Retire the now-orphaned local `CommandStack` from SceneViewport. Focused Ctrl+Z/Ctrl+Y must route directly through the Qt-free global semantic command history and rehydrate canonical scene state. Remove the synthetic local-stack compatibility assumption instead of preserving a dead second history authority.

## Scope and invariants

- Edit only the SceneViewport local-history seam and its focused tests/docs in this phase.
- Do not migrate Inspector, alter `.pond` schema, or claim all-editor unified undo/redo. `unified_undo_redo_runtime` may remain false while other UI hosts retain local history.
- Preserve public shortcut behavior: a focused SceneViewport Ctrl+Z/Ctrl+Y dispatches `command.undo`/`command.redo` through Registry, with existing failure handling and `scene.open` rehydration.
- Keep Runtime L0-L4 Qt-free; no Registry command may depend on QWidget, QPainter, `Node`, or `ConnectionLine`.
- Preserve unrelated dirty work and do not stage, commit, reset, restore, clean, or delete it.

## Implementation plan

1. Remove the `CommandStack` import, construction, and local-first branch from `SceneViewport`.
2. Make the focused keyboard helper a direct semantic-history route (or inline it while preserving a clear callable seam).
3. Update targeted tests: retain proof that Ctrl+Z/Ctrl+Y rehydrate Runtime history; replace synthetic local-record precedence with proof that no local CommandStack surface remains.
4. Update the AI command audit only if its declared route/status schema changes; do not promote `unified_undo_redo_runtime` without a whole-editor evidence audit.

## Required proof

- Static inventory proves `scene_viewport.py` has no `CommandStack` import, construction, attribute, or local execute/undo/redo route.
- Offscreen focused keyboard interaction proves undo/redo of a real semantic node transform changes disk and viewport state through Registry history.
- Targeted viewport semantic suites pass, plus audit/core/GUI boundary checks and `git diff --check`.
- Record skipped full-suite/environment evidence honestly. `CONTEXT.md` is currently awaiting restoration from external history after an accidental truncation; do not rewrite its lost historical content from inference.

## Completion evidence

- Removed the SceneViewport `CommandStack` import, instance, and compatibility fallback. `_run_viewport_keyboard_history_command()` now delegates directly to `_run_global_scene_history_command()`.
- Updated node, event-node, multi-node, and connection semantic-history tests so they prove no SceneViewport local history attribute remains. Focused Ctrl+Z/Ctrl+Y is exercised against real Registry-backed transform history and canonical `.pond` rehydration.
- Updated `tools/check_ai_command_audit_status.py` to schema version 3: it now reports `viewport_local_command_stack_retired=true` instead of the retired legacy-fallback flag. `unified_undo_redo_runtime` remains false because Inspector and other UI-host owners are not yet audited or migrated.
- Fresh proof on 2026-07-31: the E169/E170 target collection passed `33 passed, 3 subtests passed in 2.55s`; AI command audit, core-boundary check, GUI-boundary check, static no-symbol inventory, and `git diff --check` passed. `git diff --check` emitted only pre-existing LF/CRLF warnings.
- Full-suite execution was intentionally not run in this focused migration phase. `CONTEXT.md` remains untouched while its lost history awaits external recovery.

## Completion and one next gate

Do not mark this phase complete until the local stack has been removed and the above proof is fresh. Exactly one next gate after completion: **inventory Inspector and other remaining UI-host local history owners, then choose the next authority-retirement slice from evidence.**
