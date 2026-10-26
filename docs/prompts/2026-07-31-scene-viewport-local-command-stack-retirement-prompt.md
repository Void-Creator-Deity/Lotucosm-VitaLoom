# Fresh-session prompt -- E170 SceneViewport Local CommandStack Retirement

Date: 2026-07-31
Status: complete

Phase E170 is complete. Do not reintroduce a SceneViewport-local `CommandStack` or a local-first Ctrl+Z/Ctrl+Y compatibility branch.

## Verified completion state

- SceneViewport no longer imports, constructs, or references `CommandStack`.
- Focused Ctrl+Z/Ctrl+Y delegates directly to Qt-free Registry history through `_run_global_scene_history_command()`, preserving the existing canonical `scene.open` rehydration behavior.
- Targeted node, event-node, multi-node, and connection tests prove no SceneViewport local history surface remains while real semantic history still updates disk and viewport state.
- The AI command audit is schema version 3 and reports `viewport_keyboard_semantic_history=true`, `viewport_local_command_stack_retired=true`, and `unified_undo_redo_runtime=false`.
- Fresh 2026-07-31 proof: `33 passed, 3 subtests passed in 2.55s`; audit, core boundary, GUI boundary, static source inventory, and `git diff --check` passed (only pre-existing line-ending warnings).

## Exactly one next gate

Inventory Inspector and every other remaining UI-host local-history owner, record each mutation entry point and semantic/legacy authority boundary, then choose one evidence-backed authority-retirement slice. Do not claim unified editor undo/redo merely because SceneViewport is retired.

## Persistent constraints

- Keep Runtime L0-L4 Qt-free and preserve `.pond`, command registry, Inspector command binding, SR2D seams, and manifests.
- Preserve all unrelated dirty work; do not stage, commit, reset, restore, clean, or delete it.
- `CONTEXT.md` was accidentally truncated before this phase. Do not recreate or overwrite it from inference; wait for an external-history restoration before updating it.
