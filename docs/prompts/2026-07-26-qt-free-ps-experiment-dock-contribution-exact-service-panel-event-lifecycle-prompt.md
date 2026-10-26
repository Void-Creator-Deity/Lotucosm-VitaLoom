# Phase E40 Fresh-Session Prompt -- Qt-Free PsExperiment Dock Contribution and Exact Service/Panel Event Lifecycle

Date: 2026-07-26
Status: completed; historical closure and E41 handoff

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E39 plan, and the E40 plan before editing code.

## Architecture that must remain true

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` contains L2 capability/domain Modules, L3 engine extension / Host Adapters, and L4 Project World addons.

`PsExperimentPlugin` is an engine extension inside that VitaLoom plugin framework, activated through the existing package and Project World model. It is not a peer FrameCore plugin, another root engine, or another app shell. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. PyQt and `LegacyEditorPluginAdapter` remain current/legacy Host Adapter details.

Do not create a second Host, registry, PS runtime authority, service registry, manifest authority, composition root, Dock/UI framework, widget DSL, experiment framework, peer L1 engine plugin, or replacement shell.

## E39 closure truth

E39 is complete for the bounded PackageManager slice: one Qt-free `package_manager.surface`, Host-owned in-place title refresh, retained PackageManager content localization, exact four-event/two-signal/combined-publication lifecycle, and preserved Package/Project World behavior.

Fresh evidence: final E39 `9 passed`; focused `68 passed`; expanded `247 passed, 2 skipped, 17 subtests passed`; complete non-signature `1498 passed, 34 skipped, 34 subtests passed in 178.89s`; compile and four architecture guardrails green; real offscreen Editor smoke `plugins=13/20` with zero discovery failures. Signature-only remains blocked by missing `cryptography`.

Five of eight in-scope built-in Dock providers are declarative. This is 62.5% of Dock-shell migration only; the engine remains unfinished.

## Unique E40 Gate

1. Audit `PsExperimentPlugin`, `PsExperimentPanel`, `PsExperimentService`, `PsRuntimeSnapshotHostAdapter`, their package/Project World activation path, and existing tests before editing.
2. Write red tests for one `ps_experiment.surface`, authoritative Host projection, retained Dock/panel localization identity, exact panel event subscriptions, exact service Editor-context binding, and exact combined `PS_EXPERIMENT`/`PS_RUNTIME_SNAPSHOT_HOST` publication lifecycle.
3. Remove panel-owned leaking event subscriptions or replace them with one explicit retryable ownership seam. Preserve the service's separate project-open auto-load responsibility.
4. Add minimal in-place panel retranslation by retaining only the necessary concrete widget references. Do not rebuild the Dock/panel and do not create a widget DSL.
5. Preserve PS/PVAEC execution, cancellation, Project World preset/default commands, history/output/metrics, runtime snapshot authority, SR/PS separation, and legacy/community Host compatibility.
6. Close E40 with focused, protected, complete non-signature, compile, four guardrails, real offscreen Editor smoke, and explicit signature-blocker evidence.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The persistent whole-engine objective remains active.

## E40 closure evidence

E40 is complete for its bounded slice: one `ps_experiment.surface`, Host-owned in-place Dock title localization, retained panel content retranslation, exact four-panel-event ownership, exact service Editor-context binding, and exact combined `PS_EXPERIMENT`/`PS_RUNTIME_SNAPSHOT_HOST` publication lifecycle with partial-failure rollback and retry. Evidence: final E40 `9 passed`; existing related `120 passed`; protected cross-domain `289 passed`; full non-signature `1507 passed, 34 skipped, 34 subtests passed in 164.46s`; compile and four architecture guardrails green; real Editor smoke `plugins=13/20` with zero discovery failures. Signature-only remains blocked by missing `cryptography`.

Six of eight in-scope built-in Dock providers are declarative. This is 75% of Dock-shell migration only; the engine remains unfinished.

## Unique next Gate

Phase E41 -- Qt-Free SimulationControl Dock Contribution and Exact Transport-State/Localization Lifecycle. Read the E41 plan before editing. Keep FrameCore as the only L0 root, VitaLoom as the recursive L1 engine/plugin Host, and `SimulationTransport` as the sole simulation control authority. Do not create a peer engine root or second Host/transport/registry/UI framework.

