# Phase E40 -- Qt-Free PsExperiment Dock Contribution and Exact Service/Panel Event Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the versioned product runtime boundary containing L2 capability/domain Modules, L3 engine extension / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. `LegacyEditorPluginAdapter` remains the current concrete PyQt Host Adapter. `PsExperimentPlugin` is an engine extension inside the VitaLoom plugin framework and is activated according to the existing package/Project World model; it is not a peer FrameCore plugin or another engine root.

Reuse the existing `dock_surface`, runtime capability publication, PS experiment, runtime snapshot, Project World, event, command, and layout seams. Do not create a second Host, registry, PS runtime authority, service registry, manifest authority, composition root, Dock/UI framework, widget DSL, experiment framework, or replacement shell.

## Previous Gate

E39 completed the bounded PackageManager shell/lifecycle slice. Evidence: initial red `9 failed`; final E39 `9 passed`; focused `68 passed`; expanded `247 passed, 2 skipped, 17 subtests passed`; fresh full non-signature `1498 passed, 34 skipped, 34 subtests passed in 178.89s`; `compileall`; four green architecture guardrails; real offscreen Editor smoke `plugins=13/20` with zero discovery/load failures. Signature-only remains blocked because the exact repository `.venv` lacks `cryptography`.

Five of eight in-scope built-in Dock providers are now declarative: Inspector, Hierarchy, ProjectBrowser, Console, and PackageManager. This is `5/8 = 62.5%` of the Dock-shell migration only, not the engine.

## Audit truth

`PsExperimentPlugin` is the next bounded project/package-activated Dock slice. It belongs to the `vitalloom.pvaec.simulation` capability package inside the VitaLoom L1 runtime and must remain governed by the existing recursive/project-scoped Host topology.

Current facts:

- `PsExperimentPlugin` provides only `dock`; it has no Qt-free `editor_contribution` or `dock_surface` declaration.
- Its stable shell is `PsExperiment`, right placement, default hidden, closeable, tabbed with `EcologyDashboard`, with localized title key `ps_experiment.dock_title` and default `莲池演化实验`.
- `on_load()` constructs `PsExperimentService`, binds the Editor context, creates `PsRuntimeSnapshotHostAdapter`, and publishes `PS_EXPERIMENT` plus `PS_RUNTIME_SNAPSHOT_HOST` in one lease owned by `adapter.ps-experiment`.
- `PsExperimentService.bind_editor_context()` internally subscribes to `project_opened`; `unbind_editor_context()` currently swallows unsubscribe failures and clears ownership evidence, so failed teardown cannot be retried exactly.
- `PsExperimentPanel` directly subscribes to `project_opened`, `ps_experiment_finished`, and `ps_experiment_config_changed` during construction and does not unsubscribe. Recreated panels can therefore duplicate callbacks and retain concrete PyQt panel instances through the event bus.
- The panel has no `language_changed` subscription and no in-place `retranslate_ui()`. Most translatable labels, groups, and buttons are local variables, so retained content cannot currently be localized without rebuilding.
- `on_unload()` requests cancellation for a running experiment, unbinds the service, releases the capability lease, clears references, and deletes the Dock, but partial cancellation/unbind/release failure ordering, retry state, repeated unload, and later replacement ownership need direct proof.
- The underlying PS/PVAEC execution, `PsExperimentConfig`, Project World preset/default commands, history/output discovery, metric comparison, runtime snapshot authority, event publication, and SR/PS separation are existing domain behavior and are outside a broad rewrite.

## Tasks

### Task 1 -- Red declaration, projection, localization, and identity tests

- Prove exactly one JSON-safe `ps_experiment.surface` `dock_surface` containing only stable shell facts.
- Prove `LegacyEditorPluginAdapter` projects exactly one PsExperiment Dock and treats the declaration as shell authority while legacy/community fallback remains available.
- Add retained `PsExperimentPanel.retranslate_ui()` coverage. Language refresh must preserve Dock/panel identity, preset selection, form values, history/baseline selection, run/cancel state, output/history paths, and tab/layout identity.
- Keep Dock title localization Host-owned. Concrete panel text may be refreshed through one exact plugin-owned `language_changed` subscription; do not remove/re-add the Dock.

### Task 2 -- Exact panel event ownership

- Move the panel's direct event-bus subscriptions behind explicit plugin-owned exact subscription records, or provide an equally explicit retryable ownership Module without creating another framework.
- Own `project_opened`, `ps_experiment_finished`, and `ps_experiment_config_changed` only while the retained panel exists; add `language_changed` for content retranslation.
- Prove partial subscription failure rollback, failed unsubscribe retry, repeated `create_dock_widget()`, reload/unload/shutdown idempotency, and absence of callbacks into deleted panels.
- Preserve the service's separate legitimate `project_opened` binding for project preset/default auto-load; do not collapse panel presentation refresh into the PS domain service.

### Task 3 -- Exact service binding/publication lifecycle

- Treat the service Editor-context binding and the combined `PS_EXPERIMENT` + `PS_RUNTIME_SNAPSHOT_HOST` publication as exact activation resources.
- Acquire in an explicit order and release in reverse order. On partial activation failure, roll back only resources actually acquired and keep the primary activation error authoritative while recording rollback failure.
- Make failed service unbind/publication release retryable without clearing exact ownership evidence. Repeated unload must be idempotent and must preserve capabilities later replaced by another owner.
- Keep cancellation behavior honest: request cancellation when running, but do not claim worker termination or erase teardown evidence if cancellation/unbind/release fails.

### Task 4 -- Preserve PS/PVAEC and Project World semantics

- Preserve `ps.experiment.smoke`, `project.set_ps_experiment_preset`, and `project.set_evolution_defaults` command flows.
- Preserve PVAEC runner configuration, experiment state/events, history/output browsing, metric comparison, runtime organism snapshot reads, and the existing SR/PS separation/interlock policy.
- Do not move PS domain logic into PyQt widgets, FrameCore, `LegacyEditorPluginAdapter`, or a new service/registry authority.

### Task 5 -- Verification and closure

- Start with a dedicated E40 red test file, then run existing PS panel/service/snapshot/capability tests and Dock/Host/reload/shutdown regressions.
- Run protected PVAEC/Project World/command/runtime snapshot groups, the complete non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact blocker; do not install dependencies silently.
- Update `docs/mainline_status.md`, this plan, `CONTEXT.md`, `docs/INDEX.md`, and a fresh-session prompt.
- Name exactly one next Gate. Do not widen E40 into SimulationControl, EcologyDashboard, viewport/theme, replacement Host selection, SR/PS tick unification, native rendering, or whole-engine completion.

## Completion boundary

E40 is complete only when the PsExperiment shell is declarative, Host projection/title localization is authoritative and in place, retained panel content localizes without reconstruction, panel/service/publication resources have exact rollback/retry evidence, PS/PVAEC and Project World semantics remain green, and the verification ladder is recorded.

E40 does not prove replacement-Host PsExperiment content parity, complete Dock migration, unified SR/PS tick, viewport/theme migration, native GPU/OpenGL default readiness, signature provisioning, or whole-engine completion.

## Implementation result

- Added exactly one JSON-safe `ps_experiment.surface` `dock_surface` and `editor_contribution` capability. `LegacyEditorPluginAdapter` remains the concrete PyQt projection Adapter, and `get_dock_config()` remains only the legacy/community fallback.
- `PsExperimentPanel` no longer subscribes to the event bus. `PsExperimentPlugin` now owns the exact `project_opened`, `ps_experiment_finished`, `ps_experiment_config_changed`, and `language_changed` subscriptions only while the retained panel exists, with reverse rollback/release and retryable failure state.
- Added in-place `PsExperimentPanel.retranslate_ui()` using only retained concrete widget references. It preserves Dock/panel identity, preset/history/baseline selection, form values, checkbox and run/cancel state, dynamic status, and output/history state; no widget DSL or second UI framework was introduced.
- `PsExperimentService.bind_editor_context()` and `unbind_editor_context()` now form an exact retryable binding lifecycle. Failed subscribe clears incomplete ownership; failed unsubscribe preserves context/handler evidence for retry; repeated unbind is idempotent.
- The combined `PS_EXPERIMENT` + `PS_RUNTIME_SNAPSHOT_HOST` publication, service binding, panel events, and running-experiment cancellation now have direct partial-failure/retry/idempotency tests. The existing publication lease preserves later replacement owners.
- PS/PVAEC execution, `PsExperimentConfig`, Project World preset/default command flows, history/output/metric comparison, runtime snapshot authority, SR/PS separation/interlock, package activation, and legacy/community fallback remain unchanged.

## Verification evidence

- Initial E40 red: `8 failed, 1 passed in 0.81s`.
- Final E40 lifecycle/declaration/localization file: `9 passed in 0.50s`.
- Existing PS/Dock/Host/capability regression: `120 passed in 2.40s`.
- Protected PVAEC/Project World/commands/runtime snapshot/reload/shutdown/SR-PS regression: `289 passed in 8.52s`.
- Fresh complete non-signature suite: `1507 passed, 34 skipped, 34 subtests passed in 164.46s`.
- Modified-Module `compileall` passed. Architecture guardrails reported `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Real offscreen Editor smoke: `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; discovery errors were zero and deterministic reverse shutdown completed.
- Signature-only collection remains blocked at `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.30s`. No dependency was installed and signature verification is not claimed.

## Stable versus unfinished

Stable for this bounded Gate: one Qt-free PsExperiment Dock shell declaration; authoritative Host projection/title refresh; retained panel content retranslation; exact panel-event, service-binding, combined-publication, cancellation, rollback, release, retry, and idempotency evidence; preserved PS/PVAEC and Project World semantics.

Six of eight in-scope built-in Dock providers are now declarative: Inspector, Hierarchy, ProjectBrowser, Console, PackageManager, and PsExperiment. This is `6/8 = 75%` of the Dock-shell migration only, not 75% of the engine. Concrete PsExperiment content remains a PyQt legacy Host Adapter bridge. SimulationControl and EcologyDashboard shell migration, replacement-Host content parity, viewport/theme migration, native GPU/OpenGL default readiness, signature provisioning, and whole-engine completion remain open.

## Unique next Gate

Phase E41 -- Qt-Free SimulationControl Dock Contribution and Exact Transport-State/Localization Lifecycle. Preserve `SimulationTransport` as the sole play/pause/stop authority, preserve canonical `simulation.*` commands, StandardUI toolbar state, GameViewport behavior, speed/parameter signals, SR/PS separation/interlock, and the recursive engine-plugin Host topology. Do not widen into EcologyDashboard, viewport/theme, replacement Host selection, tick unification, another transport/UI/plugin framework, or whole-engine completion.

