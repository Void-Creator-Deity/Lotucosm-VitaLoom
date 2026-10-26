# Phase E47 -- Qt-Free Hot Reload Menu Command Contributions and Host-Control Dialog Bridge Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserved `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. E47 deepened only the existing Qt-free `menu_command` Interface, canonical command Registry, RuntimePluginHost copied metadata, Plugin Host observation/control capability, and current `LegacyEditorPluginAdapter`. It did not add another Host, command Registry, contribution catalog, dialog/widget DSL, UI framework, composition root, Loader authority, or peer engine root. PyQt and `QInputDialog` remain concrete current-Host implementation details.

## Previous Gate

E46 completed the one built-in portable Theme Profile and exact current Qt style apply/unload/reload restoration lifecycle. Evidence: red `16 failed, 3 passed`; dedicated `20 passed`; protected `384 passed, 1 skipped`; full non-signature `1585 passed, 34 skipped, 34 subtests passed`; compile, four guardrails, and standard/eager Editor smokes. Signature-only remained blocked by missing `cryptography`.

## Completed slice

1. Extended the existing immutable `EditorMenuCommandContribution` with an optional portable `shortcut: str | None`. Serialization preserves it; parsing accepts only a non-empty plain string or `None`; invalid values fail closed with `contribution_shortcut_invalid`. Qt types, callbacks, live plugin values, and unknown fields remain rejected.
2. `LegacyEditorPluginAdapter` now projects the copied shortcut fact together with path and canonical command action. No QAction/QKeySequence contract, second menu Registry, or shortcut authority was introduced.
3. Migrated `HotReloadPlugin` from `IMenuProvider` to `ICommandProvider` plus `editor_contribution`. It publishes exactly two portable `menu_command` contributions: `hot_reload.choose -> plugin.hot_reload.choose -> F5 -> order 10` and `hot_reload.user_mod -> plugin.hot_reload.user_mod -> Ctrl+Shift+F5 -> order 20`.
4. Both actions execute through the existing canonical command Registry with canonical Adapter ownership, `mutates=True`, and `requires_gui=True`. The plugin no longer exposes live `get_menu_items()` or toolbar enumeration.
5. Reload candidates and copied `scope=user_mod` catalog facts still come only from `PLUGIN_HOST_CONTROL_OBSERVATION`; reload execution still uses that Host capability's `reload_plugin()` reports. `HotReloadPlugin` does not reach into `kernel.plugin_loader` or acquire Loader authority.
6. The one-plugin choice bridge imports `QInputDialog` lazily only inside the concrete current Qt implementation method. Contribution and command metadata remain readable when PyQt import is forbidden. No portable dialog system was invented.
7. Deterministic outcomes are covered for no candidates, cancel, invalid choice, settled reload, failed reports, user-mod filtering/order, no targets, all-settled batch, and partial failures. Compatibility entry points route into canonical handlers.
8. Unload/reload removes the exact owned commands and Adapter-projected actions without stale ownership or legacy live menu callbacks.

## Completion evidence

- Initial executable E47 red line: `12 failed`.
- Final dedicated Hot Reload contribution/command/dialog/lifecycle file: `12 passed in 0.44s`.
- Core contribution/Adapter/Host/reload protection group: `66 passed in 1.35s`.
- Expanded plugin/editor/command/menu/reload protection group: `642 passed, 2 skipped, 987 deselected, 9 subtests passed in 58.72s`.
- Fresh complete non-signature suite: `1597 passed, 34 skipped, 34 subtests passed in 225.59s`.
- Modified Modules/tests pass `compileall` with `COMPILE_EXIT=0`.
- Guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard real offscreen Editor smoke: `plugins=13/20`, zero discovery/load errors, deterministic reverse shutdown.
- Eager real offscreen Editor smoke: `plugins=20/20`, zero discovery/load errors; `HotReloadPlugin` loads and unloads cleanly with no stale menu/command errors.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.18s`, exit code `2`). No dependency was installed and signature verification is not claimed.

## Completion boundary

E47 completes only Hot Reload's two Qt-free menu-command shells, portable shortcut facts, canonical command execution, exact Plugin Host observation/control behavior, and the bounded current Qt choice-dialog bridge lifecycle. It does not migrate `EditorWorkflowPlugin`, `PackageManagerPlugin`, or `StandardUIPlugin`; migrate concrete editor content away from PyQt; choose or prove a replacement Host; create a portable widget/dialog DSL; make native/OpenGL acceleration default-ready; provision signatures; or complete the editor/engine.

## Next-Gate audit

Three built-in plugins still expose legacy live `IMenuProvider` callbacks: `EditorWorkflowPlugin`, `PackageManagerPlugin`, and `StandardUIPlugin`. `PackageManagerPlugin` is the smallest bounded slice: one Tools/Project Plugins action, no toolbar items, and an already completed portable `package_manager.surface` Dock contribution. Its retained `show()` behavior owns meaningful current-Host policy: reveal the existing Dock, preserve configured floating/docked open mode and floating geometry, recover invalid content through the existing `LayoutManager`, and use a fallback dialog only when the LayoutManager/Dock path is unavailable. This behavior must be routed through one canonical command without inventing a second Dock visibility authority or widening into Package domain/UI refactoring.

## Unique next Gate

**Phase E48 -- Qt-Free Package Manager Reveal Menu Command and Exact Existing Dock Visibility/Geometry Lifecycle.** Migrate only PackageManager's one legacy menu shell through the existing `menu_command` Interface and canonical command Registry. Preserve the already declarative `package_manager.surface`, current `LayoutManager` ownership, default-hidden shell, floating/docked policy, exact saved geometry, retained-content refresh, fallback dialog, localization, package/Project World semantics, and unload/reload cleanup. Do not migrate EditorWorkflow or StandardUI menus, create a general Dock command/visibility Registry, add a widget/dialog DSL, or claim the editor/engine complete.
