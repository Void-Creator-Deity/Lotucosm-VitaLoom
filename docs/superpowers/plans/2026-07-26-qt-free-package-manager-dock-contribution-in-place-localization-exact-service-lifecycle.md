# Phase E39 -- Qt-Free PackageManager Dock Contribution and In-Place Localization/Exact Service Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the versioned product runtime boundary containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. `LegacyEditorPluginAdapter` remains the current concrete PyQt Host Adapter. Reuse the existing `dock_surface`, runtime capability publication, Package domain, Project World, event, menu, and LayoutManager seams. Do not create a second Host, registry, catalog, package authority, service registry, manifest authority, composition root, Dock/UI framework, widget DSL, or replacement shell.

## Previous Gate

E38 completed the bounded Console shell/lifecycle slice. Evidence: initial red `10 failed`; final E38 file `13 passed`; joint capability lifecycle `21 passed`; focused `44 passed`; expanded `130 passed, 1 skipped`; fresh full non-signature `1489 passed, 34 skipped, 34 subtests passed in 172.43s`; `compileall`; four green guardrails; real offscreen Editor smoke `plugins=13/20` with zero discovery errors. Signature-only remains blocked because the exact repository `.venv` lacks `cryptography`.

Four of eight in-scope built-in Dock providers are now declarative: Inspector, Hierarchy, ProjectBrowser, and Console. This is 50% of the Dock-shell migration only, not 50% of the engine.

## Audit truth

`PackageManagerPlugin` is the next bounded Dock slice and already contains deep Package domain and Project World behavior that must not be rewritten during shell migration.

Current facts:

- It provides `dock` and `menu`, but not `editor_contribution`, and has no Qt-free `dock_surface` declaration.
- Its stable Dock shell is `Package Manager`, right placement, default hidden, closeable, non-tabbed, and normally opened through the Tools menu. Floating versus docked open mode and saved floating geometry are existing behavior.
- `on_load()` directly subscribes to four runtime events: `language_changed`, `project_opened`, `project_plugins_synced`, and `project_manifest_issues`. It also connects exact kernel `plugin_loaded` and `plugin_unloaded` signals.
- It publishes `PACKAGE_CATALOG` and `PACKAGE_OPERATIONS` together through one capability publication lease owned by `adapter.package-manager`.
- Current unload swallows event/signal disconnect failures, deletes concrete UI before service release, and clears the publication only after successful `release()`. Exact partial-failure, retry, and later-replacement ownership need direct proof.
- `language_changed` currently calls `_rebuild_dock_for_language()`, removes/re-adds the Dock through `LayoutManager`, rebuilds its concrete content, and may rebuild the fallback dialog. This loses Dock/content identity and duplicates the Host-owned title refresh authority established in E35-E38.
- The plugin is more than 2,000 lines and owns package filtering, install/uninstall/update operations, Project World manifest alignment, plugin runtime controls, menus, floating geometry, policy configuration, and fallback dialog behavior. E39 must not become a broad rewrite.

## Tasks

### Task 1 -- Red declaration, localization, and identity tests

- Prove exactly one JSON-safe `package_manager.surface` `dock_surface` containing only stable shell facts.
- Prove `LegacyEditorPluginAdapter` projects exactly one PackageManager Dock and treats declarative shell facts as authoritative while legacy/community fallback remains available.
- Prove `language_changed` refreshes the Host-owned Dock title in place and refreshes retained PackageManager content without `LayoutManager.remove_dock()/add_dock()`, Dock replacement, content replacement, duplicated signals, lost selection/filter state, or lost floating/docked geometry.
- Preserve Tools-menu opening, default hidden behavior, floating/docked policy, geometry restoration, fallback dialog, package list/filter/selection, runtime controls, and Project World command behavior.

### Task 2 -- Exact runtime event, kernel signal, and service ownership

- Record the exact four event subscriptions as they succeed. Failed activation must roll back only successfully acquired subscriptions in reverse order; failed unsubscribe remains retained for a later retry.
- Record exact `plugin_loaded` and `plugin_unloaded` signal connections. Partial connection/disconnection failures must preserve exact ownership evidence and not create duplicate callbacks after retry/reload.
- Treat the single `PACKAGE_CATALOG` + `PACKAGE_OPERATIONS` publication lease as an exact resource. Acquire only after domain services exist, release before deleting concrete UI/domain references, preserve later replacement owners, retain failed release state for retry, and do not mask the primary activation error if rollback also fails.
- Repeated load/unload/create/show paths must not accumulate subscriptions, signal connections, capability publications, Docks, dialogs, or UI signal bindings.

### Task 3 -- Minimal implementation at existing seams

- Add `editor_contribution` and one `package_manager.surface` declaration to `PackageManagerPlugin`.
- Keep `get_dock_config()` only as the legacy/community Host fallback; declarative Host projection must not depend on it.
- Replace Dock reconstruction on localization with a small in-place content retranslation Module inside the existing plugin. Retain only the widget references needed to update visible localized text; do not invent a widget DSL or split the entire plugin.
- Keep Package catalog/operations implementations and Project World orchestration unchanged except for the minimum exact-lifecycle bookkeeping required by red tests.
- Preserve all package manifests, project manifests, package transaction/recovery/interlock semantics, plugin runtime operations, `.pond`, AI Command, Inspector, SR2D, Player/export, startup/reload/shutdown, and current adapter fallback behavior.

### Task 4 -- Regression and closure

- Run the E39 test file plus existing PackageManager PyQt adapter, Host capability, filters, Package catalog/domain, Project World, Dock contract/projection, reload/shutdown/localization/layout/startup regressions.
- Run protected `.pond`/AI Command/Inspector/SR2D/viewport/Player/export/manifest/package transaction/interlock regressions.
- Run the complete non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact blocker; do not install dependencies silently.
- Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md` only after fresh evidence exists.
- Name exactly one next Gate. Do not widen E39 into PS Experiment, SimulationControl, viewport, theme, replacement Host selection, or whole-engine completion.

## Completion bar

E39 is complete only when PackageManager's shell is Qt-free and Host-projected, localization preserves Dock/content/layout identity, exact event/signal/service resources survive failure/retry/reload/shutdown without leaks or replacement-owner damage, and protected package/Project World behavior plus the complete evidence chain remain green.

E39 does not prove replacement-Host PackageManager content parity, complete Dock migration, viewport/theme migration, native GPU/OpenGL default readiness, signature provisioning, or whole-engine completion.


## Implementation result

- Added exactly one JSON-safe `package_manager.surface` `dock_surface` and `editor_contribution` capability while keeping `LegacyEditorPluginAdapter` as the concrete PyQt projection Adapter.
- Removed PackageManager's language-time Dock reconstruction. The Host now retains the Dock shell and refreshes its title; `PackageManagerPlugin.retranslate_ui()` updates retained content in place without replacing the Dock, list, search query, filter indexes, tab index, selection, open mode, or floating geometry.
- Retained explicit widget/action references only where required for in-place retranslation. No widget DSL, second Dock framework, catalog, registry, Host, or composition root was introduced.
- The plugin now records the exact four runtime event subscriptions, exact two kernel signal connections, and exact combined `PACKAGE_CATALOG` + `PACKAGE_OPERATIONS` publication lease. Partial activation failure rolls back acquired resources in reverse order; incomplete release retains exact retry state; repeated unload is idempotent; later replacement owners remain preserved by the existing publication Module.
- The existing Package domain, Project World operations and manifest alignment, package install/update/uninstall transactions, plugin runtime controls, Tools menu, fallback dialog, floating/docked policy, and legacy/community fallback were preserved.

## Verification evidence

- Initial E39 red: `9 failed in 0.42s`.
- Final E39 lifecycle/declaration/localization file: `9 passed in 0.22s` (the first green run was `9 passed in 0.27s`).
- Focused PackageManager/Dock regression: `68 passed in 1.51s`.
- Expanded Package/Project World/Host/reload/shutdown/Dock regression: `247 passed, 2 skipped, 17 subtests passed in 9.61s`.
- Fresh complete non-signature suite: `1498 passed, 34 skipped, 34 subtests passed in 178.89s`.
- `compileall` passed. Architecture guardrails reported `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Real offscreen Editor smoke: `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; discovery errors and failed plugins were zero; PackageManager was added once and removed once during deterministic reverse shutdown.
- Signature-only collection remains blocked at `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.19s`. No dependency was installed and signature verification is not claimed.

## Stable versus unfinished

Stable for this bounded Gate: one Qt-free PackageManager Dock shell declaration; authoritative Host projection; Host-owned title refresh; retained content retranslation; exact event/signal/publication acquisition, rollback, release, retry, and idempotency; preserved Package and Project World semantics.

Five of eight in-scope built-in Dock providers are now declarative: Inspector, Hierarchy, ProjectBrowser, Console, and PackageManager. This is `5/8 = 62.5%` of the Dock-shell migration only, not 62.5% of the engine. Concrete PackageManager content remains a PyQt legacy Host Adapter bridge; replacement-Host content parity, the remaining PsExperiment/SimulationControl/EcologyDashboard Dock providers, viewport/theme migration, native GPU/OpenGL default readiness, signature provisioning, and whole-engine completion remain open.

## Unique next Gate

Phase E40 -- Qt-Free PsExperiment Dock Contribution and Exact Service/Panel Event Lifecycle. Preserve PS experiment/PVAEC execution, Project World bindings, runtime snapshot authority, cancellation, history/output behavior, and the recursive engine-plugin Host topology. Do not widen into SimulationControl, EcologyDashboard, viewport/theme, replacement Host selection, SR/PS tick unification, or another plugin/UI/service framework.
