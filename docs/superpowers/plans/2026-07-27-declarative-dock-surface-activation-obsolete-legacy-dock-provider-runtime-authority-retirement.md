# Phase E53 -- Declarative Dock Surface Activation and Obsolete Legacy Dock Provider Runtime Authority Retirement

Date: 2026-07-27
Status: completed on 2026-07-29

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. Reuse the existing `RuntimePluginHost`, copied `EditorDockSurfaceContribution` facts, `LegacyEditorPluginAdapter`, `LayoutManager`, and current concrete PyQt Dock factories. Do not create a second Host, surface Registry/catalog, layout authority, UI framework, app shell, or peer engine root.

## Previous Gate

E52 moved the Qt-free command-provider Interface and exact command publish/rollback/release lifecycle into `RuntimePluginHost`. Fresh evidence is `1631 passed, 34 skipped, 34 subtests passed in 158.98s`; compile, all four guardrails, and standard/eager Editor smokes pass. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- All eight built-in Dock providers already publish immutable Host-copied `dock_surface` facts, so Dock id/title/area/visibility/mobility/order/refresh ownership is declarative.
- Built-ins still inherit/import the PyQt-era `IDockProvider` from `kernel/plugin_interfaces.py`.
- `LegacyEditorPluginAdapter.after_plugin_load()` and fallback cleanup still use `isinstance(plugin, IDockProvider)` as activation authority even though declarative projection already resolves the current concrete `create_dock_widget` factory from the active plugin.
- Concrete Dock widgets must remain current-host Adapter payloads; they must not enter the Qt-free L0-L4 contract or become a generic widget framework.
- Three viewport providers and one theme provider remain separate live-payload seams. They are outside E53.

## Tasks

### Task 1 -- Executable red Dock-authority contract

1. Prove every built-in Dock activates and cleans up from copied `dock_surface` metadata without `IDockProvider` runtime type checks.
2. Prove a missing/non-callable/failing concrete Dock factory reports an explicit Adapter projection failure and leaves no half-active plugin, stale Dock owner, refresh subscription, command, or layout entry.
3. Preserve exact unload, reload, shutdown, localization refresh, existing-Dock reuse, visibility/geometry, tabify/layout settling, and protected-plugin behavior.
4. Preserve bounded legacy/community fallback behavior without making fallback metadata or widget methods a second authority.

### Task 2 -- Retire obsolete built-in Dock provider authority

1. Make `EditorDockSurfaceContribution` the sole built-in Dock identity/configuration authority.
2. Treat `create_dock_widget` only as a concrete current-Host factory consumed inside `LegacyEditorPluginAdapter`; do not copy callables/widgets into RuntimePluginHost metadata.
3. Remove built-in inheritance/import dependence on `IDockProvider`; keep only a bounded compatibility shim if executable external compatibility proves it necessary.
4. Remove stale Adapter/Loader `IDockProvider` gates only after Dock lifecycle parity is green.

### Task 3 -- Verification and closure

1. Run focused Dock projection/factory/rollback tests plus all eight built-in Dock lifecycle, localization, layout/tabify, reload, shutdown, command, Inspector, Project World, package, and community compatibility protections.
2. Run the complete non-signature suite, modified-Module `compileall`, all four architecture guardrails, and standard/eager real Editor smoke.
3. Run signature-only collection and record the exact environment blocker without installing dependencies silently.
4. Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, relevant Dock/contribution contracts, and `docs/INDEX.md`; name exactly one next Gate only after a fresh post-E53 audit.

## Completion boundary

E53 may retire only obsolete legacy Dock-provider runtime authority for the eight already-declarative built-in Dock shells while preserving their concrete PyQt content as Adapter payloads. It does not migrate viewport/theme providers, invent a replacement UI Host or generic widget contract, change `.pond`, Project World, scene, package, Player/export, SR2D, native/OpenGL, command ownership, or signature authorities, or complete the editor/engine.

## Completion record (2026-07-29)

- **Authority retired:** the eight built-in Dock shells now activate and clean up solely from Host-copied `dock_surface` facts. `LegacyEditorPluginAdapter` and `PluginLoader` no longer use `IDockProvider` as built-in runtime activation authority. Each built-in plugin removes the obsolete inheritance/import and `get_dock_config()` path; `create_dock_widget()` is retained only as the concrete current-PyQt Adapter payload factory.
- **Transactional safety:** the executable contract covers a declarative Dock that does not inherit `IDockProvider`, plus absent, `None`-returning, and exception-raising factories. Every failure rolls back Host activation, commands, UI state, subscriptions, layout ownership, and Dock ownership without a half-active plugin.
- **Evidence:** E53 focused tests `5 passed in 0.60s`; eight-Dock lifecycle selection `60 passed in 1.55s`; expanded Dock/Host/command/Project World/package/community compatibility selection `160 passed, 1 skipped in 4.20s`; modified-module `compileall`; project-plugin-model, core-boundary, GUI-boundary, and release-consistency guardrails all report `OK`; standard and eager real offscreen Editor smokes pass at `plugins=13/20` and `plugins=20/20`, with zero discovery/load errors and deterministic reverse teardown.
- **Honest full-regression result:** the complete non-signature run produced `1 failed, 1635 passed, 34 skipped, 34 subtests passed in 150.83s`. Its only failure was the existing load-sensitive Asset Index cold-start threshold (`14.5546574s > 10.0s`); no threshold or Asset Index code was changed. The isolated retry passed (`1 passed in 6.05s`). This phase therefore does not claim an all-green first full run.
- **Environment blocker:** signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` in the repository `.venv`. No dependency was installed, and signature verification is not claimed.

## Next-Gate audit

`UnityDarkThemePlugin` already contributes one Host-copied `theme_profile`, but it still imports/inherits the PyQt-era `IThemeProvider`, and the Adapter still uses that Interface to select its built-in live QSS payload. The three viewport providers are a larger, separate seam. The smallest ordered next phase is to retire only the obsolete built-in Theme Provider runtime authority while retaining QSS as current-Adapter payload and legacy/community fallback.

## Unique next Gate

**Phase E54 -- Declarative Theme Profile Activation and Obsolete Legacy Theme Provider Runtime Authority Retirement.** Make the existing `theme_profile` the sole built-in Unity Dark identity/configuration authority; consume `get_stylesheet()` only as an Adapter-local PyQt payload; remove built-in/Adapter/Loader `IThemeProvider` type-gating after executable rollback/retry/reload/localization parity is proved; preserve community legacy fallback and exact baseline restoration. Do not migrate viewport providers, create a style/widget DSL, change Theme/Palette/command/rendering authority, or introduce another Host/Registry.
