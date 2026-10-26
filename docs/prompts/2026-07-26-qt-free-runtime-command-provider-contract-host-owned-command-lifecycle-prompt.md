# Phase E52 Completion / Fresh-Session Handoff -- Qt-Free Runtime Command Provider Contract and Host-Owned Command Lifecycle

Date: 2026-07-27
Status: completed; do not reimplement E52

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, `docs/plugin_command_contract.md`, and the completed E52 plan before continuing.

Preserve the sole recursive architecture: `FrameCore` is L0; `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and downstream Plugin Host/derived framework; `versions/1.0.0/runtime` is the product boundary. PyQt/QPainter/OpenGL remain current/legacy UI Host Adapter details.

E52 is closed. `ICommandProvider` is Qt-free, the existing `RuntimePluginHost` owns complete-batch validation, canonical owner injection, publish/rollback/exact release, and command registration occurs after `on_load()` but before concrete Adapter projection. `LegacyEditorPluginAdapter` and `PluginLoader` no longer own command registration or release. The one canonical Registry still serves projected UI actions, CLI, MCP, and agents.

Fresh evidence: focused `68 passed`; expanded `238 passed, 8 subtests passed`; complete non-signature `1631 passed, 34 skipped, 34 subtests passed in 158.98s`; repository compileall; all four architecture guardrails; standard/eager offscreen Editor smokes at `13/20` and `20/20`. Signature-only remains blocked because `.venv` lacks `cryptography` (`1 error in 0.52s`); do not install it silently.

The first full run had only one known load-sensitive Asset Index threshold miss plus three stale guard assertions. The threshold passed in isolation (`1 passed in 8.10s`), the guards now require Host-owned command authority, and the second full run is green.

The unique next Gate is E53, documented in `docs/superpowers/plans/2026-07-27-declarative-dock-surface-activation-obsolete-legacy-dock-provider-runtime-authority-retirement.md` and its matching prompt. Do not reopen command ownership, migrate viewport/theme providers, change `.pond`/Project World/SR2D/renderer/signature authorities, or create another Host/Registry/UI framework.
