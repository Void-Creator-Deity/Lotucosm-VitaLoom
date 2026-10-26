# Phase E41 -- Qt-Free SimulationControl Dock Contribution and Exact Transport-State/Localization Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the versioned product runtime containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. `LegacyEditorPluginAdapter` remains the current concrete PyQt Host Adapter. `SimulationTransport` remains the sole simulation play/pause/stop and state authority; `SimulationControlPlugin` is only an L3 Dock extension and must not become another transport, command authority, engine root, or app shell.

Reuse the existing `dock_surface`, event bus, canonical `simulation.*` commands, `SimulationTransport`, StandardUI toolbar, GameViewport, layout, and localization seams. Do not create a second Host, transport, registry, command system, simulation coordinator, manifest authority, composition root, Dock/UI framework, widget DSL, peer L1 engine plugin, or replacement shell.

## Previous Gate

E40 completed the bounded PsExperiment shell/lifecycle slice. Evidence: initial red `8 failed, 1 passed`; final E40 `9 passed`; related `120 passed`; protected `289 passed`; fresh full non-signature `1507 passed, 34 skipped, 34 subtests passed in 164.46s`; compile and four architecture guardrails green; real offscreen Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography`.

Six of eight in-scope built-in Dock providers are declarative. This is `6/8 = 75%` of Dock-shell migration only, not the engine.

## Audit truth

- `SimulationControlPlugin` currently provides only `dock`; it has no Qt-free `editor_contribution` or `dock_surface` declaration.
- Its stable shell is `SimulationControl`, left placement, default hidden, closeable, and tabbed with `Hierarchy`; the localized Dock title key is `sim_control.dock_title` with default `模拟`.
- `on_load()` directly subscribes to `simulation_transport_state` and `language_changed`. `on_unload()` performs both unsubscribes inside one swallowed `try`, so the first failure can hide the second resource and neither failure remains retryable.
- `create_dock_widget()` always constructs a new Dock/panel and the plugin retains only `panel`; repeated creation, failed subscription rollback, unload deletion, and stale callback prevention lack direct proof.
- `_on_language_changed()` is a no-op. `SimulationControlPanel` has localized groups, buttons, form labels, and hint text stored mostly as locals and has no in-place `retranslate_ui()`.
- The Panel uses the existing global Editor context and `SimulationTransport`; play/pause/stop first delegate to the transport and only fall back to Qt signals. Speed and parameter signals are existing behavior. E41 must not rewrite those domain/control flows or merge PS and SR ticks.

## Tasks

### Task 1 -- Red declaration, projection, identity, and localization tests

- Prove exactly one JSON-safe `simulation_control.surface` `dock_surface` containing only stable shell facts.
- Prove `LegacyEditorPluginAdapter` projects exactly one Dock, owns title localization, and treats the declaration as shell authority while legacy/community fallback remains available.
- Prove retained `SimulationControlPanel.retranslate_ui()` updates static text in place without replacing Dock/panel/widgets or changing speed, FPS, time step, auto-save, button enablement, or dynamic transport status.

### Task 2 -- Exact plugin event and panel ownership

- Record exact successful subscriptions for `simulation_transport_state` and `language_changed`.
- Prove partial subscription failure rollback, reverse unsubscribe, failed unsubscribe retry, repeated create/unload idempotency, and no callback into deleted panels.
- Keep transport state consumption presentation-only. Do not move simulation state authority into the plugin or Panel.

### Task 3 -- Preserve transport, commands, and SR/PS semantics

- Preserve `SimulationTransport`, canonical `simulation.play`, `simulation.toggle_pause`, `simulation.pause`, and `simulation.stop` flows.
- Preserve StandardUI toolbar dynamic action state, GameViewport play/pause/stop behavior, speed and parameter signals, project/session behavior, and SR/PS separation/interlock.
- Keep concrete PyQt construction inside the existing legacy Adapter/content bridge and do not introduce another simulation or UI framework.

### Task 4 -- Verification and closure

- Run a dedicated E41 red test file, existing SimulationControl/transport/toolbar/command/GameViewport/Dock/Host/reload/shutdown regressions, protected cross-domain groups, complete non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact environment blocker without installing dependencies silently.
- Update `docs/mainline_status.md`, this plan, `CONTEXT.md`, `docs/INDEX.md`, and fresh-session prompts.
- Name exactly one next Gate. Do not widen E41 into EcologyDashboard, viewport/theme, replacement Host selection, SR/PS tick unification, native rendering, or whole-engine completion.

## Completion boundary

E41 is complete only when the SimulationControl shell is declarative, Host projection/title localization is authoritative and in place, retained panel content localizes without reconstruction, exact event ownership has rollback/retry/idempotency evidence, and transport/command/GameViewport/SR-PS semantics remain green.

E41 does not prove EcologyDashboard migration, replacement-Host content parity, complete Dock migration, unified SR/PS tick, viewport/theme migration, native GPU/OpenGL default readiness, signature provisioning, or whole-engine completion.
## Completion evidence

- Initial dedicated red line: `6 failed in 0.26s`.
- Final E41 dedicated lifecycle/localization suite: `6 passed in 0.31s`.
- Existing transport/Dock/toolbar/command/GameViewport/Host/reload/shutdown regression: `100 passed in 2.27s`.
- Protected command/GameViewport/PVAEC/Project World/reload/shutdown/runtime-snapshot/SR-PS group: `670 passed, 15 skipped in 28.71s`.
- Fresh complete non-signature suite: `1513 passed, 34 skipped, 34 subtests passed in 160.10s`.
- Modified Modules pass `compileall`; all four architecture guardrails report OK.
- Real offscreen Editor smoke reports `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`, zero discovery errors, and deterministic reverse shutdown.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.37s`. No dependency was installed and signature verification is not claimed.

Seven of eight in-scope built-in Dock providers are now declarative. `7/8 = 87.5%` is only the Dock-shell migration status, not whole-engine completion.

**Unique next Gate: Phase E42 -- Qt-Free EcologyDashboard Dock Contribution and Exact Timer/Event Refresh Lifecycle.** Preserve `collect_ecology_snapshots`, SR/PS lane separation, comparability display, pull-based refresh, timer behavior, event-triggered refresh, legacy/community fallback, and the recursive engine-plugin Host topology. Do not merge SR/PS ticks or create another Host, registry, observation authority, timer framework, Dock/UI framework, replacement shell, or peer L1 engine root.

