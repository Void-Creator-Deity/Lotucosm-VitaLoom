# Phase E24 -- Legacy Editor Plugin Contribution Adapter Extraction and PluginLoader Compatibility Facade

## Resume point

E23 is complete. The architecture is still:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       sole engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon
```

The Qt-free `NestedPluginHost` is now the L1 version-runtime composition root. It constructs exactly one `RuntimePluginHost` and composes `ProjectScopedPluginHost` plus `ManualPluginReloadHost` over the same registry. Legacy `PluginLoader` constructs only that composition root and preserves compatibility aliases/delegates.

The remaining concentrated friction is concrete legacy Editor behavior still implemented directly on `PluginLoader`: activation-context projection, Dock/Viewport/Menu/Theme publication, command ownership, `on_editor_ready()`, kernel load/unload signals, UI cleanup, and layout settling. This behavior is a concrete PyQt-era Host Adapter, not nested plugin framework authority.

## E24 single objective

Extract the concrete legacy Editor plugin contribution lifecycle into an explicit Adapter satisfying the existing Qt-free `RuntimePluginHostAdapter` seam, and reduce `PluginLoader` to a narrow compatibility facade over `NestedPluginHost` plus that Adapter.

A likely Module location is:

```text
core/VitaLoom/kernel/legacy_editor_plugin_adapter.py
```

Choose the final name in the E24 plan after auditing existing vocabulary and consumers. The Adapter may depend on the legacy Editor kernel/layout/theme/plugin Interfaces; the Qt-free E20-E23 Host Modules must not.

## Required first actions

1. Write the E24 phase plan before production edits.
2. Inventory every remaining `PluginLoader` method and caller, classifying it as:
   - nested Host compatibility delegate/observation alias;
   - concrete legacy Editor Adapter responsibility;
   - temporary patch seam that tests or external plugins still require.
3. Add red tests for a standalone concrete Editor Adapter covering contribution publication/removal order, command exact ownership, editor-ready failure isolation, kernel signals, layout-unavailable behavior, and layout settling.
4. Add static/behavioral tests proving `NestedPluginHost` receives the concrete Adapter rather than `PluginLoader`, while old Loader methods/attributes remain compatible where required.

## Required architecture properties

- Keep `FrameCore` as the only L0 root and `lotucosm-vitaloom` as the sole L1 engine/product plugin and recursive plugin Host.
- Keep `versions/1.0.0/runtime` as the product runtime implementation boundary.
- Keep `RuntimePluginHostAdapter` Qt-free. The legacy Editor Adapter is one concrete Adapter at that seam; `NullRuntimePluginHostAdapter` remains the real headless Adapter.
- Preserve runtime callback order: plugin `on_load` before concrete contribution publication; concrete cleanup before `on_unload`; command ownership release after successful unload callback; kernel unload signal after registry deactivation.
- Preserve `.pond`, activation metadata/context behavior, AI command registry flows, Inspector command binding, SR2D public seams, package/project manifests, Player/export semantics, L3/L4 lifecycle, operator recovery, and strict JSON reports.
- Preserve intentional compatibility seams such as Loader state aliases, public delegates, and patchable `_instantiate_plugin_from_file()` unless tests prove a narrower equivalent.
- Prefer one deep Adapter Interface with concentrated implementation and deterministic tests; do not create one shallow Module per contribution type.

## Forbidden directions

- no Unity/Godot/Unreal/Electron migration;
- no replacement UI shell, generic UI framework, or renderer rewrite in E24;
- no Qt/EditorKernel/LayoutManager/legacy plugin Interface imports in `runtime_plugin_host.py`, `project_scoped_plugin_host.py`, `manual_plugin_reload_host.py`, or `nested_plugin_host.py`;
- no second registry, composition root, plugin hierarchy, manifest authority, activation schema, lifecycle planner, or reload planner;
- no weakening of command, Inspector, Player, export, Project World, package, SR2D, or plugin compatibility behavior;
- no dependency installation for the known `cryptography` blocker;
- no Git reset, restore, clean, stage, commit, or deletion of unrelated migration work.

## E23 evidence to preserve

- red baseline: `7 failed`;
- final focused suite: `45 passed in 1.14s`;
- expanded regression: `145 passed, 1 skipped in 11.09s`;
- final full non-signature suite: `1258 passed, 25 skipped, 34 subtests passed in 120.27s`;
- project/core/gui/release guardrails all passed;
- signature-only collection remains blocked by missing `cryptography`.

Close E24 with focused Adapter tests, architecture guardrails, a full non-signature run, truthful blocker recording, status/index/context updates, and exactly one next Gate.
