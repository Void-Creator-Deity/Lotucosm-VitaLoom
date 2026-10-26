# Phase E45 -- Qt-Free GameViewport Surface Projection and Capability-Safe Host Teardown Sequencing

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. Reuse the existing `viewport_surface` Interface, `LegacyEditorPluginAdapter`, single `LayoutManager` viewport Registry, capability publication leases, and the four established Host authorities. PyQt remains the current concrete Host Adapter/content bridge; it is not the framework root or extension authority.

## Previous Gate

E44 completed the declarative SceneViewport shell and exact eight-event lifecycle. Built-in viewport-shell migration was `2/3 = 66.7%`, not whole-engine completion. Evidence included full non-signature `1554 passed, 34 skipped, 34 subtests passed`, standard/eager Editor smokes, compile, and four guardrails. Signature-only remained blocked by missing `cryptography`.

## Audit truth before implementation

- `GameViewportPlugin` declared only `viewport`; it had no `editor_contribution` or `game.surface`.
- It directly subscribed to `simulation_play`, `simulation_pause`, `simulation_stop`, and `language_changed` without partial-failure rollback, failed-release retry, or complete repeated-unload evidence.
- Widget creation was not explicitly idempotent; normal unload called both `unregister_as_sr_host()` and `deleteLater()` while `LayoutManager` was the projected-surface deletion authority.
- `_on_language_changed()` penetrated `layout_manager.viewport_tabs` and called `setTabText()`.
- Concrete `GameViewport` publishes `SIMULATION_SR_HOST` and `SR_SELECTED_IDENTITY_HOST`, owns SimulationTransport interaction, SR runtime snapshots/selected identity, rendering/input/playback state, and a capability publication lease.
- `RuntimePluginHost` deactivation called Adapter surface cleanup before `plugin.on_unload()`. Qt `deleteLater()` deferred destruction, but that timing was not a Qt-free replacement-Host contract.

## Completed slice

1. Added one immutable JSON-safe `game.surface` `viewport_surface` contribution with `viewport_id=game`, localized name facts, deterministic `order=20`, and `language_changed` refresh facts. Legacy/community getters remain available.
2. Gave `GameViewportPlugin` exact ownership of `simulation_play`, `simulation_pause`, `simulation_stop`, and `language_changed`: ordered acquisition, reverse rollback, reverse release, precise failed-release retention, retry, and repeated create/unload idempotency.
3. Added the optional Qt-free `IRuntimePluginTeardown.prepare_host_teardown()` Interface. `RuntimePluginHost` invokes it only for plugins that explicitly implement the capability, before the current Adapter removes concrete contributions.
4. `GameViewportPlugin.prepare_host_teardown()` releases exact callbacks and the existing `SIMULATION_SR_HOST` / `SR_SELECTED_IDENTITY_HOST` publication lease before `LayoutManager.remove_viewport()` can destroy the concrete surface. A failure stops deactivation at `plugin_prepare_host_teardown`, leaves the plugin active, skips Adapter cleanup, and remains retryable.
5. `LayoutManager` remains the single projected Widget removal/deletion authority. Normal unload no longer calls `deleteLater()`; activation rollback may delete only an unprojected Widget after callback and capability rollback fully succeeds.
6. Language refresh now retranslates retained GameViewport content in place. It does not access `viewport_tabs` or call `setTabText()`; Host contribution projection owns the tab name.
7. SimulationTransport, SR snapshots/selected identity, scene reload, renderer/canvas seams, `.pond`, AI Command/Inspector, Project World, reload/shutdown, Player/export, and exact capability replacement-owner behavior remain unchanged and green.

## Completion evidence

- Initial executable red line: `8 failed, 7 passed`.
- Final E45 dedicated lifecycle/contribution/real-Host suite: `17 passed`.
- Related Host/contribution/capability group: `68 passed in 2.27s`.
- Expanded GameViewport/Host/viewport/capability group: `107 passed, 1492 deselected in 2.23s`.
- Protected Viewport/Layout/capability/reload/shutdown/SR group: `305 passed, 1294 deselected in 61.60s`.
- Fresh full non-signature suite: `1565 passed, 34 skipped, 34 subtests passed in 205.14s`.
- Modified Modules pass `compileall`.
- Guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard real offscreen Editor smoke: `plugins=13/20`, zero discovery/load errors; `game` was added once and removed once during deterministic reverse shutdown.
- Eager real offscreen Editor smoke with `VITALOOM_EAGER_PLUGINS=1`: `plugins=20/20`, zero discovery/load errors; `game` was added once and removed once while all eager plugins shut down in deterministic reverse order.
- Signature-only collection still stops at `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.33s`). No dependency was installed and signature verification is not claimed.

## Completion boundary

E45 completes the declarative shell/lifecycle migration of all three in-scope built-in Viewports: `3/3 = 100%`. Combined with the already closed Dock work, built-in Dock shells are `8/8 = 100%` and built-in Viewport shells are `3/3 = 100%`.

These ratios do not describe concrete editor-content migration, menu/theme migration, a replacement Host, rendering/backend completion, native/OpenGL default readiness, signature provisioning, or whole-engine completion. The persistent engine objective remains active.

## Next-Gate audit

The remaining extension-facing theme path is now the smallest ordered shell authority gap. There is one built-in `UnityDarkThemePlugin`. Its legacy `IThemeProvider` exposes Qt/QSS implementation, `LegacyEditorPluginAdapter.register_theme()` reads live plugin getters and prepends `ThemeManager.DARK_THEME`, and `LayoutManager.register_theme()` applies styles immediately. There is no Host-copied portable theme descriptor, canonical theme owner/id collision rule, or exact unload/reload restoration lifecycle; cleanup currently removes Dock/Viewport/menu/toolbar ownership but not the applied theme. The existing plain color scheme is portable evidence worth preserving, while QSS must remain only a concrete Qt Adapter payload.

## Unique next Gate

**Phase E46 -- Qt-Free Theme Profile Contribution and Exact Legacy Style Projection/Restoration Lifecycle.** Add a portable theme-profile contribution through the existing editor contribution Interface, migrate only `UnityDarkThemePlugin`, and make the current legacy Adapter own deterministic apply/collision/unload/reload restoration. Keep QSS and `ThemeManager` concrete to the Qt Adapter, preserve visual parity and baseline overlays, and do not create a second Host, theme registry, token system, UI framework, app shell, or peer engine root.
