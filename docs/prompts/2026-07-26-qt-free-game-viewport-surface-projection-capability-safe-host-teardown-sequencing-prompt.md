# Phase E45 Historical Closure -- Qt-Free GameViewport Surface Projection and Capability-Safe Host Teardown Sequencing

Date: 2026-07-26
Status: historical closure

E45 is complete. Do not reopen it as planned work unless a regression provides new evidence.

## Closed architecture result

- The architecture remains `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`.
- `GameViewportPlugin` now publishes one immutable JSON-safe `game.surface` `viewport_surface` contribution while concrete PyQt GameViewport remains the current legacy content bridge.
- The plugin owns exactly four callbacks with ordered acquisition, reverse rollback/release, failed-release retry, and idempotent repeated teardown.
- The Qt-free optional `IRuntimePluginTeardown` Interface lets `RuntimePluginHost` release capability-sensitive plugin resources before the current Adapter removes concrete Host contributions.
- `SIMULATION_SR_HOST` and `SR_SELECTED_IDENTITY_HOST` publication is released before GameViewport surface destruction; failures stop at `plugin_prepare_host_teardown`, preserve the active plugin, skip Adapter cleanup, and can be retried.
- `LayoutManager` remains the sole projected surface removal/deletion authority. Normal plugin unload does not call `deleteLater()` and localization no longer reaches into `viewport_tabs` or `setTabText()`.

## Closure evidence

- Red: `8 failed, 7 passed`.
- Dedicated: `17 passed`.
- Related: `68 passed in 2.27s`.
- Expanded: `107 passed, 1492 deselected in 2.23s`.
- Protected: `305 passed, 1294 deselected in 61.60s`.
- Full non-signature: `1565 passed, 34 skipped, 34 subtests passed in 205.14s`.
- Modified Modules pass `compileall`; all four architecture guardrails pass.
- Real offscreen Editor smokes pass at `plugins=13/20` and eager `plugins=20/20`, each with one GameViewport add and one remove and zero discovery/load errors.
- Signature-only remains blocked at collection by missing `cryptography` (`1 error in 0.33s`). No dependency was installed.

Built-in Dock-shell migration is `8/8 = 100%`; built-in Viewport-shell migration is `3/3 = 100%`. Concrete PyQt content, menu/theme migration, replacement-Host parity, rendering/native/OpenGL default readiness, signatures, and the whole engine remain unfinished.

The unique next Gate is E46: `docs/superpowers/plans/2026-07-26-qt-free-theme-profile-contribution-exact-legacy-style-projection-restoration-lifecycle.md`.
