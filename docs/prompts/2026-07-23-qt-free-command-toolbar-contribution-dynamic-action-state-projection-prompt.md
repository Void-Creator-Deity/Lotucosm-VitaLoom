# Phase E34 Fresh-Session Prompt -- Qt-Free Command Toolbar Contribution and Dynamic Action-State Projection

Date: 2026-07-23
Status: closed

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0003, the completed E33 plan, and the E34 plan before editing code.

## Architecture authority

```text
L0 FrameCore
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin and recursive downstream Plugin Host)
   └─ versions/1.0.0/runtime
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

The engine is the L1 plugin and is itself a derived recursive plugin framework. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` are the authorities. PyQt6/QPainter/Qt OpenGL, `PluginLoader`, `LegacyEditorPluginAdapter`, `EditorKernel`, and `LayoutManager` are current/legacy Host Adapter details. Do not add a second Host, registry, catalog, manifest authority, composition root, UI DSL/framework, renderer framework, peer L1 plugin, or replacement shell. Do not migrate to Unity/Godot/Unreal/Electron.

## E33 closure truth

E33 is complete with a real Qt-free `menu_command` contract and `LocalizationUIPlugin` vertical slice. `RuntimePluginHost` owns validation/cached observations, `ManualPluginReloadHost` refreshes the same metadata, and only `LegacyEditorPluginAdapter` creates live Qt actions. Final evidence is `1430 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and four green guardrails. Signature-only collection remains blocked by missing `cryptography` in the exact repository `.venv`.

## Unique Gate

**E34 Task 1 -- audit the `StandardUIPlugin` simulation toolbar/state slice and establish red architecture tests.**

1. Trace play/stop toolbar actions, `simulation.toggle` / `simulation.stop`, authoritative transport state, localization, icon/shortcut behavior, ownership, refresh, reload, and cleanup.
2. Separate stable engine/plugin facts from Qt-only action/button/icon construction.
3. Add red tests for the minimum toolbar command contribution and only the state reference proven necessary by the real slice.
4. Reject live callbacks, arbitrary state callables, Qt/native objects, plugin instances, kernel/layout objects, forged ownership, duplicate ids, and alternate registries.
5. Do not design a general widget tree, expression language, dock/viewport schema, or replacement shell.
6. Preserve `.pond`, AI command/Inspector, SR2D, manifests, L4 Project World, Player/export, reload/startup/shutdown, viewport parity, and all protected dirty work.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, or delete unrelated files. The whole-engine objective remains active; do not claim toolbar migration, replacement Host readiness, or the entire engine complete before proof.

## Closure

E34 completed on 2026-07-23. Evidence: red `13 failed, 6 passed`; E34 `20 passed`; focused `39 passed`; expanded `94 passed`; full non-signature `1450 passed, 34 skipped, 34 subtests passed in 162.35s`; Editor smoke `plugins=13/20`; four architecture guardrails green. Signature-only collection remains blocked by missing `cryptography` in the exact project `.venv`.

Do not resume the old Task 1 from this prompt. Continue from `docs/prompts/2026-07-23-qt-free-dock-contribution-host-owned-dock-surface-projection-prompt.md`, whose unique Gate is E35 Task 2 red tests for the bounded Inspector dock shell slice.
