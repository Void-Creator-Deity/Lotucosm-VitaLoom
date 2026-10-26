# Phase E51 -- Qt-Free Declarative Menu/Toolbar Refresh and Obsolete Live Provider Interface Retirement

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. Reuse RuntimePluginHost copied metadata, the closed editor contribution Interface, canonical command Registry, and `LegacyEditorPluginAdapter` as the single current PyQt Host Adapter. Do not create another Host, Registry, contribution catalog, UI DSL, localization authority, composition root, app shell, or peer engine root.

## Previous Gate

E50 migrated the final built-in live menu/save-toolbar provider. StandardUI now publishes 22 immutable copied facts and 16 canonical commands while preserving exact Project World, scene, command-stack, LayoutManager/Dock, status, simulation, localization projection, and unload/reload behavior. Fresh full non-signature evidence is `1624 passed, 34 skipped, 34 subtests passed in 190.42s`; compile, four guardrails, and standard/eager Editor smokes pass. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- No runtime plugin implements `IMenuProvider`.
- No runtime plugin implements `get_menu_items()` or `get_toolbar_items()`; those methods exist only on the obsolete Interface and are called only by dormant Adapter compatibility code.
- `LegacyEditorPluginAdapter.load_plugin()` still checks `"menu" in provides` and `isinstance(plugin, IMenuProvider)`, and retains `register_menu()`, `_apply_menu_contributions()`, and hybrid live/declarative refresh branches.
- All built-in menu/toolbar shell projection now comes from RuntimePluginHost-copied `editor_contributions`.
- Localization publishes `language_changed`, then calls kernel `refresh_legacy_menu_contributions()`, which delegates to Adapter `refresh_menu_providers()`. These names and hybrid behavior no longer describe the active declarative path.
- Contribution state refresh events already subscribe directly through the Adapter and must remain exact; E51 must not duplicate or replace that lifecycle.
- The Adapter still has live Dock, viewport, and theme fallback seams. They are outside E51 and must not be removed merely because the menu provider seam is obsolete.

## Tasks

### Task 1 -- Executable red retirement contract

1. Prove the runtime contains no live `IMenuProvider` implementation or live menu/toolbar getter implementation.
2. Prove activation, language refresh, state refresh, unload, and reload of copied menu commands, separators, and toolbar commands remain deterministic and exact.
3. Prove localization refresh uses only copied metadata and does not inspect active plugin objects for menu/toolbar callbacks.
4. Prove stale actions fail after unload/reload and current shortcut/localization/state projection remains unchanged.

### Task 2 -- Remove only the obsolete live provider Interface

1. Remove `IMenuProvider` from `plugin_interfaces.py` and Adapter imports.
2. Remove `register_menu()`, `_apply_menu_contributions()`, the `"menu" in provides` activation branch, and live-provider/hybrid refresh branches.
3. Do not remove `IDockProvider`, `IViewportProvider`, `IThemeProvider`, or `LegacyEditorPluginAdapter` itself.
4. Fail closed on malformed copied contributions and preserve canonical owner injection and Host order.

### Task 3 -- Deepen the declarative refresh seam

1. Rename Adapter `refresh_menu_providers()` to a declarative name such as `refresh_editor_contributions()` and make it consume copied active metadata in exact Host order.
2. Rename kernel `refresh_legacy_menu_contributions()` and LocalizationPlugin's private bridge accordingly.
3. Preserve publish-then-refresh ordering for `language_changed`, deterministic remove/reproject behavior, and per-owner cleanup.
4. Keep contribution-state event refresh subscriptions exact and do not introduce a second localization or refresh Registry.

### Task 4 -- Verification and closure

1. Run dedicated red/green tests for Interface retirement, metadata-only refresh, localization ordering, projection parity, and unload/reload cleanup.
2. Run contribution/Adapter/command/localization/plugin-loader/StandardUI protection and the complete non-signature suite.
3. Run modified-Module `compileall`, all four architecture guardrails, standard/eager real Editor smoke, and signature-only collection. Record exact blockers without installing dependencies silently.
4. Update this plan to completed, convert its prompt to historical closure, update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`, and name exactly one next Gate only after a fresh post-E51 audit.

## Completion boundary

E51 may remove only the now-unused live menu/toolbar callback Interface and deepen/rename the existing copied-contribution refresh seam. It does not remove the current PyQt Host Adapter; migrate concrete editor content; remove live Dock/viewport/theme fallback seams; redesign localization, menus, toolbars, shortcuts, commands, or contribution facts; select/build a replacement Host; make native/OpenGL default-ready; provision signatures; or complete the editor/engine.

## Closure evidence

- Recovered and recompiled the four accidentally emptied legacy protection modules; the dedicated E51/recovery selection passes `36 passed in 0.85s`, and the four temporary bytecode-recovery helper files were removed without touching unrelated uncommitted work.
- Expanded contribution/Adapter/command/localization/plugin-loader/reload protection passes `145 passed in 3.67s`.
- Runtime stale-symbol audits return zero matches for `IMenuProvider`, `get_menu_items`, `get_toolbar_items`, `refresh_legacy_menu_contributions`, `refresh_menu_providers`, `_register_menu`, and `register_menu(`.
- The first complete non-signature run produced `1 failed, 1624 passed, 34 skipped, 34 subtests passed in 196.90s`; the only failure was the unrelated existing Asset Index cold-build threshold (`14.37s > 10s`). Its isolated rerun passed `1 passed in 8.36s`; no threshold or Asset Index code changed.
- Fresh second complete non-signature evidence is `1625 passed, 34 skipped, 34 subtests passed in 190.67s`.
- `compileall` passes for `FrameCore`, `workspace`, `tools`, `tests`, `main.py`, and `player.py`.
- All four architecture guardrails pass: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Real offscreen Editor smoke passes in standard mode (`plugins=13/20`) and eager mode (`plugins=20/20`), with zero discovery/load failures and deterministic reverse shutdown.
- Signature-only collection remains environmentally blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.21s`, exit code `2`). No dependency was installed and signature verification is not claimed.

## Completed result

`IMenuProvider` and every live menu/toolbar getter path are retired from the versioned runtime. Localization and toolbar-state refresh now reproject only RuntimePluginHost-copied `editor_contributions` through `LegacyEditorPluginAdapter.refresh_editor_contributions()` in exact Host metadata order. Canonical command invocation, separator structure, localization publish-then-refresh ordering, per-owner subscriptions, unload/reload cleanup, and current Qt projection remain intact. Dock, viewport, and theme concrete fallback seams remain deliberately untouched because they still carry current Host widget/QSS payloads.

## Next audited Gate

Fresh post-E51 audit found a deeper non-UI lifecycle mismatch: `ICommandProvider` describes UI/CLI/MCP/Agent-visible engine commands but still lives in `kernel/plugin_interfaces.py`, and command registration/release still runs inside the concrete `LegacyEditorPluginAdapter`. A `RuntimePluginHost` using `NullRuntimePluginHostAdapter` therefore cannot publish plugin commands even though the command Registry and command specifications are Qt-free. Five built-in command providers still import the legacy Interface, and `RuntimePluginHost` already reports post-unload failures under the stage name `command_owner_release`, showing that command ownership semantically belongs to the Host lifecycle rather than the UI Adapter.

**Unique next Gate: Phase E52 -- Qt-Free Runtime Command Provider Contract and Host-Owned Command Lifecycle.** Move only the command-provider Interface and exact register/release ownership into the existing Qt-free RuntimePluginHost lifecycle, reuse the one canonical command Registry, preserve command IDs/handlers/owner normalization/UI-CLI-MCP behavior and unload/reload/shutdown order, and remove the resulting legacy Adapter/PluginLoader command delegates. Do not migrate Dock/viewport/theme payloads, create another Host or Registry, redesign commands, or alter Project World/scene/package/renderer authorities.
