# Fresh-session prompt -- E171 UI-Host Local-History Owner Inventory and Authority-Retirement Slice Selection

Date: 2026-07-31
Status: complete

Phase E171 is complete. Do not repeat its owner discovery as though the whole editor had unified undo/redo.

## Verified completion state

- A fresh AST pass over versioned Runtime code found exactly one production legacy `CommandStack` owner: `InspectorPanel` constructs it at `core/VitaLoom/docks/inspector.py:232` and executes fallback commands at `:1617`.
- Inspector scene-backed entities already prefer Qt-free Registry authority: positions use `transform.set`, script fields use `script.set_property`, and other public fields use `entity.set_property`, followed by canonical `scene.open` rehydration. Its local stack remains only for non-scene-backed/legacy UI objects such as connections and nodes.
- Standard UI menu/toolbar Ctrl+Z/Ctrl+Y is a real Runtime contribution path, but `StandardUIPlugin.undo()`/`.redo()` only reads `context.command_stack`; no versioned Runtime source injects that attribute. The known successful behavior is a test-injected compatibility stack, so this dispatcher is stale rather than a second discovered owner.
- Focused current-state proof passed: **32 passed in 2.39s** across Inspector binding/mapping/script tests, legacy stack behavior, and Standard UI contribution lifecycle.
- `unified_undo_redo_runtime` remains false. `CONTEXT.md` remains accidentally truncated and must only be restored from external history.

## Exactly one next gate

Implement **E172 -- Standard UI Semantic Undo/Redo Dispatch Migration**: route the existing Standard UI undo/redo contribution handlers directly to Registry `command.undo`/`command.redo`, rehydrate through canonical `scene.open` after a successful history operation, prove the real menu contribution action uses that route, and update audit/status evidence. Do not migrate Inspector in E172.

## Persistent constraints

- Keep Runtime L0-L4 Qt-free and preserve `.pond`, command registry, Inspector command binding, SR2D seams, and manifests.
- Do not claim whole-editor unified undo/redo, OpenGL/native readiness, WorldBridge readiness, or overall refactor completion.
- Preserve all unrelated dirty work; do not stage, commit, reset, restore, clean, or delete it.
- Do not recreate or overwrite `CONTEXT.md` from inference.
