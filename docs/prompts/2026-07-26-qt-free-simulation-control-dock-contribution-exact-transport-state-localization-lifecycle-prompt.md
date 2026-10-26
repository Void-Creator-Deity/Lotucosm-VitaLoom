# Phase E41 Fresh-Session Prompt -- Qt-Free SimulationControl Dock Contribution and Exact Transport-State/Localization Lifecycle

Date: 2026-07-26
Status: historical closure

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E40 plan, and the E41 plan before editing code.

## Architecture that must remain true

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` contains L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`SimulationControlPlugin` is an L3 engine extension inside that VitaLoom plugin framework. It is not a peer FrameCore plugin, another engine root, another transport, or another app shell. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. PyQt and `LegacyEditorPluginAdapter` remain current/legacy Host Adapter details. `SimulationTransport` remains the sole play/pause/stop and state authority.

Do not create a second Host, transport, registry, command system, simulation coordinator, manifest authority, composition root, Dock/UI framework, widget DSL, peer L1 engine plugin, or replacement shell.

## E40 closure truth

E40 is complete for the bounded PsExperiment slice: one `ps_experiment.surface`, Host-owned in-place title refresh, retained panel retranslation, exact panel-event/service-binding/combined-publication lifecycle, and preserved PS/PVAEC/Project World behavior.

Fresh evidence: final E40 `9 passed`; related `120 passed`; protected `289 passed`; complete non-signature `1507 passed, 34 skipped, 34 subtests passed in 164.46s`; compile and four architecture guardrails green; real Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography`.

Six of eight in-scope built-in Dock providers are declarative. This is 75% of Dock-shell migration only; the engine remains unfinished.

## Unique E41 Gate

1. Audit `SimulationControlPlugin`, `SimulationControlPanel`, `SimulationTransport`, canonical `simulation.*` commands, StandardUI toolbar state, GameViewport consumption, and existing tests before editing.
2. Write red tests for one `simulation_control.surface`, authoritative Host projection, retained in-place panel localization, exact two-event ownership, partial activation rollback, failed unsubscribe retry, repeated create/unload idempotency, and stale-callback prevention.
3. Make only the minimum changes at existing seams. Keep `SimulationTransport` authoritative and preserve command, toolbar, GameViewport, speed/parameter, SR/PS separation/interlock, and legacy/community behavior.
4. Close E41 with focused, protected, complete non-signature, compile, four guardrails, real offscreen Editor smoke, and explicit signature-blocker evidence.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The persistent whole-engine objective remains active.
## Closure truth

E41 is complete for its bounded slice. `SimulationControlPlugin` declares one `simulation_control.surface`; `LegacyEditorPluginAdapter` remains the sole concrete Dock projection/title-localization Adapter; the retained Panel retranslates static content in place; and the plugin owns exact retryable `simulation_transport_state` / `language_changed` subscriptions with partial-failure rollback and idempotent unload.

`SimulationTransport` remains the sole play/pause/stop and state authority. Canonical `simulation.*` commands, StandardUI toolbar state, GameViewport behavior, speed/parameter signals, and SR/PS separation/interlock remain green.

Evidence: initial red `6 failed`; final E41 `6 passed`; related `100 passed`; protected `670 passed, 15 skipped`; complete non-signature `1513 passed, 34 skipped, 34 subtests passed in 160.10s`; modified-Module compile and four guardrails green; real Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography` (`1 error in 0.37s`).

Seven of eight in-scope built-in Dock providers are declarative. This is `87.5%` of Dock-shell migration only; the engine remains unfinished.

**Unique next Gate: Phase E42 -- Qt-Free EcologyDashboard Dock Contribution and Exact Timer/Event Refresh Lifecycle.** Audit the existing Panel-owned anonymous event subscriptions and timer first. Preserve ecology registry snapshots, SR/PS lane separation, comparability output, and legacy/community behavior; do not unify ticks or create another Host, registry, observation authority, UI framework, or replacement shell.

