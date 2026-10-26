# Phase E39 Fresh-Session Prompt -- Qt-Free PackageManager Dock Contribution and In-Place Localization/Exact Service Lifecycle

Date: 2026-07-26
Status: completed; historical closure and E40 handoff

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E38 plan, and the E39 plan before editing code.

## Architecture that must remain true

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` contains L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain the only Host authorities. `PluginLoader` remains a compatibility facade. PyQt and `LegacyEditorPluginAdapter` remain current/legacy Host Adapter details, not the engine root.

Do not create a second Host, registry, catalog, package authority, service registry, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell.

## E38 closure truth

E38 is complete: one Qt-free `console.surface`, Host-owned in-place Dock title refresh, retained Console content retranslation, exact event/capability/logging lifecycle, `1489 passed, 34 skipped, 34 subtests passed`, green compile/guardrails, and real Editor smoke `plugins=13/20`. Signature-only remains blocked by missing `cryptography`.

Four of eight in-scope built-in Dock providers are declarative. This is 50% of Dock-shell migration only.

## Unique E39 Gate

1. Write red tests for one `package_manager.surface`, authoritative Host projection, in-place Dock/content localization, and preserved layout/filter/selection/floating identity.
2. Prove exact four-event, two-kernel-signal, and combined `PACKAGE_CATALOG`/`PACKAGE_OPERATIONS` publication ownership across partial load failure, rollback failure, replacement, retry, reload, unload, and shutdown.
3. Make only the minimum PackageManager changes required by those tests. Preserve Package domain, Project World, manifest alignment, package transactions/recovery/interlock, runtime controls, menu/show/open-mode/floating geometry, fallback dialog, and legacy/community Host behavior.
4. Do not rewrite the 2,000+ line plugin, do not migrate another Dock, and do not begin viewport/theme/replacement-Host work in this Gate.
5. Close with focused, protected, complete non-signature, compile, four guardrails, real offscreen Editor smoke, and explicit signature-blocker evidence.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work.


## E39 closure evidence

E39 is complete for its bounded slice: one `package_manager.surface`, Host-owned in-place Dock title localization, retained content retranslation, and exact four-event/two-signal/combined-publication lifecycle with partial-failure rollback and retry. Evidence: final E39 `9 passed`; focused `68 passed`; expanded `247 passed, 2 skipped, 17 subtests passed`; full non-signature `1498 passed, 34 skipped, 34 subtests passed in 178.89s`; compile and four architecture guardrails green; real Editor smoke `plugins=13/20` with zero discovery failures. Signature-only remains blocked by missing `cryptography`.

Five of eight in-scope built-in Dock providers are declarative. This is 62.5% of Dock-shell migration only; the engine remains unfinished.

## Unique next Gate

Phase E40 -- Qt-Free PsExperiment Dock Contribution and Exact Service/Panel Event Lifecycle. Read the E40 plan before editing. Keep FrameCore as the only L0 root and VitaLoom as the recursive L1 engine/plugin Host. Do not create a peer engine root or second Host/registry/UI framework.
