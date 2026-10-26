# Phase E168 -- SceneViewport Node/Connection Semantic Command-History Migration and Global Undo/Redo Interaction Proof

Date: 2026-07-31
Status: complete

## Previous gate

E167 selected the Qt-free `CommandRegistry` as the sole authority for supported project-semantic history and migrated a real generic Inspector entity-property slice. Its audit remains `unified_undo_redo_runtime=false` because SceneViewport node/connection operations still depend on a local Qt `CommandStack`.

## Objective

Migrate one coherent SceneViewport node/connection editing vertical slice from local UI-object commands to registered Qt-free semantic commands, then prove that the same canonical `.pond` mutation is reached by the viewport interaction and by global undo/redo without introducing a dual history authority.

## Required discovery before production edits

- Map every SceneViewport node/connection mutation, drag/preview state, local `CommandStack` command type, `.pond` persistence path, selection/refresh behavior, and existing registry command overlap.
- Separate durable project semantics from transient graphics-item state. No QWidget, QGraphicsItem, callback, canvas, or OpenGL context may enter the registry payload or inverse record.
- Identify the smallest user-visible node or connection operation whose forward payload and inverse can be JSON-safe, deterministic, and compatible with existing `.pond` scenes.
- Run the existing viewport, command-history, persistence, core-boundary, and GUI-boundary checks before changing behavior.

## Implementation requirements

- Add or extend Qt-free registered commands for the selected node/connection semantic operation, including deterministic validation, mutation, inverse/redo record, durable audit compatibility, and explicit failure behavior.
- Make the SceneViewport interaction invoke the registered command for that operation. On success, rehydrate or synchronize from canonical `.pond`; do not execute a duplicate local `CommandStack` mutation.
- Keep local stack use only for unmigrated or genuinely transient UI state, and document exact remaining paths.
- Ensure global menu/toolbar/shortcut undo and redo reaches the same semantic record and refreshes the viewport/scene truth.
- Preserve `.pond`, Inspector command binding, AI registry flows, SR2D seams, package/project manifests, and the Qt-free L0 boundary.

## Completion evidence

- Deterministic tests prove viewport interaction -> semantic command -> `.pond`, global undo -> prior canonical state, global redo -> restored canonical state, and fresh-registry durable undo/redo where the operation is eligible.
- Tests prove the migrated interaction does not call local `CommandStack.execute` for its semantic mutation and reject invalid payloads without advancing history.
- Demonstrate viewport parity with a real offscreen interaction smoke or equivalent rendering/state proof, plus targeted regressions, command audit, core/GUI boundary checks, and `git diff --check`.
- Record all skipped checks, exact command outputs, and remaining unmigrated history boundaries in `docs/mainline_status.md`.

## Constraints

- Keep `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` as the product runtime boundary and FrameCore L0 Qt-free.
- Do not change `.pond` semantics, migrate the editor to another UI shell, or make the legacy UI host history authority.
- QPainter stays default. No claim of default-ready OpenGL, native acceleration, replay authority, unified Pond, or WorldBridge readiness is permitted.
- Preserve unrelated dirty work; do not stage, commit, push, reset, restore, clean, or delete it.

## Single next gate after E168

Name exactly one next gate only after E168 has complete evidence.


## Completion decision

E168 selected and completed the smallest coherent durable vertical slice: **single-node drag**. Its preview remains transient in the PyQt adapter; mouse release performs one JSON-safe `transform.set` through `CommandRegistry`, then reopens the canonical `.pond`. It never duplicates that semantic mutation in `CommandStack`.

The pre-close interaction review found an ownership hazard: local-stack operations still exist for multi-node movement, connection creation/deletion, and legacy event entry points. An unconditional focused-viewport Ctrl+Z/Ctrl+Y could therefore skip a newer local record and undo an older Registry record. The completed transition policy is deliberately non-merging: while the focused viewport has a matching local undo/redo record it consumes that record; only when that direction is locally empty does it call `command.undo`/`command.redo`. Menu and toolbar actions remain the global semantic-history entry points. This preserves legacy behavior without claiming one ordered history.

## Completion evidence

- Offscreen real interaction proof covers mouse press/move/release single-node drag -> `transform.set` -> canonical `.pond` -> `scene.open` rehydrate, followed by global menu actions and focused viewport Ctrl+Z/Ctrl+Y. It also proves the migrated drag does not execute the local stack and failed semantic mutation restores the preview without success signals.
- The added transition regression proves a focused viewport's unmigrated local undo and redo are consumed before any global semantic history call.
- Final targeted suite: `43 passed in 3.00s`.
- AI command audit reports `viewport_single_node_drag_semantic_route=true`, `viewport_keyboard_semantic_history=true`, and `viewport_keyboard_legacy_history_fallback=true`, while correctly retaining `command_stack.registry_integrated=false` and `unified_undo_redo_runtime=false`.
- `check_core_boundaries.py` and `check_gui_boundaries.py` both passed; `git diff --check` exited 0 with only pre-existing LF/CRLF warnings.
- Full `.venv` collection remains environment-limited: its `cryptography` dependency is missing. The non-signature run reached `1948 passed, 34 skipped, 34 subtests passed` but had four order-dependent `test_project_open_switch` failures; that module passed `6 passed` in isolated execution, so the result is recorded as cross-test-state pollution rather than an E168 product failure. `D:\app\anaconda3\python.exe` provides `cryptography 44.0.1`; `tests/test_package_signature_warn_only.py` passed there (`2 passed in 0.23s`).

## Remaining boundary

E168 is complete, but unified runtime history is not. Multi-node movement, connection create/delete, and legacy event-driven node add/delete paths still have local `CommandStack` semantics. The focused-keyboard fallback is a compatibility boundary, not a merged or durable representation of those UI-object commands. `.pond`, AI registry, Inspector binding, SR2D public seams, Qt-free L0-L4, QPainter-default status, and package/project manifests remain unchanged.

## Single next gate

**E169 -- SceneViewport Remaining Node/Connection Semantic Command-History Migration**.
