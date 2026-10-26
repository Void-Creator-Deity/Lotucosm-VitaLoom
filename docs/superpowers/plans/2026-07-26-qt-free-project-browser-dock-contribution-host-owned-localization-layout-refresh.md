# Phase E37 -- Qt-Free ProjectBrowser Dock Contribution and Host-Owned Localization/Layout Refresh

Date: 2026-07-26
Status: complete
Completed: 2026-07-26

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the versioned product runtime boundary containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the Host authorities. `PluginLoader` is compatibility facade only. `LegacyEditorPluginAdapter` is the current PyQt Host Adapter. Reuse the existing `dock_surface` contribution Interface; do not create a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell.

## Previous Gate

E36 is complete for the bounded Hierarchy Dock shell and lifecycle slice. Evidence: red `4 failed, 1 passed`; focused `20 passed`; expanded `119 passed`; protected `169 passed`; fresh second full non-signature `1470 passed, 34 skipped, 34 subtests passed`; `compileall`; Editor smoke `plugins=13/20`; all four guardrails green. Signature-only remains blocked by missing `cryptography` in the exact repository `.venv`.

## Audit target

`ProjectBrowserPlugin` is the next bounded Dock slice. Its stable shell facts are Project Dock identity, localized title, bottom placement, default visibility, and current close/float/move behavior. Its current `language_changed` handler directly reaches through `kernel.layout_manager`, removes the Dock, reconstructs `ProjectPanel`, and adds the Dock again. That mixes shell refresh authority with content construction, risks losing panel identity/state and signal connections, and duplicates work already owned by `LegacyEditorPluginAdapter`.

The plugin also owns four event subscriptions: `project_opened`, `create_asset`, `refresh_project_browser`, and `language_changed`. E37 must establish exact subscription ownership and failed-load rollback without changing canonical project/asset semantics.

## Tasks

### Task 1 -- Red projection, identity, and lifecycle tests

- Prove that ProjectBrowser declares exactly one `project_browser.surface` Qt-free `dock_surface` contribution containing stable shell facts only.
- Prove the current Adapter projects exactly one Project Dock and treats declarative configuration as authoritative rather than calling legacy `get_dock_config()` for shell facts.
- Prove `language_changed` refreshes the Dock title in place without `LayoutManager.remove_dock()`, `LayoutManager.add_dock()`, Dock reconstruction, ProjectPanel replacement, duplicate signal connection, or layout identity loss.
- Prove exact cleanup of all owned event subscriptions across unload/reload/shutdown and rollback of already-created subscriptions when a later subscription fails.
- Prove protected behavior remains unchanged for `project_opened`, `refresh_project_browser`, `scene.open`, `asset.create`, Project World scoping, layout persistence, and legacy/community fallback.

### Task 2 -- Deepen ownership at the existing seam

- Add only the ProjectBrowser `dock_surface` declaration and the minimum lifecycle bookkeeping required by the red tests.
- Keep concrete `ProjectPanel`/`QDockWidget` construction as the candid legacy content bridge; do not pretend cross-Host content parity exists.
- Let `LegacyEditorPluginAdapter` own shell title refresh from `refresh_events`. If ProjectBrowser content has a real localization Interface, refresh content through that Interface only; otherwise preserve the existing panel instance rather than recreating it.
- Keep `scene.open` and `asset.create` in the canonical Command Registry flow. Do not add parallel project, scene, asset, event, or layout authorities.

### Task 3 -- Regression and closure

- Run focused E37 red/green tests, Dock contract/projection regression, expanded Host/lifecycle/layout/localization/startup regression, and protected Project World/`.pond`/AI Command/Inspector/SR2D/viewport/Player/export/manifest regression.
- Run the full non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact result; do not install dependencies silently.
- Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md` only after fresh evidence exists.
- Name exactly one next Gate. Do not widen E37 into Console, PackageManager, viewport, theme, replacement Host selection, or whole-engine completion.

## Completion evidence

- Red baseline: the initial E37 contract/lifecycle slice produced `5 failed`; the first implementation made those tests `5 passed`.
- Real-Host correction: the first offscreen Editor smoke exposed a real initialization defect during `language_changed` (`ProjectPanel` had no `_icon_size_label`). A real-widget regression test reproduced it as `1 failed, 5 passed`; the label became a retained panel field and the final E37 test file is `6 passed in 0.23s`.
- Qt-free shell Interface: `ProjectBrowserPlugin` declares exactly one immutable `project_browser.surface` `dock_surface` and publishes `editor_contribution`. Declarative shell facts are authoritative; concrete `ProjectPanel`/`QDockWidget` construction remains the current legacy content bridge.
- Ownership and locality: the plugin owns one ordered four-event binding set (`project_opened`, `create_asset`, `refresh_project_browser`, and `language_changed`), releases exact callbacks, retries failed releases, and rolls back partial activation. `ProjectPanel` no longer subscribes to `project_opened` independently.
- Refresh behavior: `LegacyEditorPluginAdapter` owns the Dock title refresh in place. The plugin refreshes only ProjectPanel content through `retranslate_ui()`; Dock and ProjectPanel identity, selection-bearing widgets, and layout identity are preserved. No plugin-owned `LayoutManager.remove_dock()/add_dock()` cycle remains.
- Focused E37/Dock/project regression: `45 passed in 1.27s`. Expanded Host/lifecycle/layout/localization/startup regression: `140 passed in 2.87s`. Protected Project World/`.pond`/AI Command/Inspector/SR2D/viewport/Player/export/manifest/lifecycle regression: `327 passed, 16 skipped in 24.35s`.
- First full non-signature run: `1 failed, 1474 passed, 34 skipped, 34 subtests passed in 154.86s`; the only failure was the historical load-sensitive 1000-asset cold-build threshold at `10.544s > 10.0s`. Its isolated retry passed: `1 passed in 7.32s`. No threshold was widened.
- Fresh second full non-signature run: `1476 passed, 34 skipped, 34 subtests passed in 152.42s`. Modified Modules pass `compileall`; project plugin model, core boundaries, GUI boundaries, and release consistency are all green.
- Final real offscreen Editor smoke passes with `plugins=13/20`, zero discovery errors, one Project Dock, no Project Dock remove/add during localization, no runtime callback warning, and deterministic reverse shutdown/removal.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` in the exact repository `.venv`. No dependency was installed and signature verification remains unclaimed.

## Stable result and remaining debt

Stable in E37: ProjectBrowser shell declaration/projection, in-place Host-owned Dock localization, stable ProjectPanel identity, exact four-event ownership and failed-load rollback, single `project_opened` ownership, and protected project/asset semantics. Still legacy: concrete PyQt ProjectBrowser content construction. E37 does not prove replacement-Host content parity, complete Dock migration, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or whole-engine completion.

## Unique next Gate

**Phase E38 -- Qt-Free Console Dock Contribution and Exact Logging/Capability Adapter Lifecycle.** Migrate only the Console shell through the existing `dock_surface` Interface, remove plugin-owned Dock-title mutation, and prove exact `UI_CONSOLE_PANEL` capability plus logging-handler acquire/release behavior across create, failure, reload, unload, and shutdown. Preserve console output semantics, Project tabification, legacy/community fallback, and the current concrete PyQt content bridge. Do not widen into PackageManager, PS Experiment, SimulationControl, viewport, theme, or replacement-Host selection.

## Completion bar

E37 is complete only when the ProjectBrowser shell is declared Qt-free, the existing Adapter projects and localizes it in place, ProjectPanel identity survives language refresh, event ownership and failed-load rollback are exact, protected project/asset semantics remain green, and the full evidence chain closes.

E37 does not prove replacement-Host ProjectBrowser content parity, complete Dock migration, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or whole-engine completion.
