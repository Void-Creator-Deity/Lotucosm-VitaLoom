# Phase E24 -- Legacy Editor Plugin Contribution Adapter Extraction and PluginLoader Compatibility Facade

- **Date:** 2026-07-21
- **Status:** completed
- **Previous Gate:** E23 completed the Qt-free `NestedPluginHost` composition root over exactly one E20 runtime registry, with E21 Project-scoped and E22 manual-reload Hosts composed over that same object. Final E23 proof was `1258 passed, 25 skipped, 34 subtests passed in 120.27s` plus all four architecture guardrails.
- **Single objective:** extract concrete legacy Editor plugin contribution lifecycle behavior from `PluginLoader` into one explicit Adapter satisfying the existing Qt-free `RuntimePluginHostAdapter` seam, while retaining `PluginLoader` as a narrow compatibility facade over `NestedPluginHost` and the Adapter.

## Immutable architecture

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       sole engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon
```

The new Adapter remains inside the existing L1 version runtime and is concrete legacy Editor infrastructure. It is not a FrameCore plugin, second engine root, generic UI framework, nested plugin authority, or replacement shell.

## Audited PluginLoader responsibilities

| Current responsibility | E24 classification | Target |
|---|---|---|
| construct `NestedPluginHost` and publish compatibility state aliases | compatibility facade | remain in `PluginLoader` |
| discovery/bootstrap/Project World/reload/operator public methods | compatibility delegates | remain as narrow delegates |
| candidate importer lambda and `_instantiate_plugin_from_file()` | tested patch seam | remain as Loader compatibility delegate |
| activation-context projection/cache | concrete legacy Editor Adapter | move implementation; retain Loader delegate and observation compatibility |
| `RuntimePluginHostAdapter` lifecycle callbacks | concrete legacy Editor Adapter | move implementation |
| Dock/Viewport/Menu/Toolbar/Theme contribution registration | concrete legacy Editor Adapter | move implementation |
| command ownership registration/unpublication | concrete legacy Editor Adapter | move implementation |
| `IEditorPlugin.on_editor_ready()` and kernel signals | concrete legacy Editor Adapter | move implementation |
| UI contribution cleanup | concrete legacy Editor Adapter | move implementation |
| post-transition layout settling | concrete legacy Editor Adapter | move implementation |
| eager-mode and repo-root resolvers | composition environment compatibility | remain narrow Loader resolvers in E24 |

## Target Module

Create a single deep Module, expected at:

```text
core/VitaLoom/kernel/legacy_editor_plugin_adapter.py
```

Primary Interface:

```python
LegacyEditorPluginAdapter(kernel)
  .activation_context_for(plugin_info)
  .after_lifecycle_transition(report)
  .after_plugin_load(plugin, plugin_id, plugin_info)
  .before_plugin_unload(plugin, plugin_id, plugin_info)
  .after_plugin_unload_callback(plugin, plugin_id, plugin_info)
  .after_plugin_deactivated(plugin, plugin_id, plugin_info)
```

Registration/cleanup helpers stay private implementation details unless preserving a tested Loader method requires a compatibility delegate.

## Required invariants

- `NestedPluginHost.runtime_plugin_host.adapter` is the exact `LegacyEditorPluginAdapter` object, never `PluginLoader`.
- The Qt-free E20-E23 Modules must not import this concrete Adapter, PyQt, EditorKernel, LayoutManager, theme manager, or legacy plugin Interfaces.
- Load ordering remains: runtime `plugin.on_load()`, then contribution publication/commands/editor-ready/signal.
- Unload ordering remains: contribution cleanup, runtime `plugin.on_unload()`, command unpublication, registry removal, kernel unload signal.
- Contribution or editor-ready failures remain isolated and logged as before; no false runtime lifecycle success/failure semantics are introduced.
- Command specs remain exact-owner normalized and unregister by plugin owner.
- Layout settling runs only after an actual lifecycle transition, as ensured by `NestedPluginHost`.
- Loader compatibility state aliases, report properties, public delegates, private patch seam, and externally exercised activation-context behavior remain intact.
- `.pond`, activation schema, Project World L4 timing, AI command/Inspector binding, SR2D, package/project manifests, Player/export, operator recovery, and strict JSON reports remain unchanged.

## Red tests

1. Guarded import proves the Adapter is concrete-host-only while E20-E23 Modules remain free of it and Qt/legacy Interfaces.
2. Standalone Adapter projects runtime vs exact legacy UI activation contexts and caches the runtime projection.
3. Standalone Adapter publishes Dock/Viewport/Menu/Toolbar/Theme/commands, calls editor-ready, and emits the load signal in established order.
4. Standalone Adapter removes UI before unload, unregisters commands only after the unload callback, then emits the unload signal after deactivation.
5. Failure isolation and missing layout-manager behavior remain deterministic.
6. Layout settling delegates only when the legacy manager exposes the supported method.
7. Loader constructs one Adapter, passes its exact object to `NestedPluginHost`, and preserves compatibility delegates/properties without implementing contribution logic itself.

## Implementation sequence

1. Add standalone Adapter behavior and architecture red tests; run them to prove absence/wrong wiring.
2. Implement `legacy_editor_plugin_adapter.py` by moving concrete behavior without changing lifecycle semantics.
3. Rewire Loader construction and replace old implementations with narrow compatibility delegates/properties.
4. Update static architecture gates to prevent Loader from regaining concrete contribution implementation and prevent Qt-free Hosts from importing the Adapter.
5. Run focused Adapter/Loader/runtime/nested/project/reload/activation tests.
6. Run expanded plugin/command/Inspector/Player/export/layout/FrameCore regressions.
7. Run the complete non-signature suite and all four architecture guardrails; verify the known signature blocker separately.
8. Close plan/status/context/index and name exactly one next Gate.

## Non-goals

- No Unity, Godot, Unreal, Electron, or replacement UI shell.
- No generic UI contribution framework invented from the legacy PyQt API.
- No renderer, SR2D, native acceleration, or OpenGL migration in E24.
- No new registry, plugin layer, manifest authority, activation schema, lifecycle planner, or reload planner.
- No removal of compatibility seams without evidence.
- No dependency installation for `cryptography`.
- No Git reset, restore, clean, stage, commit, or unrelated-work deletion.

## Completion record

- Red baselines: the initial standalone Adapter/composition tests produced `7 failed`, proving that concrete Editor contribution behavior was still embedded in `PluginLoader`; a later canonical command-owner test independently produced `1 failed`, proving that metadata raw names could register commands under an owner different from the canonical runtime plugin ID.
- Implementation: added `core/VitaLoom/kernel/legacy_editor_plugin_adapter.py` as the single concrete legacy Editor Adapter at the existing Qt-free `RuntimePluginHostAdapter` seam. It now owns activation-context projection, Dock/Viewport/Menu/Toolbar/Theme and command contribution handling, `on_editor_ready()`, kernel signals, UI cleanup, and layout settling. `PluginLoader` constructs `NestedPluginHost` with that exact Adapter and retains only compatibility aliases, delegates, environment resolvers, and the patchable candidate-import seam.
- Command ownership correction: contribution registration now uses the canonical plugin ID supplied by `RuntimePluginHost`, so registration and `unregister_owner(...)` use the same owner even when metadata `name` differs from the class-derived canonical ID.
- Source recovery: `layout_manager.py` was restored after an accidental PowerShell transcoding incident by combining the clean distribution source with the current viewport-capability cleanup behavior and comparing every method against the preserved CPython 3.11 bytecode while ignoring docstrings. The restored source SHA-256 is `df800fca81aacd0b86b823b935d9a0b9c25d5aa93c26ee92835e2517178a7fe2`; behavioral comparison reported `same_code_keys True` and `behavior_differences_ignoring_docstrings []`.
- Focused proof: `84 passed in 2.42s` across the Adapter, nested/runtime/Project/reload Hosts, activation, Loader lifecycle/failure/operator/reload, plugin-ID, layout, and viewport paths.
- Expanded cross-domain proof: `383 passed, 1 skipped in 30.24s` across plugin, command, Inspector, Player, startup, export, layout, FrameCore, Editor, Project-scoped, runtime-host, and activation-context tests.
- Final full non-signature proof: `1266 passed, 25 skipped, 34 subtests passed in 127.34s` on 2026-07-21.
- Final architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Environment blocker: `tests/test_package_signature_warn_only.py` still fails during collection with `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed, so package-signature verification is not claimed.
- Stable now: the E20-E24 Qt-free downstream plugin Host Modules and concrete legacy Editor Adapter preserve one L1 version-runtime composition, one runtime registry, command/Inspector/SR2D/Player/export/Project World compatibility, and deterministic lifecycle ordering.
- Still open: `EditorKernel.closeEvent()` directly enumerates `loaded_plugins`; PyQt6/QPainter/OpenGL remain the current legacy UI-host Adapter; native acceleration, real current-context OpenGL parity/interaction/benchmark proof, and the signature environment remain incomplete. No replacement UI Host or whole-engine completion is claimed.

**Unique next Gate: Phase E25 -- Qt-free Nested Plugin Host Shutdown Authority and Legacy Editor Close Adapter.** Add one explicit shutdown Interface over the existing `NestedPluginHost`/`RuntimePluginHost` authority, reuse the lifecycle planner for deterministic reverse-dependency teardown, keep ordinary protected-plugin unload/reload restrictions intact while allowing process shutdown to clean every active plugin, and make `EditorKernel.closeEvent()` consume the compatibility facade instead of enumerating the runtime registry.
