# Phase E48 Historical Closure -- Qt-Free Package Manager Reveal Menu Command and Exact Existing Dock Visibility/Geometry Lifecycle

Date: 2026-07-26
Status: historical closure

E48 is complete. Do not reopen it as planned work unless a regression provides new evidence.

## Closed architecture result

- The architecture remains `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`.
- `PackageManagerPlugin` retains the completed `package_manager.surface` Dock contribution and now publishes one copied `package_manager.reveal` menu command plus one canonical GUI command.
- Live `IMenuProvider` callbacks are removed. `LegacyEditorPluginAdapter`, the canonical command Registry, and `LayoutManager` remain the only menu/command/Dock projection and visibility authorities.
- Existing floating/docked mode, exact geometry, retained-content refresh, invalid-content recovery, and fallback current Qt dialog behavior are preserved.
- Command results are portable and exact unload/reload cleanup leaves no stale action, command, or Dock ownership.

## Closure evidence

- Red: `7 failed`.
- Dedicated: `8 passed in 0.29s`.
- Protected: `87 passed in 1.75s`.
- Full non-signature: `1605 passed, 34 skipped, 34 subtests passed in 238.66s`.
- Modified Modules/tests pass `compileall`; all four architecture guardrails pass.
- Real offscreen Editor smokes pass at `plugins=13/20` and eager `plugins=20/20`, with PackageManager added/removed once and no stale menu/command state.
- Signature-only remains blocked at collection by missing `cryptography` (`1 error in 0.17s`, exit code `2`). No dependency was installed.

E48 does not complete the remaining EditorWorkflow/StandardUI live menus, concrete PyQt content migration, replacement-Host parity, native/OpenGL default readiness, signatures, or the whole engine. The persistent objective remains active.

The unique next Gate is E49: `docs/superpowers/plans/2026-07-26-qt-free-editor-workflow-menu-commands-exact-pond-file-dialog-clipboard-bridge-lifecycle.md`.
