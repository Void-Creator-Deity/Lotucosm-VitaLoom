# Phase E48 -- Qt-Free Package Manager Reveal Menu Command and Exact Existing Dock Visibility/Geometry Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. Reuse the existing `menu_command` contribution Interface, canonical command Registry, already-completed `package_manager.surface` `dock_surface`, RuntimePluginHost copied metadata, `LegacyEditorPluginAdapter`, and current `LayoutManager`. Do not add another Host, command/menu/Dock Registry, visibility authority, contribution catalog, widget/dialog DSL, UI framework, composition root, Package authority, Project World authority, or peer engine root.

PyQt, `QDockWidget`, and the extreme fallback `QDialog` remain concrete current-Host implementation details. E48 must not grow framework/plugin rules around them.

## Previous Gate

E47 completed Hot Reload's two portable menu-command shells, shortcut facts, canonical command execution, exact Plugin Host observation/control behavior, and the bounded current Qt choice-dialog bridge. Evidence: red `12 failed`; dedicated `12 passed`; core protected `66 passed`; expanded protected `642 passed, 2 skipped, 9 subtests passed`; full non-signature `1597 passed, 34 skipped, 34 subtests passed`; compile, four guardrails, and standard/eager Editor smokes. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- Three built-in plugins still expose live `IMenuProvider` callbacks: `EditorWorkflowPlugin`, `PackageManagerPlugin`, and `StandardUIPlugin`.
- `PackageManagerPlugin` is the smallest bounded slice: exactly one live menu item at Tools / Project Plugins and no toolbar items.
- E39 already established one immutable Host-copied `package_manager.surface` Dock contribution with `dock_id="Package Manager"`, right placement, `default_visible=False`, exact in-place localization, and exact event/signal/capability lifecycle.
- The live action calls `show()`. That method is not merely `dock.show()`: it reuses the existing Host-projected Dock, reconstructs only if retained UI references are invalid, applies the configured floating/docked open mode through `LayoutManager.show_dock_with_mode()`, restores/records floating geometry, enforces a usable floating size, refreshes retained package content, and updates UI state.
- Only when the LayoutManager/Dock path is unavailable does `show()` create/reuse a standalone `QDialog` fallback. That fallback is current Qt implementation and must not enter contribution or command metadata.
- `LayoutManager` is already the single current Dock registration/removal/visibility/geometry authority. E48 must route the menu shell to the canonical command Registry without creating a generic Dock command Registry or moving visibility policy into metadata.
- Package catalog/operations, Project World manifest alignment, plugin runtime controls, service publication, filters, selection, update/install/uninstall behavior, and E39 lifecycle are out of scope for refactoring.

## Tasks

### Task 1 -- Executable red contract and ownership tests

1. Prove exactly one immutable JSON-safe Host-copied `menu_command` contribution owned canonically by PackageManager, with stable Tools path, Project Plugins label facts, empty payload, deterministic order, and no shortcut unless existing behavior proves one.
2. Prove metadata contains no callback, Qt/Dock/Dialog object, live plugin value, LayoutManager object, or visibility/geometry authority.
3. Prove declarative projection does not call legacy `get_menu_items()` and that exactly one canonical PackageManager reveal command is registered with canonical Adapter ownership.

### Task 2 -- Minimal canonical reveal command

1. Change `PackageManagerPlugin` from `IDockProvider + IMenuProvider` to `IDockProvider + ICommandProvider` while retaining its existing `dock_surface` declaration.
2. Publish exactly one `menu_command`, suggested identity `package_manager.reveal`, routed to exactly one canonical command, suggested ID `plugin.package_manager.reveal`.
3. Mark the command as GUI-required and mutating current Host presentation state. Keep the command payload empty and route its handler into the existing reveal implementation rather than duplicating Package or Dock policy.
4. Remove live menu/toolbar enumeration only after red tests prove declarative projection and command registration.

### Task 3 -- Exact existing Dock visibility/geometry lifecycle

1. Preserve reuse of the Host-projected `Package Manager` Dock and the `default_visible=False` shell fact.
2. Preserve configured floating/docked mode, `LayoutManager.show_dock_with_mode()`, exact saved floating geometry, fallback hex geometry path, minimum floating size, `show()/raise_()/activateWindow()` behavior, and UI toggle synchronization.
3. Preserve retained-content refresh and selection-detail refresh after reveal without replacing valid Dock/content identity.
4. Preserve the existing invalid-content recovery path through the same `LayoutManager` and the standalone `QDialog` fallback only when no usable LayoutManager/Dock exists.
5. Define deterministic command results for revealed Dock, revealed fallback dialog, and unavailable/failed reveal. Do not expose Qt objects in the result.
6. Prove unload/reload removes the exact command and menu action while the existing Adapter/LayoutManager Dock teardown remains authoritative and retry-safe.

### Task 4 -- Protection and closure

1. Preserve `.pond`, Project World, package manifests, package transactions, plugin runtime control, AI Command/Inspector, SR2D, viewport/theme, Player/export, startup/shutdown, and all four Host authorities.
2. Run dedicated red/green tests, PackageManager Dock/Host/Project World protection, contribution/menu/command/Adapter/reload protection, and the complete non-signature suite.
3. Run modified-Module `compileall`, all four architecture guardrails, standard/eager real Editor smoke, and signature-only collection. Record exact skips/blockers; do not install dependencies silently.
4. Update this plan to completed, convert its fresh-session prompt to historical closure, update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`, and name exactly one next Gate.

## Completion boundary

E48 may complete only PackageManager's one Qt-free reveal menu shell, one canonical command, and exact preservation of the existing Dock/fallback visibility and geometry lifecycle. It does not migrate EditorWorkflow or StandardUI menus; rewrite PackageManager content/domain/Project World behavior; create a general Dock action/visibility system; migrate concrete PyQt content; choose a replacement Host; make native/OpenGL default-ready; provision signatures; or complete the editor/engine.
## Implementation result

- `PackageManagerPlugin` now implements `IDockProvider + ICommandProvider`; it no longer implements `IMenuProvider` or publishes live `get_menu_items()` / empty toolbar callbacks.
- The existing `package_manager.surface` Dock contribution remains unchanged and authoritative. One additional immutable copied `package_manager.reveal` `menu_command` publishes only Tools path, localized label facts, empty payload, no shortcut, deterministic `order=70`, and canonical command ID `plugin.package_manager.reveal`.
- Exactly one GUI-required mutating `CommandSpec` routes through the existing `show()` implementation. The Adapter canonicalizes command ownership and the menu action calls the global canonical Registry; no Dock/menu/visibility Registry or second authority was added.
- `show()` now reports only the portable current-Host result token `dock` or `dialog`. Its behavior remains unchanged: valid Host-projected Dock reuse, invalid-content recovery through the same `LayoutManager`, configured floating/docked mode, geometry synchronization/restoration, minimum floating size, retained refresh/detail update, toggle synchronization, and extreme standalone dialog fallback.
- The command returns JSON-safe `revealed`, `unavailable`, or `failed` envelopes and never exposes Qt/Dock/Dialog objects. Existing direct callers may continue to ignore `show()`'s return value.
- Unload/reload removes the exact command and menu action while `LegacyEditorPluginAdapter` plus `LayoutManager` remain the sole Dock cleanup authority.

## Verification evidence

- Initial executable E48 red line: `7 failed`.
- Final dedicated E48 menu/command/visibility lifecycle: `8 passed in 0.29s`.
- PackageManager Dock/Host plus contribution/menu/command/Adapter/reload protection group: `87 passed in 1.75s`.
- Fresh complete non-signature suite: `1605 passed, 34 skipped, 34 subtests passed in 238.66s`.
- Modified Modules/tests pass `compileall`.
- Guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard real offscreen Editor smoke: `plugins=13/20`, zero discovery/load errors; PackageManager Dock is added once and removed once during deterministic reverse shutdown.
- Eager real offscreen Editor smoke: `plugins=20/20`, zero discovery/load errors; the command-backed PackageManager plugin loads/unloads cleanly with no stale menu, command, or Dock state.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.17s`, exit code `2`). No dependency was installed and signature verification is not claimed.

## Stable versus unfinished

Stable for E48: one portable PackageManager reveal menu shell, one canonical command, Host-copied/canonical ownership, exact existing Dock visibility/geometry/content refresh behavior, concrete fallback dialog containment, and exact unload/reload cleanup.

Two built-in legacy live menu providers remain: `EditorWorkflowPlugin` and `StandardUIPlugin`. Concrete PackageManager content remains PyQt current-Host implementation. Replacement-Host content parity, native/OpenGL default readiness, signatures, and whole-engine completion remain open.

## Next-Gate audit

`EditorWorkflowPlugin` is the smaller remaining provider: five menu actions, no toolbar content, and one `language_changed` subscription used only to remove/re-enumerate live menu callbacks. Its behaviors are important and heterogeneous: copy active `.pond` summary to the clipboard, export/import `.pond` JSON through file dialogs, scan scene dependencies and publish to the existing Console capability, and export a runnable Player. Qt dialogs/clipboard are concrete current-Host bridges; `.pond`, Cosmos, serializer, dependency scan, Console capability, and Player export semantics must remain unchanged. `StandardUIPlugin` still has 18 menu paths, two separators, a retained legacy save toolbar slice, Dock/layout controls, and broader event lifecycles, so it is not the next bounded Gate.

## Unique next Gate

**Phase E49 -- Qt-Free Editor Workflow Menu Commands and Exact Pond/File-Dialog/Clipboard Bridge Lifecycle.** Migrate only EditorWorkflow's five menu shells to copied `menu_command` facts and five canonical commands. Preserve `.pond` identity/state, serializer formats, Cosmos activation behavior, dependency scanning/Console publication, Player export, cancel/success/failure dialogs, clipboard text, localization, and cleanup. Remove the language-time live menu rebuild only when declarative refresh is proved. Do not migrate StandardUI, invent portable file-dialog/clipboard/widget systems, change Project World or Player authority, or claim the editor/engine complete.

