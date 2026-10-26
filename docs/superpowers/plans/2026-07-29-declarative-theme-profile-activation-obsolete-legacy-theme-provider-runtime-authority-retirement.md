# Phase E54 -- Declarative Theme Profile Activation and Obsolete Legacy Theme Provider Runtime Authority Retirement

Date: 2026-07-29
Status: completed on 2026-07-29

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. Reuse the existing `RuntimePluginHost`, copied `EditorThemeProfileContribution` facts, `LegacyEditorPluginAdapter`, `LayoutManager`, and current concrete Unity Dark QSS payload. Do not create a second Host, theme Registry/catalog, palette/token authority, composition root, UI framework, app shell, or peer engine root.

## Previous Gate

E53 made the eight Host-copied `dock_surface` facts the only built-in Dock identity/configuration authority and retired built-in/Adapter/Loader `IDockProvider` gating. Focused evidence is `5 passed`; eight-Dock lifecycle evidence is `60 passed`; the expanded protection selection is `160 passed, 1 skipped`; compile, four guardrails, and standard/eager Editor smokes pass. The first full non-signature run has one pre-existing load-sensitive Asset Index threshold miss, which passes in isolation; signature collection remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- E46 already established immutable, JSON-safe Host-copied `theme_profile` facts. `UnityDarkThemePlugin` declares `unity_dark.profile` / `unity.dark`, including portable profile identity/order/appearance/palette.
- `UnityDarkThemePlugin` still imports and inherits `IThemeProvider` and exposes the current-QT `get_stylesheet()` payload.
- `LegacyEditorPluginAdapter` still imports/tests `IThemeProvider` when selecting the built-in profile's QSS payload, while the copied profile already supplies identity/configuration authority.
- `PluginLoader` has no direct current `IThemeProvider` gate, but E54 must preserve its legacy/community compatibility behavior and verify no stale provider authority remains in its facade path.
- `get_stylesheet()` is not a portable L0-L4 contribution and must remain Adapter-local. Existing theme profile ordering, collision prevention, baseline capture/restoration, failure-retry preservation, reload, and legacy/community fallback are already contractual.
- The three viewport providers are a separate live-payload seam and are outside E54.

## Tasks

### Task 1 -- Executable red Theme-authority contract

1. Prove a built-in declarative `theme_profile` activates, layers, unloads, and restores exact baseline state without inheriting `IThemeProvider`.
2. Prove absent, non-callable, non-string, or exception-raising built-in QSS payload factories fail explicitly and leave no half-active Host/plugin/theme projection/style mutation.
3. Preserve exact collision-before-mutation, deterministic ordering, theme-stack reprojection, baseline restoration, cleanup failure retry, reload, localization, and shutdown behavior.
4. Preserve bounded legacy/community `IThemeProvider` fallback without making fallback metadata or live QSS methods a second built-in authority.

### Task 2 -- Retire obsolete built-in Theme Provider authority

1. Make `EditorThemeProfileContribution` the only built-in Unity Dark identity/configuration authority.
2. Treat `get_stylesheet()` solely as the concrete current-PyQt payload factory consumed by `LegacyEditorPluginAdapter`; do not copy QSS/callables/live style objects into Host metadata.
3. Remove `UnityDarkThemePlugin` inheritance/import dependence on `IThemeProvider` and remove Adapter/Loader built-in type-gating only after lifecycle parity passes.
4. Keep only a bounded legacy compatibility branch for unmigrated community providers, with explicit source and behavior coverage.

### Task 3 -- Verification and closure

1. Run focused theme projection/factory/rollback tests, existing E46 lifecycle coverage, Host activation/unload/reload/shutdown, command, localization, Dock/viewport, Project World, package, and community compatibility protections.
2. Run the complete non-signature suite, modified-module `compileall`, all four architecture guardrails, and standard/eager real Editor smoke.
3. Run signature-only collection and record the exact environment blocker without silently installing dependencies.
4. Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, relevant contribution contract documentation, and `docs/INDEX.md`; name exactly one next Gate only after a fresh post-E54 audit.

## Completion boundary

E54 may retire only obsolete built-in Theme Provider runtime authority for the already-declarative Unity Dark profile while keeping concrete QSS as an Adapter payload and preserving legacy/community fallback. It does not migrate viewport providers, create a universal style/widget DSL, alter Theme/Palette/command/scene/Project World/package/Player/export/SR2D/native/OpenGL/signature authorities, select a replacement Host, or complete the editor/engine.
## Completion record (2026-07-29)

- **Authority retired.** `UnityDarkThemePlugin` now implements the Qt-free `IRuntimePlugin` contract directly. Its copied `theme_profile` is the sole built-in identity/configuration authority. The concrete `get_stylesheet()` method remains only the current PyQt payload factory in `LegacyEditorPluginAdapter`; QSS, callables, Qt objects, widgets, and live style state were not copied into Host metadata.
- **Bounded compatibility.** Adapter selection no longer checks `IThemeProvider`. A theme-profile owner uses the declared path regardless of its legacy inheritance. Only an unmigrated community plugin that declares `theme` and exposes callable `get_theme_name()` plus `get_stylesheet()` can use the narrow legacy fallback.
- **Transactional proof.** New lifecycle coverage proves declarative non-`IThemeProvider` activation, canonical command ownership, projection stack/baseline restore, and removal of all Host/theme/style state on unload. Missing, `None`, or raising payload factories fail activation and roll back Host publication, commands, style/projection state, and lifecycle notifications; `on_unload()` is invoked and `plugin_loaded` is not emitted.
- **Regression evidence.** The E54 authority suite passes: `5 passed in 0.23s`. The expanded theme/Host/command/editor contribution/Dock/viewport/Project World/package/community protection selection passes: `175 passed, 1 skipped in 3.34s`. The complete non-signature suite is green: `1641 passed, 34 skipped, 34 subtests passed in 169.63s`.
- **Build and runtime evidence.** Modified-file `compileall` passes; `check_project_plugin_model.py`, `check_core_boundaries.py`, `check_gui_boundaries.py`, and `check_release_consistency.py` all report `OK`. Real offscreen Editor smokes pass in standard mode (`plugins=13/20`) and eager mode (`plugins=20/20`) with zero discovery/load failures and deterministic reverse shutdown.
- **Environment limit.** Signature-only collection is still blocked by `.venv` missing `cryptography`: `ModuleNotFoundError: No module named 'cryptography'`, `1 error in 0.29s`, exit code `2`. No dependency was installed, so signature verification is not claimed.
- **Scope honesty.** E54 does not migrate the three viewport providers, introduce another Host/Registry/style system, establish replacement-Host parity, make native/OpenGL default-ready, or complete the editor/engine.

## Fresh post-E54 audit and unique next Gate

All three built-in viewport shells (`CellEditorPlugin`, `GameViewportPlugin`, and `SceneViewportPlugin`) already publish immutable Host-copied `viewport_surface` facts, but still inherit the PyQt-era `IViewportProvider` and the Adapter still uses it to gate legacy viewport activation/cleanup. The smallest remaining authority mismatch is therefore the shared viewport seam, not concrete viewport content or rendering.

**Unique next Gate: Phase E55 -- Declarative Viewport Surface Activation and Obsolete Legacy Viewport Provider Runtime Authority Retirement.** Make copied `viewport_surface` facts the sole built-in shell identity/configuration and projection/cleanup authority; keep `create_viewport_widget()` as the concrete PyQt Adapter payload; retire built-in/Adapter `IViewportProvider` gating while preserving exact layout, localization, subscriptions, reload/shutdown, Project World, SR/PS, `.pond`, command/Inspector, and bounded community fallback parity. Do not redesign concrete viewport content, create another Host/Viewport Registry, or change native/OpenGL authority.