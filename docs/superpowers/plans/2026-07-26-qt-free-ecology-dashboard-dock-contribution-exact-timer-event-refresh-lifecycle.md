# Phase E42 -- Qt-Free EcologyDashboard Dock Contribution and Exact Timer/Event Refresh Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

`FrameCore` remains the sole L0 root framework. `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` remains the product runtime containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons.

`NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. `LegacyEditorPluginAdapter` remains the current concrete PyQt Host Adapter. `EcologyDashboardPlugin` is only an L3 Dock/observation extension. `collect_ecology_snapshots` and the existing SR/PS ecology providers remain observation authorities; the Dock must not become another simulation registry, tick owner, snapshot authority, or engine root.

Reuse the existing `dock_surface`, event bus, ecology registry, `EcologyLane`, comparability policy, and localization seams. Do not create a second Host, registry, observation system, event transport, timer framework, Dock/UI framework, widget DSL, composition root, manifest authority, peer L1 engine plugin, replacement shell, or unified SR/PS tick.

## Previous Gate

E41 completed the bounded SimulationControl shell/lifecycle slice. Evidence: initial red `6 failed`; final E41 `6 passed`; related `100 passed`; protected `670 passed, 15 skipped`; fresh full non-signature `1513 passed, 34 skipped, 34 subtests passed in 160.10s`; modified-Module compile and four guardrails green; real offscreen Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography`.

Seven of eight in-scope built-in Dock providers are declarative. This is `7/8 = 87.5%` of Dock-shell migration only, not the engine.

## Audit truth

- `EcologyDashboardPlugin` currently provides only `dock`; it has no Qt-free `editor_contribution` or declarative `dock_surface`.
- Stable shell facts are `EcologyDashboard`, right placement, default hidden, closeable, and default title `生态统计`. Float/move semantics are currently implicit and must remain compatible.
- `create_dock_widget()` always creates a new Dock and does not retain the Panel separately. `on_unload()` schedules deletion but does not clear references or prove repeated create/unload idempotency.
- `EcologyDashboardPanel` starts a 400 ms `QTimer` and directly subscribes three anonymous lambdas to `ps_experiment_state`, `ps_experiment_finished`, and `simulation_transport_state`. The callbacks cannot be precisely unsubscribed; unload can leave stale callbacks into deleted content.
- The Panel stores title/hint widgets only as locals, has no in-place `retranslate_ui()`, and uses no existing localization seam for its static content.
- Snapshot aggregation is already centralized in `collect_ecology_snapshots`. SR play, PS batch, PS replay filtering, and comparability rendering are existing domain behavior and must remain unchanged.

## Tasks

### Task 1 -- Red shell projection and retained localization tests

- Prove exactly one JSON-safe `ecology_dashboard.surface` `dock_surface` containing only stable shell facts.
- Prove `LegacyEditorPluginAdapter` projects exactly one Dock, owns title localization in place, and treats declarative shell facts as authoritative while legacy/community fallback remains available.
- Prove retained Panel static title/hint localization does not rebuild Dock/Panel/labels, replace the timer, or overwrite current ecology output.

### Task 2 -- Exact timer and event refresh lifecycle

- Move the three anonymous event subscriptions out of the Panel and into the plugin with exact callback records.
- Prove acquisition order, reverse release, partial subscription rollback, failed-unsubscribe retry, repeated create/unload idempotency, and no callback into deleted content.
- Treat the Panel's 400 ms timer as an exact retained resource: stop it on rollback/unload, retain retry state if stopping fails, and destroy content only after all exact resources are released.
- Keep timer refresh and event refresh presentation-only; do not move tick or snapshot authority into the plugin.

### Task 3 -- Preserve ecology observation semantics

- Preserve `collect_ecology_snapshots`, `EcologyLane.SR_PLAY`, `EcologyLane.PS_BATCH`, PS replay filtering, comparability gating/lines, 30 retained output rows, error fallback, and current 400 ms cadence.
- Preserve GameViewport SR publication, PsExperiment event flows, SR/PS separation/interlock, Project World/package behavior, and legacy/community Host fallback.

### Task 4 -- Verification and closure

- Run the dedicated E42 red/final suite, existing ecology/comparability/PS/SR/GameViewport/Dock/Host/reload/shutdown regressions, protected cross-domain groups, complete non-signature suite, modified-Module `compileall`, four architecture guardrails, and real offscreen Editor smoke.
- Run signature-only collection and record the exact environment blocker without installing dependencies silently.
- Update `docs/mainline_status.md`, this plan, `CONTEXT.md`, `docs/INDEX.md`, and fresh-session prompts.
- Name exactly one next Gate. Do not widen E42 into viewport/theme migration, replacement Host selection, SR/PS tick unification, native rendering, signature provisioning, or whole-engine completion.

## Completion boundary

E42 is complete only when the EcologyDashboard shell is declarative, Host title projection is authoritative and in place, retained Panel content localizes without reconstruction, anonymous subscriptions are eliminated, timer/event resources have exact rollback/retry/idempotency evidence, and ecology observation/comparability semantics remain green.

E42 does not prove replacement-Host content parity, viewport/theme migration, unified SR/PS tick, native GPU/OpenGL default readiness, signature provisioning, or whole-engine completion.

## Completion evidence

- Initial dedicated red line: `7 failed in 0.25s`.
- Final E42 dedicated shell/timer/event suite: `7 passed in 0.22s`.
- Related ecology/comparability/PS/SR/Dock/Host regression: `133 passed in 4.67s`.
- Protected command/GameViewport/PVAEC/Project World/reload/shutdown/runtime-snapshot/SR-PS/ecology group: `697 passed, 15 skipped in 29.88s`.
- Fresh complete non-signature suite: `1520 passed, 34 skipped, 34 subtests passed in 185.73s`.
- Modified Modules/tests pass `compileall`; all four architecture guardrails report OK.
- Real offscreen Editor smoke reports `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`, zero discovery errors, and deterministic reverse shutdown.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` with `1 error in 0.18s`. No dependency was installed and signature verification is not claimed.

All eight in-scope built-in Dock providers now have declarative Qt-free shell contributions. `8/8 = 100%` is only Dock-shell migration; concrete content remains current PyQt Host Adapter bridges and the engine remains unfinished.

**Unique next Gate: Phase E43 -- Qt-Free Viewport Contribution Contract and Host-Owned CellEditor Surface Projection.** First deepen the existing editor contribution Interface with portable viewport shell facts and migrate only the bounded CellEditor shell as the initial vertical slice. Preserve `IViewportProvider` legacy/community fallback, current layout switching, CellEditor enter/exit semantics, recursive Host topology, and all Qt-free L0-L4 engine-plugin contracts. Do not select or build a replacement app shell, migrate Scene/GameViewport content, or create a second Host, viewport registry, rendering framework, composition root, or peer L1 engine root.
