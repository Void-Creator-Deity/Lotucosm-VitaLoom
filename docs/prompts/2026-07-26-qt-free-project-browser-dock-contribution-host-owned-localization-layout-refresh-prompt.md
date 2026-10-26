# Phase E37 Fresh-Session Prompt -- Qt-Free ProjectBrowser Dock Contribution and Host-Owned Localization/Layout Refresh

Date: 2026-07-26
Status: closed
Closed: 2026-07-26

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E36 plan, and the E37 plan before editing code.

## Non-negotiable architecture

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` is the versioned product runtime boundary. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain Host authorities. `PluginLoader` remains a compatibility facade. PyQt6/QPainter/Qt OpenGL and `LegacyEditorPluginAdapter` are current/legacy Host Adapter details, not the future engine-plugin authority.

Do not create a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell. Reuse the existing `dock_surface` Interface and Adapter projection path.

## E36 closure truth

E36 completed the bounded Hierarchy shell/lifecycle slice: one Qt-free contribution, Host-owned Dock title refresh, plugin-owned content-header refresh, exact six-event cleanup, and failed-load subscription rollback. Fresh evidence includes focused `20 passed`, expanded `119 passed`, protected `169 passed`, full non-signature `1470 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, `compileall`, and four green guardrails. Signature-only remains blocked by missing `cryptography` in the repository `.venv`.

## Unique Gate

1. Write red tests proving one `project_browser.surface` declaration, one projected Dock, declarative shell authority, in-place language refresh, preserved ProjectPanel identity, exact four-event cleanup, and failed-load rollback.
2. Remove ProjectBrowser's direct `LayoutManager.remove_dock()/add_dock()` language-refresh cycle by reusing Host-owned `dock_surface.refresh_events` projection.
3. Preserve `project_opened`, `refresh_project_browser`, `scene.open`, `asset.create`, Project World scope, layout identity, and legacy/community fallback.
4. Run the protected and complete evidence chain before declaring E37 complete or choosing another Dock slice.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The persistent whole-engine objective remains active.

## E37 closure truth

E37 is complete for the bounded ProjectBrowser Dock shell/lifecycle slice. `ProjectBrowserPlugin` declares one Qt-free `project_browser.surface`; the existing Host Adapter owns shell projection and in-place Dock title localization; the plugin refreshes only retained ProjectPanel content. All four event bindings have exact unload ownership and failed-load rollback, and ProjectPanel no longer duplicates `project_opened` subscription ownership.

The first smoke exposed a missing retained icon-size label; a real-widget red test reproduced it and the final smoke is clean. Evidence: initial red `5 failed`; final E37 file `6 passed`; focused `45 passed`; expanded `140 passed`; protected `327 passed, 16 skipped`; fresh full non-signature `1476 passed, 34 skipped, 34 subtests passed in 152.42s`; `compileall`; real Editor smoke `plugins=13/20`; four green guardrails. The first full run's only load-sensitive asset-index threshold failure passed in isolation and no threshold changed. Signature-only remains blocked by missing `cryptography`.

E37 does not claim replacement-Host ProjectBrowser content parity, complete Dock migration, viewport/theme migration, a replacement UI Host, native GPU geometry/OpenGL readiness, signature provisioning, or whole-engine completion.

## Unique next Gate

**Phase E38 -- Qt-Free Console Dock Contribution and Exact Logging/Capability Adapter Lifecycle.** Start from its plan and red tests. Preserve the existing recursive framework/plugin architecture, Console output behavior, `UI_CONSOLE_PANEL` capability consumers, logging bridge semantics, tabification with Project, and legacy/community fallback.
