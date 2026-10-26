# Phase E38 Fresh-Session Prompt -- Qt-Free Console Dock Contribution and Exact Logging/Capability Adapter Lifecycle

Date: 2026-07-26
Status: completed; historical closure and E39 handoff

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E37 plan, this completed E38 plan, and the E39 plan before editing code.

## Non-negotiable architecture

`FrameCore` is the sole L0 root framework. `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and itself the recursive downstream Plugin Host / derived framework. `versions/1.0.0/runtime` is the versioned product runtime boundary containing L2 capability/domain Modules, L3 engine extensions / Host Adapters, and L4 Project World addons. `NestedPluginHost`, `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` remain Host authorities. `PluginLoader` remains a compatibility facade. PyQt6/QPainter/Qt OpenGL and `LegacyEditorPluginAdapter` are current/legacy Host Adapter details, not the engine root or future extension authority.

Do not create a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, logging framework, capability registry, widget DSL, renderer framework, peer L1 engine plugin, or replacement shell.

## E38 closure truth

E38 completed the bounded Console shell/lifecycle slice. `ConsolePlugin` declares one Qt-free `console.surface`; `LegacyEditorPluginAdapter` owns shell projection and in-place title refresh; `ConsolePanel.retranslate_ui()` refreshes retained content; exact event, `UI_CONSOLE_PANEL`, and logging-handler resources are acquired/released transactionally with rollback, retry, repeated-construction idempotency, and replacement-owner preservation.

Fresh evidence: initial red `10 failed`; final E38 file `13 passed`; joint capability lifecycle `21 passed`; focused `44 passed`; expanded `130 passed, 1 skipped`; full non-signature `1489 passed, 34 skipped, 34 subtests passed in 172.43s`; modified-Module `compileall`; four green architecture guardrails; real offscreen Editor smoke `plugins=13/20` with zero discovery errors. Signature-only remains blocked because the exact repository `.venv` lacks `cryptography`; no dependency was installed.

This means four of eight in-scope built-in Dock providers are declarative: Inspector, Hierarchy, ProjectBrowser, and Console. This is 50% of the Dock-shell migration only, not 50% of the engine.

## Unique next Gate

Phase E39 -- Qt-Free PackageManager Dock Contribution and In-Place Localization/Exact Service Lifecycle.

1. Audit and preserve PackageManager's existing Package domain, Project World commands/events, floating/open-mode behavior, menu surface, package catalog/operations publications, plugin runtime semantics, and legacy/community fallback.
2. Write red tests before implementation for one Qt-free `package_manager.surface`, Host-owned in-place Dock localization, retained content/layout identity, exact four-event ownership, and exact service publication/release across partial failure, replacement, reload, unload, and shutdown.
3. Remove only PackageManager's Dock reconstruction on `language_changed`; do not rewrite the full plugin or create another Host, service registry, package catalog, Dock/UI framework, or composition root.
4. Close E39 with focused, protected, complete non-signature, compile, guardrail, smoke, and signature-blocker evidence.

Use `.\.venv\python.exe`. Do not install dependencies, stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work. The persistent whole-engine objective remains active.
