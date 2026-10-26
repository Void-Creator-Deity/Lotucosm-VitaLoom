# Phase E33 Fresh-Session Prompt -- Qt-Free Editor Contribution Contract and Replacement Host Adapter Migration Readiness

Date: 2026-07-23
Status: closed -- E33 completed; continue with the E34 prompt.

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0003, the completed E32 plan, and the E33 plan before editing code.

## Architecture authority

```text
L0 FrameCore
└─ L1 lotucosm-vitaloom (sole engine/product plugin and recursive downstream Plugin Host)
   └─ versions/1.0.0/runtime
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

The engine is not a PyQt project. PyQt6/QPainter/Qt OpenGL, `EditorKernel`, `LayoutManager`, `PluginLoader`, and `LegacyEditorPluginAdapter` are legacy/current Host Adapter details. Keep `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` as the only authorities. Do not create a second Host, registry, manifest authority, composition root, UI framework, renderer framework, or peer FrameCore plugin. Do not choose or migrate to Unity/Godot/Unreal/Electron.

## E32 closure truth

E32 is complete with real current-context pixels, logical parity, interaction/recreation/teardown proof, comparable policy evidence, final full non-signature `1412 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and all four guardrails green. `auto` remains QPainter. Signature-only remains blocked by missing `cryptography`.

## Unique Gate

**E33 Task 1 -- inventory contribution shapes and establish red architecture tests.**

1. Inventory all currently active builtin editor contributions and their lifecycle/ownership/localization/cleanup behavior.
2. Separate stable engine/plugin facts from Qt-only widget/action construction details.
3. Write/update the E33 plan with the exact first vertical slice if the inventory changes the current hypothesis.
4. Add red tests for a future contribution catalog that rejects Qt objects, live callbacks, live plugin instances, `EditorKernel`, and `LayoutManager`; requires canonical plugin ownership, deterministic ordering, JSON-safe observation, and Qt-free imports.
5. Do not implement a speculative universal UI schema before the red tests and inventory establish the minimum Interface.
6. Preserve `.pond`, AI command/Inspector, SR2D, manifests, L4 Project World addons, Player/export, reload/startup/shutdown, viewport parity, and the protected dirty worktree.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, or delete unrelated files. The persistent objective `彻底完善` remains active; do not claim the replacement Host or whole engine complete.
