# 2026-07-18 Engine Plugin Host Downstream-Extension Lifecycle Authority

## Purpose

Close the first real lifecycle seam for the user-confirmed nested framework topology:

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and downstream plugin-host framework
      -> versions/<version>/runtime
          -> L2 vitalloom.* capability/domain packages
          -> L3 engine extension plugins/adapters
          -> L4 project addons discovered only for an opened Project World
```

This phase does not replace the editor shell. PyQt6/QPainter/OpenGL remain legacy/current UI-host adapters. The phase moves downstream-extension lifecycle decisions behind a Qt-free Interface so another Host Adapter can execute the same plan later without redefining project/plugin semantics.

## Starting truth

- `PluginLoader` currently owns discovery, source collision choice, dependency sorting, activation, deactivation, project-addon replacement, UI registration, and Qt/editor callbacks in one Module.
- `plugin_activation.py` computes requested plugin ids but does not own a source catalog or transition ordering.
- `scan_project_addons()` clears the previous Project World's embedded plugins before the next addon discovery succeeds.
- `plugin.json` is only logged; it is not an authority and does not constrain entry path, plugin id, dependencies, or runtime compatibility.
- missing dependencies and dependency cycles are logged and loading continues, so lifecycle transitions can partially apply.
- project deactivation iterates current dictionary order rather than reverse dependency order.
- project-open events occur before addon sync and sync exceptions are swallowed, so `project_opened` does not mean downstream extensions are settled.
- workspace extensions are sources/development areas and must not become cold-start globally enabled plugins.

## Decisions

### 1. Qt-free deep Module

Add `core/VitaLoom/project/plugin_host_lifecycle.py` as the authority Module. Its public Interface owns:

- normalized downstream-extension catalog entries and source scopes;
- deterministic source collision diagnostics;
- dependency closure and missing-dependency rejection;
- cycle rejection;
- dependency-first activation order;
- reverse-dependency deactivation order;
- protected-plugin retention;
- exact JSON-safe lifecycle plan/report facts.

The Module imports no PyQt6 and creates no editor singleton. The Interface is the test surface.

### 2. Scope model

Keep existing public scope strings for compatibility:

```text
core_mod      L3 protected engine Host/bootstrap extension

official_mod  L3 official engine extension
user_mod      workspace extension source/development adapter
embedded_mod  L4 current Project World addon
unknown       compatibility/test source only
```

These scopes are downstream scopes inside the L1 engine plugin. None becomes a FrameCore/L1 plugin, and `vitalloom.*` remains a capability/domain package id rather than a plugin-host level.

### 3. Project addon manifest authority

Each immediate `<project>/addons/<addon>/` directory that contributes a plugin must contain `plugin.json`. The supported schema for this phase is:

```json
{
  "schema_version": 1,
  "id": "ExamplePlugin",
  "version": "1.0.0",
  "entry": "example_plugin.py",
  "runtime": {
    "plugin_id": "lotucosm-vitaloom",
    "version": ">=1.0.0,<2.0.0"
  },
  "dependencies": ["OtherPlugin"]
}
```

Authority rules:

- addon discovery occurs only after a project-open flow supplies a project path;
- addon directories, manifests, and entries must remain contained by the canonical Project World root;
- symlinked addon directories, manifests, or entries fail closed in this phase;
- `entry` must be one relative `*_plugin.py` file and may not contain traversal;
- manifest id/version/dependencies must match `get_plugin_info()` after the Adapter imports the entry;
- runtime `plugin_id` must be `lotucosm-vitaloom` and the version constraint must accept the current version runtime;
- malformed, duplicate, incompatible, escaping, or colliding addon sources block the new addon catalog before the previous Project World catalog is removed.

No recursive arbitrary `*_plugin.py` scan is an authority for L4 after this phase.

### 4. Adapter convergence

`PluginLoader` remains the concrete Editor/PyQt Host Adapter. It may:

- import an already-authorized entry file;
- instantiate `IEditorPlugin`;
- call `on_load`, provider registration, `on_editor_ready`, UI cleanup, and `on_unload`;
- emit existing kernel signals.

It may not independently choose lifecycle order or continue through a blocked lifecycle plan. It executes the Qt-free plan and records the returned report.

### 5. Project-switch safety

New addon discovery and metadata/import validation must complete before the old embedded catalog is removed. Discovery failure leaves the prior catalog and active set unchanged.

Applying plugin callbacks cannot be made fully transactional in Python/Qt in this phase. If an Adapter callback fails, the report must state the exact completed and failed actions and stop further unsafe actions; no success event may claim the lifecycle settled.

### 6. Project events

Preserve existing `project_opened` for compatibility; it continues to mean the project/scene context has been selected, not that extensions settled.

`project_plugins_synced` must carry the lifecycle report and only publish a settled success report when planning and Adapter execution succeed. A blocked/partial report is published under `project_plugin_lifecycle_failed`. Existing `.pond`, scene signals, AI command registry ownership, Inspector binding, SR2D seams, package manifests, and project manifests remain unchanged.

## Implementation order

1. Add red Qt-free tests for lifecycle planning and addon manifest discovery.
2. Implement `plugin_host_lifecycle.py` until those tests pass.
3. Add red PluginLoader Adapter tests for transactional discovery, reverse deactivation, blocked dependency/cycle transitions, and exact reports.
4. Converge `PluginLoader` on the lifecycle Module without changing provider registration Interfaces.
5. Update `ProjectManager` event/report handling and project-close embedded cleanup.
6. Reconcile `CONTEXT.md` and architecture docs so L2/L3/L4 have one meaning.
7. Run focused regression and architecture guardrails.

## Defensive test matrix

- cold start catalog excludes project addons;
- workspace extensions remain sources and are not automatically activated;
- addon discovery requires project-open path and manifest;
- malformed JSON/schema/id/version/entry/runtime/dependencies fail closed;
- absolute/traversing/escaping/symlink addon paths fail closed;
- duplicate ids and source collisions are deterministic;
- runtime version incompatibility blocks discovery;
- missing dependency and cycle produce no transition actions;
- activation is dependency-first;
- deactivation is reverse dependency order;
- protected plugins are retained explicitly;
- failed new-project discovery preserves the prior embedded catalog and active state;
- callback failure produces partial/failed report rather than settled success;
- project addons never enter the FrameCore plugin manifest or `vitalloom.*` capability catalog.

## Verification

Focused:

```powershell
python -m pytest -q tests/test_plugin_host_lifecycle.py tests/test_plugin_activation.py tests/test_plugin_loader_failure_isolation.py tests/test_engine_plugin_host_architecture.py tests/test_project_plugin_model_gate.py
```

Guardrails:

```powershell
python tools/check_project_plugin_model.py
python tools/check_core_boundaries.py
python tools/check_gui_boundaries.py
python tools/check_release_consistency.py
```

Also run Python import/compile smoke for changed runtime Modules and `git diff --check`. Record environment-dependent skips without fake Qt or fake filesystem behavior.

## Non-goals

- changing the L0 FrameCore plugin loader;
- promoting `vitalloom.*` capability packages to FrameCore plugins;
- replacing PyQt6, QPainter, or the current opt-in OpenGL path;
- watcher/hot-reload redesign;
- package installation/resolution redesign;
- automatic stale-lock recovery;
- transactional rollback of arbitrary third-party Qt callback side effects;
- changing `.pond`, AI command registry, Inspector, SR2D, package manifest, or project manifest semantics.

## Completion and next gate

E5 completes only when the Qt-free lifecycle Module, project-addon manifest authority, PluginLoader Adapter convergence, event reports, tests, guardrails, `docs/mainline_status.md`, and fresh-session prompt all agree.

After E5 closes, the single next gate is **Phase E6 — Downstream Extension Operator Inspection and Failed-Lifecycle Recovery Authority**.
