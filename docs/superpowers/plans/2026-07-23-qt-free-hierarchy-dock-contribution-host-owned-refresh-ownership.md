# Phase E36 -- Qt-Free Hierarchy Dock Contribution and Host-Owned Hierarchy Refresh Ownership

Date: 2026-07-23
Status: complete
Completed: 2026-07-26

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ itself is the recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (versioned product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

`NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the only Host authorities. `LegacyEditorPluginAdapter` is the current PyQt Host Adapter. The existing `dock_surface` contribution Interface is the only editor contribution seam. Do not add a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell.

## Previous Gate

E35 is complete for the bounded Inspector Dock shell. Its evidence is recorded in the E35 plan and mainline status: contract/legacy focus `67 passed`, expanded focus `185 passed`, protected regression `164 passed`, full non-signature `1465 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and four green architecture guardrails. Signature-only remains blocked by missing `cryptography` in the exact repository `.venv`.

## Audit target

`HierarchyPlugin` is the next bounded slice. The stable shell facts are already known: `Hierarchy`, localized title, left placement, visible by default, closable, and existing layout identity. The audited lifecycle debt is that `scene_hierarchy_updated` is subscribed but not unsubscribed. E36 must establish event ownership and refresh locality before widening the shell Interface.

## Tasks

### Task 1 -- Red lifecycle and projection tests

- Prove that Hierarchy declares one `hierarchy.surface` `dock_surface` contribution with only stable shell facts.
- Prove no duplicate Dock, no direct plugin-owned LayoutManager refresh, and exact owner cleanup on unload/reload/shutdown.
- Prove `scene_hierarchy_updated` is removed exactly once with no stale callback after unload or reload.
- Preserve legacy/community fallback, layout persistence, localization refresh, current Hierarchy content, and canonical scene/entity command/read-model authorities.

### Task 2 -- Deepen ownership without a second authority

- Reuse `editor_contribution_contract` and the existing `LegacyEditorPluginAdapter` projection path.
- Move only stable shell ownership and the event-subscription cleanup needed to close the audited stale-subscription gap; keep content construction in the current legacy bridge.
- Do not introduce a Hierarchy registry, event bus, Dock catalog, widget DSL, replacement shell, or duplicate scene authority.

### Task 3 -- Regression and closure

- Run focused E36 tests, protected `.pond`/AI command/Inspector/SR2D/viewport/Project World/Player/export/manifest/lifecycle regressions, full non-signature suite, compileall, four guardrails, real Editor smoke, and signature-only collection.
- Update the E36 plan, prompt, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md` only after fresh evidence exists.
- Name exactly one next Gate; do not claim full Dock migration or whole-engine completion.

## Completion evidence

- Red baseline: `4 failed, 1 passed`; the failures proved the missing contribution declaration, missing contribution capability publication, leaked `scene_hierarchy_updated` subscription, and missing failed-load rollback.
- Implementation: `HierarchyPlugin` declares exactly one `hierarchy.surface` `dock_surface`; `LegacyEditorPluginAdapter` remains the sole current Qt shell projection Adapter; Hierarchy content construction remains the legacy bridge.
- Lifecycle: the plugin records the six successful event bindings, releases each exact callback once, preserves failed unsubscriptions for retry, and rolls back already-subscribed callbacks if a later subscription fails.
- Refresh ownership: the Host Adapter refreshes the Dock title from declarative `refresh_events`; the plugin refreshes only the Hierarchy content header and no longer reaches into `LayoutManager` or mutates the Dock shell.
- Focused E36 and Dock contract/projection regression: `20 passed in 0.36s`.
- Expanded Host/lifecycle/layout/localization/startup regression: `119 passed in 5.10s`.
- Protected Project World/`.pond`/AI Command/Inspector/SR2D/viewport/Player/export/manifest/lifecycle regression: `169 passed in 15.81s`.
- First full non-signature run: `1 failed, 1469 passed, 34 skipped, 34 subtests passed in 215.26s`; the only failure was the historically load-sensitive 1000-asset cold-build threshold (`16.226s > 10.0s`), not a Hierarchy assertion. The isolated retry passed: `1 passed in 8.46s`. No threshold was widened.
- Three-repeat `asset_index_scale` benchmark recorded compound-case mean/min/max `17038.526/16610.491/17591.438 ms`; last cold build `5463.657 ms`, last full rebuild `2423.657 ms`, deterministic revision and registry projection parity both true.
- Fresh second full non-signature run: `1470 passed, 34 skipped, 34 subtests passed in 142.02s`.
- Modified Modules pass `compileall`. All four architecture guardrails are green: project plugin model, core boundaries, GUI boundaries, and release consistency.
- Real offscreen Editor smoke passes with `plugins=13/20`, zero discovery errors, one Hierarchy Dock, one Inspector Dock, layout exercise, and deterministic reverse shutdown/removal.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` in the exact repository `.venv`. No dependency was installed and signature verification remains unclaimed.

## Stable result and remaining debt

Stable in this Gate: the Hierarchy shell declaration/projection Interface, exact event-subscription ownership, failed-load rollback, Host-owned shell localization, content-header refresh locality, and compatibility with protected engine semantics. Still legacy: the concrete PyQt `HierarchyPanel`/`QDockWidget` construction. E36 does not prove replacement-Host content parity, complete Dock migration, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or whole-engine completion.

## Unique next Gate

**Phase E37 -- Qt-Free ProjectBrowser Dock Contribution and Host-Owned Localization/Layout Refresh.** Reuse the existing `dock_surface` Interface for the bounded ProjectBrowser shell and eliminate its direct `LayoutManager.remove_dock()/add_dock()` language-refresh cycle while preserving ProjectPanel identity, project/asset events, `scene.open`, `asset.create`, Project World scope, layout identity, legacy/community fallback, and exact lifecycle ownership. Do not widen into Console, PackageManager, viewport, theme, or a replacement shell.

## Completion bar

E36 is complete only when Hierarchy shell facts are validated Qt-free, the current Adapter projects them with real content and exact lifecycle ownership, `scene_hierarchy_updated` has no stale subscription after unload/reload, legacy/community compatibility remains green, and the full evidence chain closes.

E36 does not prove replacement Host implementation/parity, viewport/theme migration, native GPU geometry/OpenGL default readiness, signature provisioning, or whole-engine completion.
