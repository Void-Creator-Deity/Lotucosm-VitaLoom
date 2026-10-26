# 2026-07-18 Downstream Extension Hot-Reload / Watcher Lifecycle Authority

## Purpose

Continue the user-confirmed nested framework topology:

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and downstream plugin-host framework
      -> versions/<version>/runtime (versioned runtime boundary)
          -> L2 vitalloom.* capability/domain packages
          -> L3 engine extension plugins/adapters
          -> L4 project addons scoped to one Project World
```

Phase E5 made normal downstream-extension discovery and transitions authoritative. Phase E6 added canonical live Host inspection and confirmation-bound failed-lifecycle retry. The remaining manual hot-reload path still predates both authorities and can mutate Adapter state directly.

## Starting truth

- No automatic filesystem watcher currently exists. Repository search finds only manual F5/Ctrl+Shift+F5 UI actions and `PluginLoader.reload_plugin()`.
- `HotReloadPlugin._reloadable_plugins()` currently lists every non-protected non-core active plugin, including L4 `embedded_mod` addons, although its batch action only filters `user_mod`.
- `PluginRuntimeOpsMixin` directly calls `reload_plugin()` and `unload_plugin()`; project disable writes the manifest through the shared command and then performs a separate direct unload rather than normal lifecycle sync.
- `PluginLoader.reload_plugin()` unloads the old instance before candidate import/identity/dependency validation.
- import/name/callback failure can therefore leave the old plugin absent or a new partially loaded instance retained; no canonical reload report, dependency skip report, operator recovery, or rollback proof exists.
- reload updates dependency metadata without `normalize_dependency_ids`, does not validate missing/cyclic dependencies, and does not deactivate active dependents in reverse dependency order.
- direct L4 reload bypasses `<project>/addons/*/plugin.json` id/version/dependency/runtime/containment authority and the requested-versus-retained Project World semantics.
- protected checks exist, but they are only local guards and do not make the reload path lifecycle-authoritative.

## Decisions

### 1. No automatic watcher in E7

E7 will not add `QFileSystemWatcher`, watchdog, polling, or background reload. A future watcher Adapter may only emit debounced source-change facts into a Qt-free Interface; it may not call plugin callbacks, rescan arbitrary directories, or reload automatically.

This is a contract decision, not a claim that watcher support is complete.

### 2. L3 reload and L4 refresh are different operations

- L3 `official_mod` / `user_mod` extension replacement may use the manual hot-reload authority.
- L4 `embedded_mod` addon code must never use direct single-file reload. It must re-enter normal Project World manifest discovery and lifecycle sync so id/version/dependencies/runtime/containment and requested/retained catalog rules remain authoritative.
- `core_mod`, protected, unknown-scope, missing-source, and non-regular-source targets fail closed.

### 3. Qt-free reload planning Module

Add `core/VitaLoom/project/plugin_host_reload.py`. Its Interface owns deterministic planning only:

- normalize current/candidate catalog facts;
- validate target identity, allowed scope, source continuity and protected state;
- validate candidate dependency closure and cycles before mutation;
- compute active transitive dependents of the target;
- compute reverse-dependency deactivation order;
- compute dependency-first activation order after replacement, including newly required dependencies;
- return JSON-safe `ready / blocked` plan facts and diagnostics.

The Module imports no PyQt and never imports plugin source or invokes callbacks.

### 4. Candidate-first Adapter execution

`PluginLoader` remains the current Host Adapter and must execute in this order:

1. read current host/catalog facts;
2. import and instantiate the candidate before any unload;
3. validate exact plugin id and normalize candidate version/dependencies;
4. obtain a Qt-free reload plan;
5. if blocked, perform zero unload/load callbacks;
6. if target is inactive, replace only the registry metadata and instance;
7. if active, deactivate the target's active dependent closure in plan order;
8. install the candidate registry entry;
9. activate the planned closure dependency-first, recording completed, failed and skipped actions;
10. publish one canonical `last_reload_report` and update the ordinary lifecycle report with source `hot_reload`.

E7 does not claim generic rollback. Once an old callback successfully unloads, later failure may require manual repair or process restart. Reports must say so explicitly.

### 5. UI Adapter convergence

- HotReloadPlugin and plugin manager UI may only list L3 reload candidates exposed by the loader authority.
- They must consume the canonical reload result rather than assuming a boolean means stable.
- Project enable/disable must converge on normal project lifecycle sync; direct post-command unload is forbidden.
- E7 adds no new recovery panel.

### 6. Shared command decision

The canonical AI-native command shape is reserved as:

```text
plugin.host.reload.inspect
plugin.host.reload.resolve
```

Implementation is required only if the candidate/report/source identity can be bound without weakening E6 stale-report semantics. If not completed in E7, the plan and mainline status must explicitly leave these commands unregistered rather than add a shallow pass-through Interface.

## Defensive test matrix

- no automatic watcher dependency or PyQt import enters the Qt-free Module;
- ready plan for one active L3 plugin deactivates target then activates candidate;
- active transitive dependents deactivate reverse-dependency-first and reactivate dependency-first;
- newly required dependency is activated before the candidate;
- missing/cyclic candidate dependencies block before any callback;
- core/protected/unknown/L4 targets block;
- candidate import or id mismatch executes zero unload callbacks and preserves old active instance;
- failed unload/load yields exact partial/failed report and dependency skips;
- inactive target replacement invokes no lifecycle callbacks;
- UI candidate listing excludes L4/core/protected targets;
- project disable no longer performs a direct independent unload;
- E5 lifecycle, E6 operator, command registry, package/project model and architecture gates remain green.

## Verification

Focused tests must include new reload authority tests plus:

```powershell
python -B -m pytest -q tests/test_plugin_hot_reload.py tests/test_plugin_host_lifecycle.py tests/test_plugin_loader_lifecycle_authority.py tests/test_plugin_host_operator.py tests/test_plugin_loader_operator_recovery.py tests/test_plugin_command_contributions.py tests/test_engine_plugin_host_architecture.py tests/test_project_plugin_model_gate.py
```

Guardrails:

```powershell
python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B tools/check_gui_boundaries.py
python -B tools/check_release_consistency.py
```

Also run AST/import smoke, targeted whitespace checks and `git diff --check`. Record the known no-PyQt headless failures truthfully; do not fake Qt.

## Non-goals

- automatic file watching or background reload;
- L4 single-file hot reload;
- generic callback rollback or state migration between plugin instances;
- force unload/import, protected bypass, manifest editing, or dependency-cycle best effort;
- replacing PyQt or choosing a successor app shell;
- changing `.pond`, Inspector binding, SR2D seams, package/project manifests, or the L0/L1/L2/L3/L4 topology.

## Completion and next gate

E7 completes only when the Qt-free reload plan, candidate-first Adapter execution, L3/L4 separation, UI convergence, tests, guardrails, `docs/mainline_status.md`, and a fresh-session prompt agree.

The single next Gate after E7 will be selected only from evidence produced by this phase; do not predeclare it now.

## Completion evidence

- Initial red: `17 failed` across the missing Qt-free Module and legacy Adapter/UI paths.
- Focused E7 reload/operator proof: `32 passed in 0.61s`.
- Expanded E7/E6/E5 regression: `49 passed, 1 skipped in 1.16s`; the sole skip is the real Windows L4 directory-symlink permission limitation.
- Project plugin model, core, GUI, and release consistency guardrails passed.
- AST/import smoke, modified-region trailing-whitespace checks, and targeted `git diff --check` passed.
- No automatic watcher was added. `plugin.host.reload.inspect` and `plugin.host.reload.resolve` remain intentionally unregistered until stale-safe candidate/source/report identity exists.

E7 is complete. The unique next Gate is **Phase E8 — Host Adapter Independence for Project World and Runtime Replay Application Seams**.

