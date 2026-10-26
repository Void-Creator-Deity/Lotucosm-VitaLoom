# Phase E42 Fresh-Session Prompt -- Qt-Free EcologyDashboard Dock Contribution and Exact Timer/Event Refresh Lifecycle

Date: 2026-07-26
Status: historical closure

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E41 plan, and the E42 plan before editing code.

## Architecture that must remain true

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` contains L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`EcologyDashboardPlugin` is an L3 observation/Dock extension inside that VitaLoom plugin framework. It is not a peer FrameCore plugin, another engine root, another snapshot registry, or another tick owner. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. PyQt and `LegacyEditorPluginAdapter` remain current/legacy Host Adapter details. `collect_ecology_snapshots` and current SR/PS providers remain observation authorities.

Do not create a second Host, registry, observation system, event transport, timer framework, Dock/UI framework, widget DSL, composition root, manifest authority, peer L1 engine plugin, replacement shell, or unified SR/PS tick.

## E41 closure truth

E41 is complete for the bounded SimulationControl slice: one `simulation_control.surface`, Host-owned title refresh, retained Panel retranslation, exact two-event lifecycle, and preserved `SimulationTransport`/command/toolbar/GameViewport authority.

Fresh evidence: final E41 `6 passed`; related `100 passed`; protected `670 passed, 15 skipped`; complete non-signature `1513 passed, 34 skipped, 34 subtests passed in 160.10s`; compile and four guardrails green; real Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography`.

Seven of eight in-scope built-in Dock providers are declarative. This is `87.5%` of Dock-shell migration only; the engine remains unfinished.

## Unique E42 Gate

1. Audit `EcologyDashboardPlugin`, `EcologyDashboardPanel`, ecology registry/providers, comparability policy, related events, and existing tests before editing.
2. Write red tests for one `ecology_dashboard.surface`, authoritative Host projection, retained content localization, exact three observation-event subscriptions, partial activation rollback, failed unsubscribe/timer-stop retry, repeated create/unload idempotency, and stale-callback prevention.
3. Make only minimum changes at existing seams. Preserve the 400 ms pull refresh, SR/PS lanes, replay filtering, comparability output, GameViewport/PsExperiment flows, and legacy/community behavior.
4. Close E42 with focused, protected, complete non-signature, compile, four guardrails, real offscreen Editor smoke, and explicit signature-blocker evidence.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The persistent whole-engine objective remains active.

## Closure truth

E42 is complete for its bounded slice. `EcologyDashboardPlugin` declares one `ecology_dashboard.surface`; `LegacyEditorPluginAdapter` remains the sole concrete Dock projection/title-localization Adapter; retained Panel title/hint content retranslates in place; and the plugin owns exact three observation-event plus one language-event subscriptions and the retained 400 ms timer with rollback/retry/idempotent teardown.

`collect_ecology_snapshots`, SR play/PS batch lane separation, PS replay filtering, comparability gating/lines, 30 output rows, and GameViewport/PsExperiment ownership remain unchanged. Evidence: initial red `7 failed`; final E42 `7 passed`; related `133 passed`; protected `697 passed, 15 skipped`; full non-signature `1520 passed, 34 skipped, 34 subtests passed in 185.73s`; compile, four guardrails, and Editor smoke `plugins=13/20` green. Signature-only remains blocked by missing `cryptography` (`1 error in 0.18s`).

All eight in-scope built-in Dock providers are declarative. This is 100% of Dock-shell migration only, not replacement-Host content parity or whole-engine completion.

**Unique next Gate: Phase E43 -- Qt-Free Viewport Contribution Contract and Host-Owned CellEditor Surface Projection.** Establish portable viewport shell facts through the existing contribution seam and migrate only CellEditor as the first bounded slice; preserve legacy/community fallback and do not build/select a replacement shell or migrate Scene/Game viewport content in the same phase.
