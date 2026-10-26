# Phase E52 -- Qt-Free Runtime Command Provider Contract and Host-Owned Command Lifecycle

Date: 2026-07-26
Status: completed on 2026-07-27

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. Reuse the existing `RuntimePluginHost`, canonical command Registry, `CommandSpec`, copied plugin metadata, and current `LegacyEditorPluginAdapter`. Do not create a second Host, command Registry, command catalog, composition root, UI framework, app shell, or peer engine root.

## Previous Gate

E51 retired the obsolete live menu/toolbar provider Interface and deepened refresh to consume only RuntimePluginHost-copied editor facts in exact Host order. Fresh non-signature evidence is `1625 passed, 34 skipped, 34 subtests passed in 190.67s`; compile, all four guardrails, and standard/eager Editor smokes pass. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- `ICommandProvider` describes commands shared by UI, CLI, MCP, and agents, but it still lives in legacy `kernel/plugin_interfaces.py` rather than the Qt-free runtime plugin contract.
- Five built-in providers (`EditorWorkflowPlugin`, `HotReloadPlugin`, `LocalizationPlugin`, `PackageManagerPlugin`, and `StandardUIPlugin`) import that legacy Interface.
- Exact command registration, owner canonicalization, and owner release still execute inside `LegacyEditorPluginAdapter`; `PluginLoader` retains compatibility delegates for them.
- A direct/headless `RuntimePluginHost` using `NullRuntimePluginHostAdapter` does not register plugin commands even though `CommandSpec` and the canonical Registry are Qt-free.
- `RuntimePluginHost` already names the post-unload release failure stage `command_owner_release`; this is evidence that command ownership belongs to the plugin Host lifecycle, not to a concrete UI Host Adapter.
- Dock, viewport, and theme providers still carry concrete current-Host widget/QSS payloads. They are outside E52.

## Tasks

### Task 1 -- Executable red Host authority contract

1. Prove a command provider loaded by direct `RuntimePluginHost` with `NullRuntimePluginHostAdapter` publishes commands without importing or constructing the legacy Editor Adapter.
2. Prove canonical owner injection, duplicate/partial registration rollback, activation failure reporting, unload, reload, and shutdown command release are deterministic.
3. Prove Adapter failure after command publication rolls command ownership back with no half-active plugin or stale command.
4. Prove current menu/toolbar actions, CLI, MCP, project-scoped/nested Host behavior, and stale-action failure still use the same canonical Registry and command IDs.

### Task 2 -- Establish the Qt-free command-provider Interface

1. Move or define `ICommandProvider` in the Qt-free runtime plugin contract with the smallest Interface required to return `CommandSpec` values.
2. Keep only a bounded compatibility import/alias in `kernel/plugin_interfaces.py` when existing external imports require it; migrate all built-in providers to the Qt-free Interface.
3. Do not place Qt, editor context, menu/toolbar facts, live widgets, dialogs, or Project World objects in the command contract.
4. Preserve existing command metadata, handlers, error shapes, mutation/undo flags, GUI requirements, capabilities, and command IDs.

### Task 3 -- Move exact ownership into RuntimePluginHost

1. Make the existing RuntimePluginHost lifecycle own command registration after `plugin.on_load()` and before concrete Adapter projection, so projected actions always target already-published commands.
2. Reuse the one canonical command Registry; do not introduce per-Host shadow registries or a second command catalog.
3. Canonicalize every `CommandSpec.owner` to the Host plugin id, validate the complete batch, and roll back the exact batch on any registration or later activation failure.
4. Release exact command ownership after `plugin.on_unload()` while preserving ordinary unload, strict shutdown, retry, reload, and failure-report ordering.
5. Remove command registration/release responsibility and resulting compatibility delegates from `LegacyEditorPluginAdapter` and `PluginLoader` only after executable parity is green.

### Task 4 -- Verification and closure

1. Run focused RuntimePluginHost/command-provider red-green tests plus current plugin command, menu/toolbar, localization, reload, shutdown, CLI, MCP, Inspector, Project World, and package protections.
2. Run the complete non-signature suite, modified-Module `compileall`, all four architecture guardrails, and standard/eager real Editor smoke.
3. Run signature-only collection and record the exact environment blocker without installing dependencies silently.
4. Update this plan, its prompt, `docs/mainline_status.md`, `CONTEXT.md`, `docs/plugin_command_contract.md`, and `docs/INDEX.md`; then name exactly one next Gate only after a fresh post-E52 audit.

## Completion boundary

E52 may move only the command-provider Interface and exact command ownership lifecycle from the current PyQt Host Adapter into the existing Qt-free RuntimePluginHost. It does not redesign the command Registry or command schemas; migrate concrete Dock/viewport/theme content; remove `LegacyEditorPluginAdapter`; select/build a replacement UI Host; change `.pond`, Project World, scene, package, Player/export, SR2D, native/OpenGL, or signature authorities; or complete the editor/engine.


## Completion evidence (2026-07-27)

- `ICommandProvider` now lives in the Qt-free `core/VitaLoom/core/runtime_plugin_contract.py`; `kernel/plugin_interfaces.py` retains only the bounded compatibility import. All five built-in command providers import the runtime contract directly.
- `RuntimePluginHost` now validates and canonicalizes the complete command batch, publishes commands after `plugin.on_load()` and before Adapter projection, retains exact `(command_id, CommandSpec)` release facts, and releases them after `plugin.on_unload()`.
- Registration failure and later Adapter-projection failure roll back plugin resources, concrete UI projection, and exact command ownership in reverse lifecycle order. A plugin whose activation fails is not left half-active outside `loaded_plugins`.
- `LegacyEditorPluginAdapter` and `PluginLoader` no longer register or release plugin commands. The Adapter still invokes the one canonical Registry for projected actions, which preserves UI/CLI/MCP/Agent command identity.
- Focused contribution/lifecycle protection: `68 passed`. Expanded command/Adapter/Inspector/package protection: `238 passed, 8 subtests passed`.
- The first complete non-signature run reported `1627 passed, 34 skipped, 34 subtests passed, 4 failed in 178.94s`: one known load-sensitive Asset Index cold-build threshold and three stale architecture/tool assertions that still required the removed Adapter callbacks. The assertions were migrated to require Host-owned command authority; the Asset Index case passed in isolation (`1 passed in 8.10s`).
- Fresh second complete non-signature run: `1631 passed, 34 skipped, 34 subtests passed in 158.98s`.
- Repository `compileall`, project plugin model, core boundaries, GUI boundaries, and release consistency all pass. Standard/eager offscreen Editor smokes pass at `plugins=13/20` and `plugins=20/20`, with zero discovery/load failures and deterministic reverse shutdown.
- Signature-only collection remains environmentally blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.52s`, exit code `1`). No dependency was installed and signature verification is not claimed.

## Post-E52 audit and unique next Gate

All eight built-in Dock plugins already publish immutable `dock_surface` contribution facts, but activation and fallback cleanup still treat the PyQt-era `IDockProvider` type in `kernel/plugin_interfaces.py` as runtime extension authority. The current Adapter already resolves the concrete `create_dock_widget` factory from the active plugin while the Host-copied contribution owns Dock identity/configuration. The three viewport providers and one theme provider remain separate seams and are intentionally not bundled into the next phase.

**Unique next Gate: Phase E53 -- Declarative Dock Surface Activation and Obsolete Legacy Dock Provider Runtime Authority Retirement.** Make the eight existing Host-copied `dock_surface` facts the sole activation/cleanup authority for built-in Docks, keep each concrete PyQt Dock factory as an Adapter-only implementation detail, remove built-in/runtime dependence on `IDockProvider`, and preserve exact Dock identity, localization, tabify/layout, unload/reload/shutdown, community compatibility, and real Editor parity. Do not migrate viewport/theme providers, create a replacement Host, or introduce a generic widget framework.
