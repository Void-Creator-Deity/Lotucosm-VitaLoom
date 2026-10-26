# Phase E46 -- Qt-Free Theme Profile Contribution and Exact Legacy Style Projection/Restoration Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserved `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. E46 deepened only the existing Qt-free editor contribution Interface and the current `LegacyEditorPluginAdapter`. It did not create another Host, contribution catalog, theme Registry, token authority, composition root, app shell, UI framework, or peer engine root. PyQt/QSS/`ThemeManager`/`LayoutManager` remain concrete legacy Adapter implementation details.

## Previous Gate

E45 completed the three built-in declarative Viewport shells and capability-safe GameViewport teardown. Built-in Dock shells are `8/8 = 100%` and built-in Viewport shells are `3/3 = 100%`, but these are shell-only ratios. E45 evidence included full non-signature `1565 passed, 34 skipped, 34 subtests passed`, standard/eager Editor smokes, compile, and four guardrails. Signature-only remained blocked by missing `cryptography`.

## Completed slice

1. Added immutable JSON-safe `EditorThemeProfileContribution` through the existing `editor_contribution_contract.py` Interface. The copied facts are stable contribution/theme identity, localized display facts, `dark|light` appearance, a read-only deterministically ordered semantic palette, and order.
2. The contract rejects QSS/stylesheet fields, Qt/live objects, callbacks, invalid semantic tokens, invalid colors, forged ownership, duplicate contribution IDs, and duplicate same-owner theme IDs. No Theme Registry/Host/token authority was added.
3. Migrated the one built-in `UnityDarkThemePlugin` to publish `unity_dark.profile` / `unity.dark`. QSS remains only in legacy `IThemeProvider.get_stylesheet()` as the current Qt Adapter payload bridge.
4. Extended `LegacyEditorPluginAdapter` with an internal concrete projection ledger. Declarative identity/order comes only from the Host-copied profile; live `get_theme_name()` / `get_color_scheme()` are not consulted, and `get_stylesheet()` is read exactly once. Unmigrated community providers retain the prior live fallback.
5. Theme ID collision is rejected before QSS retrieval or style mutation. Active projection is deterministic by `(order, theme_id, owner_plugin_id)`. Loading a lower layer does not perturb the active style; active unload reprojects the next layer; final unload restores the exact pre-theme application/window baseline.
6. `LayoutManager` now captures application and main-window styles independently and applies/restores them transactionally. If either write fails, the pre-write state is restored. Adapter cleanup retains its owner/projection ledger on apply/restore failure so unload can be retried without stale ownership.
7. Declarative Unity Dark projection preserves `DARK_THEME + modern_editor_overlay() + plugin QSS`; legacy/community fallback preserves its former `DARK_THEME + plugin QSS` behavior.

## Completion evidence

- Initial executable red line: `16 failed, 3 passed`.
- Final E46 dedicated contract/projection/style lifecycle: `20 passed in 0.34s`.
- Contribution/Adapter compatibility: `38 passed in 0.65s`.
- Dock/Viewport/shutdown compatibility: `20 passed in 0.60s`.
- Expanded plugin/reload/editor/theme/layout/startup/shutdown protection first exposed one stale historical supported-kind assertion: `1 failed, 383 passed, 1 skipped`. After updating that test for the new legitimate kind, the group passed `384 passed, 1 skipped in 11.16s`.
- Fresh complete non-signature suite: `1585 passed, 34 skipped, 34 subtests passed in 190.00s`.
- Modified Modules/tests pass `compileall`.
- Guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard real offscreen Editor smoke: `plugins=13/20`, zero discovery/load errors; Unity Dark applied once and unloaded cleanly during deterministic reverse shutdown.
- Eager real offscreen Editor smoke: `plugins=20/20`, zero discovery/load errors; Unity Dark applied once and unloaded cleanly while all eager plugins shut down in deterministic reverse order.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.21s`, exit code `2`). No dependency was installed and signature verification is not claimed.

## Completion boundary

E46 completes only the built-in portable theme-profile shell and exact current Qt Adapter style lifecycle. It does not migrate concrete Dock/Viewport content away from PyQt, finish all legacy menu providers, select or build a replacement Host, create a universal widget/style DSL, make native/OpenGL acceleration default-ready, provision signatures, or complete the engine.

## Next-Gate audit

Four built-in plugins still expose legacy live `IMenuProvider` callbacks: `StandardUIPlugin`, `EditorWorkflowPlugin`, `PackageManagerPlugin`, and `HotReloadPlugin`. `LocalizationUIPlugin` already proves the portable `menu_command` path. The smallest remaining bounded menu slice is `HotReloadPlugin`: two actions, no toolbar content, stable shortcuts, existing canonical Plugin Host observation/control seams, but live callback/path enumeration and a concrete `QInputDialog` still sit behind the legacy provider Interface.

## Unique next Gate

**Phase E47 -- Qt-Free Hot Reload Menu Command Contributions and Host-Control Dialog Bridge Lifecycle.** Migrate only the two Hot Reload menu shells through the existing `menu_command` contract and canonical command registry. Preserve reloadable-plugin observation, user-mod filtering, F5 shortcuts, reload reports, localization, cleanup/reload, and the existing concrete Qt choice dialog as a bounded current-Host bridge. Do not migrate the other three menu providers, invent a dialog/widget DSL, create another Host/Registry/command authority, or claim the editor/engine complete.
