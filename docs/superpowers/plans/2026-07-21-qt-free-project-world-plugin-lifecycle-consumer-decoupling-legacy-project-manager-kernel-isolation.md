# Phase E27 — Qt-free Project World Plugin Lifecycle Consumer Decoupling and Legacy ProjectManager Kernel Isolation

- **Date:** 2026-07-21
- **Status:** completed
- **Previous Gate:** E26 published the exact composed `NestedPluginHost` as one Qt-free `PluginHostControlObservation` capability and migrated the first Editor consumers. Evidence: focused `43 passed`, expanded plugin/Loader/Editor `106 passed`, cross-domain `210 passed`, real offscreen Editor smoke `plugins=13/20`, full non-signature `1296 passed, 25 skipped, 34 subtests passed`, and all four architecture guardrails passed. Signature-only collection remains blocked because `.venv` lacks `cryptography`.
- **Single objective:** remove `ProjectManager`'s direct dependency on the legacy `kernel.plugin_loader` facade for L4 Project World addon discovery/synchronization, resolving the already-published exact recursive plugin Host capability instead, without changing the sole lifecycle authority or Project World truth.

## Immutable recursive framework architecture

```text
L0 FrameCore (the only root framework)
└─ L1 lotucosm-vitaloom (the sole engine/product mega-plugin)
   ├─ hub/ (version and Project World portal, outside a version runtime)
   └─ versions/1.0.0/runtime/ (product runtime boundary)
      ├─ L2 capability/domain packages
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

`lotucosm-vitaloom` is not merely an ordinary leaf plugin: it is the engine and a recursive downstream plugin Host/derived framework. The exact `NestedPluginHost` composes the existing `RuntimePluginHost`, `ManualPluginReloadHost`, `ProjectScopedPluginHost`, and shutdown/control Interfaces. PyQt6/QPainter/current OpenGL remain legacy/current UI Host Adapter implementations, never the engine root, plugin contract authority, manifest authority, lifecycle planner, or future framework rule source.

## Audited direct dependency inventory

| Path | Current access | Existing semantics that must survive |
|---|---|---|
| `ProjectManager._sync_project_plugins()` | `editor_context.kernel.plugin_loader.scan_project_addons(project_path)` then `sync_plugins_for_project(project_data, repo_root=...)` | scan-before-sync; non-ready discovery blocks sync; report gains `discovery` and `source=project_open`; adapter exceptions become deterministic failed reports |
| `ProjectManager.close_project()` | after successful flush, `kernel.plugin_loader.scan_project_addons(None)` then `sync_plugins_for_project({})` | flush-before-addon teardown; scan-before-sync; unsettled/exception teardown preserves current Project World and suppresses close publication; settled teardown precedes host scene/context clearing |
| Existing transition tests | construct `context.kernel.plugin_loader` fakes | migrate proof setup to `context.services` capability publication; do not retain a Loader fallback solely for tests |

## Target deep Module and seam

Reuse, do not widen, the E26 Module:

- `core/VitaLoom/core/plugin_host_capabilities.py`
- `resolve_plugin_host(editor_context)`
- `PluginHostControlObservation.scan_project_addons(...)`
- `PluginHostControlObservation.sync_plugins_for_project(...)`

The capability is an Interface at the recursive engine-plugin Host seam. The exact `NestedPluginHost` remains its primary Adapter. `ProjectScopedPluginHost` remains the only L4 discovery/lifecycle authority. `ProjectManager` remains Project World orchestration and report assembly, not a second Host, registry, planner, manifest parser, or composition root.

## Open/close ordering and failure policy

### Open

1. Apply validated Project World and load active `.pond` scene using existing behavior.
2. Publish existing Project World open events in the current order.
3. Resolve the plugin Host capability from the composed runtime registry.
4. Scan L4 addons for the canonical project path.
5. Only when discovery status is `ready`, synchronize against project manifest data and the existing repo-root resolution.
6. Attach copied `discovery` and `source=project_open` facts to the lifecycle report.
7. Unsettled lifecycle remains a truthful open warning/event; E27 does not invent rollback that did not previously exist.

### Close

1. Verify prepared/current Project World identity.
2. Flush before any plugin lifecycle action.
3. Resolve the plugin Host capability.
4. Scan with `None`, then synchronize with `{}` in the existing order.
5. Any unavailable, exception, or unsettled result is fail-closed: return a partial close report, preserve current Project World/scene/context, and do not emit `project_closed`.
6. Only a settled/eager-skip lifecycle may proceed to clear scene, selection, project facts, and publish close.

The old `skipped_host_unavailable` branch is not safe enough because it clears Project World state without evidence that active L4 addons were deactivated. E27 replaces it with explicit capability reports and existing unsettled-close policy.

## Genuine red tests

Before production changes, add tests proving:

1. `ProjectManager` can open/synchronize without `editor_context.kernel` or `kernel.plugin_loader` when the exact capability is published in `editor_context.services`.
2. Open calls scan before sync, forwards unchanged project data and repo root, and attaches discovery/source facts.
3. A non-ready discovery report prevents sync and produces a blocked Project World plugin lifecycle report.
4. Close flushes before scan/sync; then calls scan `None` before sync `{}`; successful teardown clears/publishes exactly as before.
5. Missing capability is explicit and fail-closed during close, preserving the current Project World and suppressing false close publication.
6. Unsettled/exception lifecycle reports preserve existing partial-close truth.
7. Source-level guard: production `project_manager.py` no longer contains `kernel.plugin_loader`, does not import `PluginLoader`, and does not construct/import `NestedPluginHost`, `ProjectScopedPluginHost`, or another registry/planner.

Record the real failing baseline before implementation.

## Verification ladder

1. E27 red tests.
2. Focused capability + ProjectManager open/close/session + ProjectScopedPluginHost tests.
3. Expanded plugin lifecycle/Loader compatibility/Project World recovery/package/project manifest/AI command/Inspector/SR2D/Player/export/startup tests.
4. Real offscreen `runtime/main.py --smoke-editor`.
5. Full suite excluding only `tests/test_package_signature_warn_only.py`.
6. Four guardrails:
   - `tools/check_project_plugin_model.py`
   - `tools/check_core_boundaries.py`
   - `tools/check_gui_boundaries.py`
   - `tools/check_release_consistency.py`
7. Reconfirm the signature-only blocker without installing dependencies or claiming a pass.

## Non-goals

- no Unity/Godot/Unreal/Electron migration;
- no second root framework, registry, plugin Host, lifecycle planner, manifest authority, project manager, or god context;
- no broad `PluginLoader` compatibility facade removal;
- no Package Manager live-object migration;
- no Localization/menu/widget contribution widening into the Qt-free Interface;
- no replacement UI Host decision;
- no native acceleration or OpenGL default-ready claim;
- no modification of `.pond`, AI command registry, Inspector, SR2D, package/project manifests, Player/export semantics;
- no reset/restore/clean/stage/commit/delete of unrelated uncommitted migration work.

## Closure rule

At completion, append actual red/green/full/smoke/guardrail evidence here; update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`; create one fresh-session prompt naming exactly one next Gate. The persistent objective “彻底完善” remains active unless every remaining requirement is proven complete.

## Completion record

- Genuine E27 red baseline: the new capability-isolation group failed `4 failed` because `ProjectManager` still reached `kernel.plugin_loader`, ignored the published capability, allowed close to clear a Project World when the Host was unavailable, and violated the source guard.
- Consumer migration: `ProjectManager._sync_project_plugins()` and `close_project()` now resolve `resolve_plugin_host(editor_context)` and call the exact capability. Production `project_manager.py` no longer contains `kernel.plugin_loader` and does not import or construct `PluginLoader`, `NestedPluginHost`, `ProjectScopedPluginHost`, or another registry/planner.
- Open truth preserved: L4 scan still precedes sync; non-`ready` discovery prevents sync; repo-root selection is forwarded unchanged; lifecycle reports retain copied `discovery` and `source=project_open`; exceptions remain deterministic `plugin_lifecycle_adapter_exception` failures.
- Close truth strengthened: flush still precedes addon teardown; scan `None` still precedes sync `{}`; unavailable capability now returns the existing partial/unsettled close path instead of the unsafe legacy `skipped_host_unavailable` clear. Unavailable, exception, and unsettled teardown preserve the current Project World and suppress false `project_closed` publication.
- Existing authority preserved: the exact `NestedPluginHost` remains the published Adapter and `ProjectScopedPluginHost` remains the only L4 discovery/lifecycle authority. `PluginLoader` scan/sync delegates remain intact only as compatibility seams.
- Test migration: legacy Project World transition fixtures now publish a complete test Adapter under `PLUGIN_HOST_CONTROL_OBSERVATION`; no Loader fallback was added. Architecture guards now assert capability routing and the absence of direct Loader access.
- Focused proof: the main E27 capability/Project World/ProjectScopedPluginHost group passed `70 passed in 1.31s`; the final exception/source/architecture regression group passed `38 passed in 0.81s`.
- Cross-domain proof: plugin, Project World, package, AI command, Inspector, SR2D, Player/export, startup, and Editor compatibility group passed `391 passed, 2 skipped, 17 subtests passed in 28.91s`.
- Real legacy Host smoke: offscreen `runtime/main.py --smoke-editor` completed `plugins=13/20`, zero discovery/load failures, and deterministic reverse shutdown.
- Full non-signature proof: after updating one stale architecture assertion, the final suite passed `1302 passed, 25 skipped, 34 subtests passed in 127.29s` on 2026-07-21.
- Architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Environment blocker: the expanded selection that included `tests/test_package_signature_warn_only.py` failed collection only with `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed, so package-signature verification is not claimed.
- Stable now: recursive L0/L1/L2/L3/L4 topology, one exact nested plugin Host, Project World capability orchestration, fail-closed open/close lifecycle truth, `.pond`, AI command/Inspector/SR2D, manifests, Player/export, reload, shutdown, and current legacy Editor smoke.
- Still open: Package Manager still reads live Loader/plugin objects for active/detail/protection/unload facts; Localization still enumerates live menu providers; the broader `PluginLoader` compatibility facade remains; replacement UI Host parity, native acceleration, real current-context OpenGL default-readiness, and signature verification remain incomplete. The persistent objective 彻底完善 is not complete.

**Unique next Gate: Phase E28 ? Qt-free Plugin Catalog Metadata Projection and Legacy PackageManager Consumer Decoupling.** Deepen only the existing deterministic copied observation enough for Package Manager display metadata, then migrate active/detail/protected/unload behavior to `resolve_plugin_host(...)`, `observe_plugins()`, validated `unload_plugin()`, and the canonical AI command registry. Do not expose live plugins or absorb Localization/menu contribution behavior into the Qt-free Interface.

