# Phase E27 -- Qt-free Project World Plugin Lifecycle Consumer Decoupling and Legacy ProjectManager Kernel Isolation

## Resume point

E26 is complete on 2026-07-21. The authoritative recursive framework remains:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       sole engine/product plugin and recursive downstream plugin Host
       -> versions/1.0.0/runtime
            -> L2 capability/domain packages
            -> L3 engine extensions / Host Adapters
            -> L4 Project World addons
```

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` is the product runtime boundary. PyQt6/QPainter/current OpenGL are legacy/current UI Host Adapters, not the engine root, extension authority, plugin specification, or future framework rule source. Do not migrate the project to Unity, Godot, Unreal, Electron, or another shell.

The exact `NestedPluginHost` composes one `RuntimePluginHost`, one `ManualPluginReloadHost`, one `ProjectScopedPluginHost`, and one shutdown authority over one exact registry. E26 added the Qt-free `PluginHostControlObservation` Interface and publishes that exact nested Host through the existing runtime capability registry and `CapabilityPublicationLease`.

## E26 evidence to preserve

- genuine red baseline: `4 failed, 1 passed`;
- final focused Interface/publication/consumer proof: `43 passed in 1.16s`;
- expanded plugin lifecycle/Loader/Editor/Adapter proof: `106 passed in 2.00s`;
- Project World/package/AI command/Inspector/SR2D/Player/export/startup compatibility: `210 passed in 16.33s`;
- real offscreen editor smoke: `plugins=13/20`, no discovery/load failures, deterministic shutdown;
- full non-signature: `1296 passed, 25 skipped, 34 subtests passed in 129.32s`;
- project plugin model, core boundary, GUI boundary, and release consistency guardrails all passed;
- signature-only collection remains blocked because `.venv` lacks `cryptography`; do not install it during this Gate unless the user explicitly changes direction.

## Concentrated remaining friction

`core/VitaLoom/project/project_manager.py` still reaches through the legacy UI kernel to call:

```python
kernel.plugin_loader.scan_project_addons(...)
kernel.plugin_loader.sync_plugins_for_project(...)
```

Those operations are already owned by the exact Qt-free `ProjectScopedPluginHost` and exposed by the E26 plugin Host capability. Leaving the calls on `kernel.plugin_loader` makes Project World lifecycle code depend on a concrete PyQt-era compatibility facade and weakens the recursive engine-plugin architecture.

Known call sites at E26 closure are around project open/load and project close/reset paths (previous audit: lines near 1062/1071 and 1311/1312; re-run `rg` because line numbers may move).

## E27 single objective

Migrate Project World L4 addon scan/sync consumers in `ProjectManager` from direct `kernel.plugin_loader` access to the exact already-published Qt-free plugin Host capability, while preserving all existing Project World lifecycle ordering, manifest semantics, rollback/failure truth, reports, and Editor/Player/headless compatibility.

## Required first actions

1. Read `AGENTS.md`, `CONTEXT.md`, ADR-0003, `docs/mainline_status.md`, the E26 plan, and this prompt.
2. Create a new E27 phase plan under `docs/superpowers/plans/` before implementation.
3. Audit every `ProjectManager` open/load/close/reset call path around addon discovery and lifecycle synchronization, including exception and rollback paths.
4. Write genuine red tests proving the current direct Loader dependency and the required capability-based behavior before changing production code.
5. Reuse `resolve_plugin_host(...)` and the existing exact `PluginHostControlObservation.scan_project_addons(...)` / `sync_plugins_for_project(...)` Interface. Do not add a second registry, project plugin Host, lifecycle planner, manifest parser, or composition root.

## Required invariants

- `.pond` scene semantics remain unchanged.
- Project manifests and package manifests remain unchanged.
- AI command registry flows and Inspector command binding remain unchanged.
- SR2D public seams remain unchanged.
- Player/export behavior remains unchanged.
- Project World L4 discovery, activation, deactivation, close/reset ordering, reports, rollback, and recovery behavior remain truthful and deterministic.
- `ProjectScopedPluginHost` remains the only Project plugin lifecycle authority.
- `PluginLoader` compatibility aliases/delegates remain available for external compatibility; E27 removes only the targeted production dependency.
- Missing/unavailable capability behavior must fail closed with explicit report/error evidence; do not silently skip L4 lifecycle work.
- No Qt/PyQt/EditorKernel/LayoutManager import may enter Qt-free Host Modules.
- Existing uncommitted migration work is user/prior work: do not reset, restore, clean, stage, commit, or delete unrelated changes.

## Explicitly out of scope

- Package Manager live plugin metadata/contribution migration;
- Localization live menu/widget contribution enumeration;
- broad removal of `PluginLoader` compatibility aliases;
- replacement UI Host selection or migration;
- native acceleration completion;
- OpenGL default-ready claims;
- signature dependency installation.

Package Manager and Localization require concrete live plugin instances today. Keep those behaviors behind or move them deeper into the existing `LegacyEditorPluginAdapter` seam in a later dedicated Gate; do not widen the Qt-free observation Interface to leak plugin objects.

## Verification ladder

1. Record the genuine E27 red baseline.
2. Run focused ProjectManager/capability/ProjectScopedPluginHost/open-close-transition tests.
3. Run plugin lifecycle, Loader compatibility, Project World recovery, package/project manifests, AI command, Inspector, SR2D, Player/export, and editor smoke tests.
4. Run real `runtime/main.py --smoke-editor` offscreen.
5. Run the full suite excluding only `tests/test_package_signature_warn_only.py`.
6. Run:
   - `tools/check_project_plugin_model.py`
   - `tools/check_core_boundaries.py`
   - `tools/check_gui_boundaries.py`
   - `tools/check_release_consistency.py`
7. Confirm the signature test still fails only for missing `cryptography`, and record that limitation honestly.

## Closure rule

At E27 completion, update the E27 plan, `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and create exactly one fresh-session prompt naming one next Gate. Do not claim the persistent project objective `彻底完善` is complete unless every remaining project requirement is actually proven complete.