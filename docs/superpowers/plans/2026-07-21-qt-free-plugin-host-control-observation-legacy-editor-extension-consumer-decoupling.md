# Phase E26 -- Qt-free Plugin Host Control/Observation Interface and Legacy Editor Extension Consumer Decoupling

- **Date:** 2026-07-21
- **Status:** completed
- **Previous Gate:** E25 established one Qt-free nested Host shutdown authority. Editor close delegates once through the compatibility facade; focused verification was `17 passed`, expanded lifecycle/Loader/Editor was `88 passed, 1 skipped`, cross-domain was `146 passed`, full non-signature was `1283 passed, 25 skipped, 34 subtests passed`, and all four architecture guardrails passed. Signature-only verification remains blocked because the existing virtual environment lacks `cryptography`.
- **Single objective:** deepen the existing exact `NestedPluginHost` authority into one deterministic Qt-free plugin Host control/observation Interface, publish that exact Host through the composed runtime capability registry, and migrate the first legacy Editor consumers away from direct `kernel.plugin_loader` mutable-state access without creating another registry, planner, lifecycle authority, or UI framework rule.

## Immutable recursive framework architecture

`FrameCore` remains the only L0 root framework. `FrameCore/plugins/lotucosm-vitaloom` remains the sole L1 engine/product plugin. That engine plugin is itself a recursive downstream plugin Host/framework whose versioned runtime composes:

- L2 capability/domain packages;
- L3 engine extensions and concrete Host Adapters;
- L4 Project World addons.

The product runtime implementation boundary remains:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`

PyQt6/QPainter/current OpenGL code remains a legacy UI-host Adapter implementation. It is not the engine root, nested plugin authority, manifest authority, lifecycle planner, or future UI-host framework rule.

## Audited production access inventory

| Consumer | Existing access | Classification | E26 decision |
|---|---|---|---|
| `builtin/editor_extensions/plugin_runtime_ops.py` | scope/protection queries, reload, unload, Project sync through `kernel.plugin_loader` | Qt-free observation + validated runtime control + Project World orchestration | migrate to one resolved plugin Host capability |
| `builtin/editor_extensions/plugin_manager_plugin.py` | reads `plugin_registry`, `loaded_plugins`, `failed_plugins` | Qt-free observation facts | migrate to an immutable-by-copy JSON-safe snapshot |
| `builtin/editor_extensions/hot_reload_plugin.py` | reloadable IDs, scope, reload, facade scope constant | observation + validated reload control | migrate to the same Interface; no facade constants |
| `runtime/main.py::_run_editor_smoke()` | discovery/failure/active/catalog compatibility dictionaries | Qt-free diagnostic observation | migrate to the same snapshot |
| `builtin/editor_extensions/package_manager_plugin.py` | active IDs, live plugin object metadata, protection/unload | observation + validated control + legacy metadata compatibility | migrate only if catalog projection stays narrow and JSON-safe; never expose live plugin objects |
| `builtin/editor_extensions/localization_plugin.py` | enumerates live loaded plugin objects to rebuild menu contributions | concrete legacy Editor contribution behavior | do not place in the Qt-free Interface; retain/move behind `LegacyEditorPluginAdapter` seam |
| `core/VitaLoom/project/project_manager.py` | scans and synchronizes Project World addons through facade | Project World command/orchestration | migrate only by delegating the existing `ProjectScopedPluginHost`; no second lifecycle authority |
| `PluginLoader` compatibility aliases | mutable registry dictionaries and facade methods | temporary external compatibility seam | preserve in E26; stop new production consumers from depending on them |

## Target deep Interface

Create a Qt-free Module under `core/VitaLoom/core` that defines and resolves one plugin Host control/observation Interface. The exact composed `NestedPluginHost` is the primary Adapter; an unavailable Adapter fails closed with deterministic reports where consumer startup requires graceful degradation.

The Interface must provide high leverage behind a small surface:

1. deterministic observation snapshot;
2. validated reload/unload controls delegated to existing authorities;
3. Project World scan/sync delegation only if needed by migrated consumers.

Observation facts must include, as required by consumers:

- sorted catalog rows with plugin ID, scope, source, version, dependencies, protection, activation-context facts, active state, reloadable state, and optional JSON-safe metadata projection;
- sorted active/reloadable/failed plugin IDs;
- copied failure facts;
- copied discovery, lifecycle, reload, and shutdown/control diagnostics;
- stable status/count facts.

Every observation call returns fresh containers. It must serialize with `json.dumps(..., allow_nan=False)`, must not return plugin instances, mappings owned by the Host, Qt objects, or mutable registry dictionaries, and must not allow consumer mutation to change Host state.

## Publication and lifetime

- Add one centralized service key for the plugin Host capability.
- Publish the exact existing `NestedPluginHost` into the existing composed runtime capability registry after `EditorContext.services` is available.
- Use the existing capability publication lease/exact-unpublication authority; do not manually create a parallel singleton or registry.
- Unpublish the exact capability during the existing kernel/runtime release sequence.
- Consumer resolution must use the runtime capability registry/Editor context compatibility shapes already established by the L1 registry Interface.

## Control invariants

- Reload delegates to the existing `ManualPluginReloadHost` and preserves protection, scope, dependency, callback, report, command-owner, and legacy contribution semantics.
- Unload delegates to the existing Runtime/Nested authority. Ordinary unload remains fail-closed for protected/core plugins and must not reuse shutdown-only semantics.
- Project scan/sync delegates to the existing `ProjectScopedPluginHost` and existing lifecycle planner.
- No new registry, plugin-manager authority, dependency planner, composition root, manifest parser, activation schema, or callback loop may be introduced.
- Controls return deterministic JSON-safe result facts or preserve existing canonical reports; they do not expose internal plugin objects.

## Red tests before Implementation

1. Snapshot is deterministic and `json.dumps(..., allow_nan=False)` succeeds.
2. Snapshot contains sorted catalog/active/reloadable/failed facts plus scope/protected/active/reloadable facts per plugin.
3. Snapshot contains no live plugin objects or Host-owned mutable mappings.
4. Mutating nested snapshot containers does not mutate the Host or a later snapshot.
5. Reload control delegates to the exact existing manual reload Host.
6. Ordinary unload delegates to the existing unload authority and still rejects protected plugins.
7. Project scan/sync delegates to the exact existing Project-scoped Host when included in the Interface.
8. Capability publication exposes the exact `NestedPluginHost` and exact unpublication removes only that publication.
9. Plugin manager, runtime ops, hot reload, and Editor smoke no longer read `kernel.plugin_loader` mutable compatibility dictionaries.
10. Qt-free Interface Modules import no PyQt6, EditorKernel, LayoutManager, or legacy Editor Adapter.

## Bounded migration slice

Required in E26:

- plugin manager;
- `PluginRuntimeOpsMixin`;
- hot-reload UI;
- Editor smoke/startup diagnostics;
- shared resolver and publication wiring required by those consumers.

Conditional in E26:

- package manager, only if JSON-safe catalog metadata satisfies it without widening the Interface;
- project manager, only if its project lifecycle ordering can be preserved exactly through the same deep Interface.

Explicitly deferred from the Qt-free Interface:

- localization/menu/widget contribution enumeration, because it requires concrete live plugin instances and belongs in the legacy Editor Adapter;
- broad removal of `PluginLoader` compatibility aliases;
- replacement UI shell or renderer work;
- native/OpenGL completion claims unrelated to this Gate.

## Verification ladder

1. Record the genuine red baseline for new/updated E26 tests.
2. Run focused Interface/publication/consumer tests.
3. Run plugin lifecycle, loader, operator, Project World, package-manager, localization, Editor smoke, AI command, Inspector, SR2D, Player/export compatibility tests affected by the seam.
4. Run the full non-signature suite with the established signature exclusions.
5. Run project plugin model, core boundary, GUI boundary, and release consistency guardrails.
6. Record the known signature-only `cryptography` blocker truthfully; do not install dependencies during this phase.

## Documentation closure

Before closing E26:

- append actual implementation and proof to this plan;
- update `docs/mainline_status.md`;
- update `CONTEXT.md` only where the recursive engine-plugin Host language or new deep Interface needs a durable term;
- update `docs/INDEX.md`;
- create one fresh-session prompt naming exactly one next Gate;
- do not claim the persistent project goal `彻底完善` is complete.

## Forbidden directions

- no Unity/Godot/Unreal/Electron migration;
- no second registry, composition root, lifecycle/reload planner, plugin hierarchy, manifest authority, or activation god context;
- no Qt/PyQt/EditorKernel/LayoutManager import in Qt-free Host Modules;
- no live plugin object or mutable registry exposure through observation;
- no weakening of `.pond`, AI command registry, Inspector binding, SR2D seams, package/project manifests, Player/export, Project World L4 lifecycle, or shutdown fail-closed behavior;
- no Git reset, restore, clean, stage, commit, or deletion of unrelated migration work.


## Completion record

- Genuine E26 red baseline: `4 failed, 1 passed` before the Qt-free control/observation Interface existed.
- Deep Module: `core/VitaLoom/core/plugin_host_capabilities.py` now defines one Qt-free `PluginHostControlObservation` Interface, deterministic JSON-safe observation construction, strict capability resolution, and a fail-closed unavailable Adapter. It does not import PyQt6, `EditorKernel`, `LayoutManager`, or `PluginLoader`.
- Exact authority: `NestedPluginHost.observe_plugins()`, `reload_plugin()`, `unload_plugin()`, `scan_project_addons()`, and `sync_plugins_for_project()` continue to compose the existing exact runtime, manual-reload, and Project-scoped Hosts. No second registry, lifecycle planner, reload planner, manifest authority, or composition root was added.
- Publication lifecycle: `EditorKernel` publishes the exact `plugin_loader.nested_plugin_host` under `plugin_host.control_observation` with the existing `CapabilityPublicationLease`. Publication now occurs inside the guarded composition block; initialization failure releases it, normal release removes it, and exact release preserves a newer replacement.
- Consumer migration: Plugin Manager, `PluginRuntimeOpsMixin`, Hot Reload, and Editor smoke now resolve the capability and consume copied observation/control reports instead of reading `kernel.plugin_loader` mutable compatibility dictionaries. Project-persistent enable/disable still uses the canonical AI command registry. Localization live menu/widget contribution enumeration remains deliberately outside the Qt-free Interface at the concrete legacy Editor Adapter seam.
- Behavior proof: final focused Interface/publication/consumer group `43 passed in 1.16s`; expanded plugin lifecycle/Loader/Editor/Adapter group `106 passed in 2.00s`; Project World/package/AI command/Inspector/SR2D/Player/export/startup compatibility group `210 passed in 16.33s`.
- Real legacy Host smoke: `runtime/main.py --smoke-editor` completed with `plugins=13/20`, zero discovery/load failures, and deterministic plugin shutdown.
- Full non-signature proof: `1296 passed, 25 skipped, 34 subtests passed in 129.32s` on 2026-07-21.
- Architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Environment blocker: `tests/test_package_signature_warn_only.py` still fails during collection with `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed, so package-signature verification is not claimed.
- Stable now: the L0 FrameCore / sole L1 recursive engine-plugin topology, one exact nested runtime registry, Qt-free plugin observation/control, existing reload/shutdown/Project World lifecycle authorities, AI command flow, Inspector/SR2D seams, package/project manifests, and Player/export compatibility.
- Still open: `ProjectManager` still reaches `kernel.plugin_loader` for L4 scan/sync; Package Manager and Localization still have concrete live-plugin lookups that must remain or move behind the legacy Editor contribution Adapter rather than widening the Qt-free Interface; PyQt6/QPainter/OpenGL remain legacy/current UI Host Adapters; native acceleration, real current-context OpenGL default-readiness, replacement UI Host evidence, and signature verification remain incomplete.

**Unique next Gate: Phase E27 -- Qt-free Project World Plugin Lifecycle Consumer Decoupling and Legacy ProjectManager Kernel Isolation.** First write the E27 plan and red tests, then migrate `core/VitaLoom/project/project_manager.py` away from direct `kernel.plugin_loader.scan_project_addons(...)` / `sync_plugins_for_project(...)` access to the exact already-published plugin Host capability. Preserve Project World open/close ordering, project manifests, L4 addon discovery/activation reports, failure rollback, and the single existing `ProjectScopedPluginHost` authority; do not create another project manager, registry, lifecycle planner, or UI framework rule.
