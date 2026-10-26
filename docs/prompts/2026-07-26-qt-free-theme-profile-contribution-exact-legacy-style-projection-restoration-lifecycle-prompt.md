# Phase E46 Historical Closure -- Qt-Free Theme Profile Contribution and Exact Legacy Style Projection/Restoration Lifecycle

Date: 2026-07-26
Status: historical closure

E46 is complete. Do not reopen it as planned work unless a regression provides new evidence.

## Closed architecture result

- The architecture remains `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`.
- `EditorThemeProfileContribution` is immutable, JSON-safe, Host-owned, deterministic, and Qt/QSS/live-object free.
- `UnityDarkThemePlugin` publishes one portable profile. Its QSS remains only a current Qt Adapter payload bridge.
- `LegacyEditorPluginAdapter` owns deterministic theme collision/order/application/unload/reload projection and exact baseline restoration without adding a second theme authority.
- `LayoutManager` captures and transactionally applies/restores application and main-window styles independently.
- Legacy/community Theme Providers preserve the old fallback path.

## Closure evidence

- Red: `16 failed, 3 passed`.
- Dedicated: `20 passed`.
- Compatibility: `38 passed` and `20 passed`.
- Expanded protected group: `384 passed, 1 skipped` after one stale historical supported-kind assertion was updated.
- Full non-signature: `1585 passed, 34 skipped, 34 subtests passed in 190.00s`.
- Modified Modules/tests pass `compileall`; all four architecture guardrails pass.
- Real offscreen Editor smokes pass at `plugins=13/20` and eager `plugins=20/20`, with Unity Dark applied once and cleanly removed during shutdown.
- Signature-only remains blocked at collection by missing `cryptography` (`1 error in 0.21s`). No dependency was installed.

E46 does not complete concrete editor-content migration, remaining menu providers, replacement-Host parity, native/OpenGL default readiness, signatures, or the whole engine.

The unique next Gate is E47: `docs/superpowers/plans/2026-07-26-qt-free-hot-reload-menu-command-contributions-host-control-dialog-bridge-lifecycle.md`.
