# Fresh-session prompt — Phase E28 Qt-free Plugin Catalog Metadata Projection and Legacy PackageManager Consumer Decoupling

Continue the persistent VitaLoom objective **“彻底完善”** from the completed E27 checkpoint. Do not treat E27 completion as whole-engine completion.

## Immutable architecture authority

```text
L0 FrameCore (the only root framework)
└─ L1 lotucosm-vitaloom (the sole engine/product mega-plugin)
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain packages
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

`lotucosm-vitaloom` is itself a recursive downstream plugin Host/derived framework. The exact `NestedPluginHost` remains the sole composition authority over runtime, manual reload, Project-scoped lifecycle, shutdown, and control/observation. PyQt6/QPainter/current OpenGL remain legacy/current UI Host Adapters, not the engine root, extension authority, manifest authority, lifecycle planner, or future framework rule source.

## Previous gate evidence

E27 migrated `core/VitaLoom/project/project_manager.py` away from direct `kernel.plugin_loader` scan/sync calls to `resolve_plugin_host(editor_context)` and the exact already-published capability. Open still scans before sync and blocks sync on non-ready discovery. Close still flushes first, scans `None`, syncs `{}`, and preserves the current Project World on unavailable, exception, or unsettled teardown rather than falsely clearing/publishing close.

Read the completed E27 plan and its recorded verification before starting. Signature-only collection remains blocked because `.venv` lacks `cryptography`; do not install it unless the user explicitly changes direction.

## E28 single objective

Deepen the existing copied plugin observation catalog just enough to serve Package Manager status/detail/control needs, then migrate `builtin/editor_extensions/package_manager_plugin.py` away from all live `kernel.plugin_loader` lookups and control calls.

Known Package Manager legacy accesses at E27 closure:

- active IDs from `plugin_loader.loaded_plugins`;
- selected plugin detail from a live plugin object's `get_plugin_info()`;
- protected checks through the Loader facade;
- immediate session unload through the Loader facade.

The E26 capability already provides active IDs, catalog scope/protection/version facts, and validated unload. If description/provides or other display metadata is still required, add only a deterministic JSON-safe copied metadata projection owned by the exact Host observation implementation. Never return plugin instances, bound methods, Qt objects, Host-owned mutable mappings, or another registry.

## Required first actions

1. Read `AGENTS.md`, `CONTEXT.md`, ADR-0003, `docs/mainline_status.md`, the completed E27 plan, and this prompt.
2. Create an E28 phase plan under `docs/superpowers/plans/` before implementation.
3. Audit every Package Manager Loader/live-object access and the existing tests around list population, details, disable, protection, unload, and command-registry persistence.
4. Write genuine red tests before production changes.
5. Reuse `resolve_plugin_host(...)`, `observe_plugins()`, `unload_plugin()`, and the canonical AI command registry flow. Do not create another catalog authority, registry, plugin Host, lifecycle planner, package manifest authority, or composition root.

## Required invariants

- Project-persistent enable/disable remains owned by the canonical AI command registry.
- Immediate session unload remains validated by the exact recursive plugin Host.
- Protected plugins remain impossible to disable/unload through Package Manager.
- Package/project manifests, `.pond`, Inspector command binding, SR2D, Project World L4 lifecycle, Player/export, reload, and shutdown behavior remain unchanged.
- Observation results remain deterministic, JSON-safe, sorted, fresh-copy, and mutation-isolated.
- `PluginLoader` compatibility aliases remain available for external compatibility; E28 removes only targeted production consumers.
- No Qt/PyQt/UI type enters Qt-free Host Modules.
- Existing uncommitted migration work must not be reset, restored, cleaned, staged, committed, or deleted without explicit user instruction.

## Explicit non-goals

- Localization live menu/toolbar contribution refresh. That is concrete legacy Editor Adapter behavior and should be handled by a later dedicated Adapter Gate, not by exposing live plugins through the Qt-free Interface.
- broad PluginLoader facade deletion;
- replacement UI Host selection;
- native acceleration completion;
- real current-context OpenGL default-ready claims;
- signature dependency installation.

## Verification ladder

1. Record genuine E28 red tests.
2. Run focused observation + Package Manager + command registry + protected/unload tests.
3. Run expanded plugin lifecycle/reload/shutdown/Project World/package/Inspector/SR2D/Player/export/startup tests.
4. Run real offscreen Editor smoke.
5. Run the full suite excluding only `tests/test_package_signature_warn_only.py`.
6. Run all four architecture guardrails.
7. Record the signature environment blocker honestly.

## Closure rule

Update the E28 plan, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`; then create exactly one next-Gate prompt. Do not claim the persistent objective “彻底完善” is complete unless all remaining engine requirements have real evidence.
