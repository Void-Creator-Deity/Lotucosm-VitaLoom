# Phase E26 -- Qt-free Plugin Host Control/Observation Interface and Legacy Editor Extension Consumer Decoupling

## Resume point

E25 is complete. The authoritative architecture remains:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       sole engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 capability/domain packages
            -> L3 engine extensions / Host Adapters
            -> L4 Project World addons
```

The Qt-free `NestedPluginHost` composes exactly one `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` over one exact registry. `LegacyEditorPluginAdapter` is the concrete PyQt-era contribution Adapter. `PluginLoader` is a compatibility facade, and Editor close now consumes a single shutdown Interface rather than enumerating the registry.

E25 evidence to preserve:

- red baseline: `16 failed, 1 passed`;
- focused: `17 passed`;
- expanded lifecycle/Loader/Editor: `88 passed, 1 skipped in 2.33s`;
- cross-domain compatibility: `146 passed in 16.57s`;
- full non-signature: `1283 passed, 25 skipped, 34 subtests passed in 125.53s`;
- project/core/gui/release guardrails all passed;
- signature-only verification remains blocked by missing `cryptography`.

## Concentrated remaining friction

Several legacy Editor extensions and smoke paths still reach `kernel.plugin_loader` directly and depend on mutable compatibility dictionaries or concrete facade methods. Current examples include plugin manager/runtime operations, hot reload UI, Editor smoke diagnostics, localization contribution refresh, and package-manager runtime lookups.

This leaks the compatibility facade as if it were engine authority. It also forces consumers to know registry representation, protection/scope rules, and concrete Editor composition details.

## E26 single objective

Deepen the existing Qt-free nested Host/operator seams into deterministic observation and validated control Interfaces, then migrate the first concrete legacy Editor consumers away from direct `kernel.plugin_loader` state access without creating a second registry or lifecycle authority.

Prioritize a bounded first slice:

1. plugin manager and `PluginRuntimeOpsMixin`;
2. hot-reload UI;
3. Editor smoke/startup diagnostics;
4. any shared helper required by those consumers.

Audit localization and package-manager accesses, but only migrate them in E26 when the new Interface remains narrow. Concrete menu/widget contribution refresh belongs in `LegacyEditorPluginAdapter`, not in a Qt-free Host Interface.

## Required first actions

1. Write the E26 phase plan before production edits.
2. Inventory every production access to `kernel.plugin_loader`, `loaded_plugins`, `plugin_registry`, `failed_plugins`, `discovery_errors`, scope/protection queries, reload/unload, and Project-scoped sync.
3. Classify each access as:
   - Qt-free observation fact;
   - validated runtime control;
   - Project World command/orchestration;
   - concrete legacy Editor contribution behavior;
   - temporary compatibility seam.
4. Add red tests for deterministic JSON-safe observation, protected/scope facts, reload/unload delegation, no mutable registry exposure, and migrated consumers.
5. Extend an existing Host/operator seam where possible. Do not bind a second global registry or invent a parallel plugin manager.

## Required architecture properties

- Keep `FrameCore` as the only L0 root and `lotucosm-vitaloom` as the sole L1 engine/product plugin and recursive downstream plugin Host.
- Keep `versions/1.0.0/runtime` as the product runtime implementation boundary.
- Observation results must be deterministic, JSON-safe facts: catalog/active IDs, scope/protection, failures, discovery/lifecycle/reload status, and stable diagnostics as needed. Do not return live plugin objects or mutable registry dictionaries.
- Controls must delegate to the existing Runtime/Nested/Project/Reload Host authorities and preserve planner, protection, failure, report, command-owner, Inspector, Player/export, and L4 lifecycle semantics.
- Prefer one deep Interface with leverage and locality over shallow per-screen wrappers.
- Keep concrete Dock/Viewport/Menu/Toolbar/Theme refresh and widget access in `LegacyEditorPluginAdapter` or another concrete legacy Host Adapter seam.
- Preserve intentional external compatibility aliases until production consumers and tests prove a safe deprecation path; do not delete them broadly in the first patch.

## Forbidden directions

- no Unity/Godot/Unreal/Electron migration;
- no replacement UI shell, renderer rewrite, or generic UI framework;
- no second registry, composition root, lifecycle/reload planner, plugin hierarchy, manifest authority, or activation schema;
- no Qt/PyQt/EditorKernel/LayoutManager imports in Qt-free Host Modules;
- no runtime activation god context and no exposure of live plugin objects through the new Interface;
- no weakening of `.pond`, AI command registry, Inspector binding, SR2D seams, package/project manifests, Player/export, Project World L4 lifecycle, or shutdown fail-closed semantics;
- no dependency installation for the known `cryptography` blocker;
- no Git reset, restore, clean, stage, commit, or deletion of unrelated migration work.

Close E26 with focused consumer tests, cross-domain regressions, full non-signature verification, all four architecture guardrails, truthful blocker recording, status/index/context updates, and exactly one next Gate.
