# Phase E38 -- Qt-Free Console Dock Contribution and Exact Logging/Capability Adapter Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the versioned product runtime boundary containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain Host authorities. `PluginLoader` remains a compatibility facade. `LegacyEditorPluginAdapter` remains the current PyQt Host Adapter. Reuse the existing `dock_surface` Interface and canonical capability publication seam; do not create a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, logging framework, capability registry, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell.

## Previous Gate

E37 is complete for the bounded ProjectBrowser shell/lifecycle slice. Evidence: initial red `5 failed`; final E37 file `6 passed`; focused `45 passed`; expanded `140 passed`; protected `327 passed, 16 skipped`; fresh full non-signature `1476 passed, 34 skipped, 34 subtests passed`; `compileall`; clean Editor smoke `plugins=13/20`; all four guardrails green. Signature-only remains blocked by missing `cryptography` in the exact repository `.venv`.

## Audit target

`ConsolePlugin` is the next bounded Dock slice. Its stable shell facts are Console identity, localized title, bottom placement, default visibility, close behavior, and tabification with Project. It currently subscribes to `language_changed` only to mutate the concrete Dock title, which duplicates the Host Adapter refresh authority established in E35-E37.

Console content also owns a concrete PyQt bridge: after constructing `ConsolePanel`, it publishes `UI_CONSOLE_PANEL` and attaches the logging bridge. Unload releases the logging handler and capability publication, but exact acquire/release ordering, partial-failure rollback, repeated construction, reload, and shutdown behavior need direct proof. This phase must deepen that existing Adapter lifecycle without moving logging or UI capability authority into a new framework.

## Tasks

### Task 1 -- Red shell and adapter-lifecycle tests

- Prove that Console declares exactly one `console.surface` Qt-free `dock_surface` containing stable shell facts only.
- Prove the current Adapter projects exactly one Console Dock, treats declarative shell facts as authoritative, and preserves delayed tabification with Project.
- Prove `language_changed` refreshes the Dock title in place without plugin-owned `setWindowTitle()`, Dock reconstruction, duplicate Dock creation, or layout identity loss.
- Prove `UI_CONSOLE_PANEL` publication and logging-handler attachment are acquired once for the retained ConsolePanel and released exactly once in safe order on replacement, unload, reload, shutdown, and partial failure.
- Prove failed activation/construction leaves no stale event subscription, capability publication, logging handler, Dock, or panel reference.
- Preserve console append/filter/clear behavior, capability consumers, logging output, Project tabification, legacy/community fallback, and deterministic Host shutdown.

### Task 2 -- Deepen ownership at existing seams

- Add only the Console `dock_surface` declaration and minimum lifecycle bookkeeping required by the red tests.
- Let `LegacyEditorPluginAdapter` own shell title refresh from `refresh_events`; remove the plugin's direct Dock-title mutation and any now-redundant language event ownership.
- Keep concrete `ConsolePanel`/`QDockWidget` construction, `UI_CONSOLE_PANEL` publication, and logging attachment as an explicit current Host Adapter/content bridge. Do not claim replacement-Host content parity.
- Make acquisition and teardown transactional: on any later failure, unwind only resources acquired by the current Console instance, in reverse order, without masking the primary failure.
- Do not add a second logging bridge, UI capability key, service registry, event bus, Dock registry, or replacement shell.

### Task 3 -- Regression and closure

- Run focused E38 red/green tests, Dock contract/projection regression, Console/logging/capability consumer regression, expanded Host/reload/shutdown/localization/layout/startup regression, and protected Project World/`.pond`/AI Command/Inspector/SR2D/viewport/Player/export/manifest regression.
- Run the full non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact result; do not install dependencies silently.
- Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md` only after fresh evidence exists.
- Name exactly one next Gate. Do not widen E38 into PackageManager, PS Experiment, SimulationControl, viewport, theme, replacement Host selection, or whole-engine completion.

## Completion bar

E38 is complete only when the Console shell is declared Qt-free, the current Adapter projects and localizes it in place, Console capability/logging resources have exact transactional lifecycle ownership, protected consumers and logging behavior remain green, and the full evidence chain closes.

E38 does not prove replacement-Host Console content parity, complete Dock migration, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or whole-engine completion.


## Completion evidence

- Initial red line: `10 failed`, covering missing `console.surface`, missing `editor_contribution`, duplicate panel event ownership, plugin-owned Dock title mutation, swallowed publication/logging failures, missing exact resource identity, repeated-construction leakage, and missing teardown retry.
- Final E38 lifecycle file: `13 passed`. Joint Console/capability lifecycle: `21 passed`. Focused Dock/Console/Hierarchy/ProjectBrowser regression: `44 passed`. Expanded Host/lifecycle/reload/shutdown/localization/layout/startup regression: `130 passed, 1 skipped`.
- Fresh complete non-signature regression after the final three failure-path tests: `1489 passed, 34 skipped, 34 subtests passed in 172.43s`.
- Modified Modules pass `compileall`. `check_project_plugin_model.py`, `check_core_boundaries.py`, `check_gui_boundaries.py`, and `check_release_consistency.py` are green.
- Real offscreen Editor smoke passes with zero discovery errors and `plugins=13/20`; Console is projected once and removed deterministically during reverse shutdown.
- Signature-only collection remains blocked at `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.29s`). No dependency was installed and package-signature verification is not claimed.

## Stable versus unfinished

Stable for this bounded Gate: one Qt-free `console.surface`; Host-owned in-place Dock-title refresh; retained `ConsolePanel.retranslate_ui()` content refresh; exact event subscription ownership and retry; exact `UI_CONSOLE_PANEL` publication plus logging-handler acquire/reverse-release; partial-failure rollback and retry; replacement-owner preservation; repeated create/unload idempotency; Project tabification and legacy/community fallback.

Still unfinished: concrete Console content remains a PyQt legacy Host Adapter bridge; replacement-Host content parity is not proven; four of eight in-scope built-in Dock providers remain undeclared; viewport/theme contribution migration, replacement UI Host implementation, native GPU/OpenGL default readiness, signature provisioning, and whole-engine completion remain open.

## Unique next Gate

Phase E39 -- Qt-Free PackageManager Dock Contribution and In-Place Localization/Exact Service Lifecycle. Preserve the existing Package domain and Project World command semantics, floating/open-mode behavior, package catalog/operations publication seams, and recursive engine-plugin Host topology. Do not widen into PS Experiment, SimulationControl, viewport, theme, replacement Host selection, or a second plugin/UI/service framework.
