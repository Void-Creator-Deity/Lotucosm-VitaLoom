# Phase E22 -- Qt-free Manual Hot-Reload Orchestration and Legacy PluginLoader Reload Adapter

- **Date:** 2026-07-21
- **Status:** completed
- **Previous Gate:** E21 completed the Qt-free `ProjectScopedPluginHost` extraction with focused `56 passed`, expanded `118 passed, 1 skipped`, full non-signature `1237 passed, 25 skipped, 34 subtests passed`, and all four architecture guardrails green.
- **Single objective:** move manual L3 extension hot-reload candidate import, planning, transition execution, report publication, and failure truth out of legacy `PluginLoader` into one Qt-free deep Module under the L1 version runtime; leave `PluginLoader` as an Editor/UI compatibility Adapter.

## Immutable architecture

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       single engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 VitaLoom capability/domain
            -> L3 engine extension / host adapter
            -> L4 Project World addon
```

E22 must not create another root, registry, manifest system, plugin model, or UI framework authority. PyQt6/QPainter/OpenGL remain legacy/current UI-host Adapters and cannot define the engine-plugin Interface.

## Current friction

`project/plugin_host_reload.py` already owns the deterministic reload-plan Implementation, and E20 `RuntimePluginHost` owns registry/import/callback execution. However, `kernel/plugin_loader.py` still owns roughly 327 lines of manual reload orchestration:

- report construction, canonical JSON publication, and blocked diagnostics;
- reloadable-plugin filtering;
- source validation and candidate import;
- candidate identity, metadata, activation-context, dependency, scope, and protection validation;
- plan composition;
- reverse-dependent deactivation;
- registry replacement and dependency re-resolution;
- dependency-first activation, skip propagation, failed-plugin facts, and truthful partial/rollback reporting.

This is non-UI engine behavior. Keeping it in the legacy Editor Adapter prevents direct headless/future-host use and weakens locality.

## Target Module and Interface

Create:

```text
core/VitaLoom/core/manual_plugin_reload_host.py
```

Primary Interface:

```python
ManualPluginReloadHost(runtime_plugin_host)
  .last_reload_report
  .list_reloadable_plugins() -> list[str]
  .reload_plugin(plugin_id) -> dict[str, Any]
```

The Module must compose:

- `RuntimePluginHost` for registry facts, candidate import, dependency ordering, and callbacks;
- `build_plugin_reload_plan` for candidate/affected closure and deterministic order;
- `plugin_activation_contract` for candidate activation metadata;
- canonical plugin ID/dependency rules.

The Module must not import PyQt6, EditorKernel, LayoutManager, `kernel.plugin_loader`, or `kernel.plugin_interfaces`.

## Compatibility Adapter design

`PluginLoader` must:

- construct exactly one `ManualPluginReloadHost` over its existing `RuntimePluginHost`;
- preserve public `list_reloadable_plugins()` and `reload_plugin()` by explicit delegation;
- preserve the legacy `last_reload_report` observation seam through delegation;
- preserve `last_lifecycle_report` visibility for operator/UI consumers after hot reload;
- keep UI contribution cleanup/registration, command bridge, signals, editor-ready behavior, and dock-tabify settling in the Loader/RuntimeHost Adapter seam;
- stop directly importing or calling `build_plugin_reload_plan`, activation parsing, candidate import validation, or reload transition loops.

## Red tests

Add headless tests for the new Interface before production extraction:

1. candidate import failure preserves old active registry and callbacks do not run;
2. active target reload deactivates reverse dependents and activates dependency-first, including a new dependency;
3. inactive target replacement mutates registry without callbacks;
4. missing/cyclic candidate dependencies block before mutation;
5. target activation failure reports `partial`, skips blocked dependents, and publishes failed-plugin facts truthfully;
6. first unload failure leaves the old registry candidate installed and reports `failed` without claiming rollback;
7. L4/core/unknown/protected targets are rejected before candidate import;
8. reloadable listing includes only regular-file, non-protected active L3 official/user extensions;
9. the Module is Qt-free and independent of legacy Loader/interfaces;
10. Loader source contains explicit construction/delegation and no direct reload plan/execution authority.

## Implementation steps

1. Add the E22 plan and red architecture/headless tests.
2. Implement `ManualPluginReloadHost` by moving orchestration without changing report schema or behavior.
3. Replace Loader-owned reload state/methods with narrow compatibility properties/delegates.
4. Update architecture test and `tools/check_project_plugin_model.py` to enforce authority location.
5. Run focused reload/runtime/project suites.
6. Run four architecture guardrails.
7. Run full non-signature suite; separately record the signature environment blocker without installing dependencies.
8. Close E22 docs and create exactly one fresh-session prompt for the next Gate.

## Acceptance evidence

E22 is complete only when:

- headless new-Module tests prove candidate-first and transition failure semantics;
- Loader compatibility tests prove unchanged public behavior;
- static guardrails reject direct Loader ownership of reload orchestration;
- focused and expanded regressions pass;
- all four architecture guardrails pass;
- the full non-signature suite passes;
- exact skips/blockers are recorded in `docs/mainline_status.md`;
- exactly one next Gate is named.

## Explicit non-goals

- no PyQt-host replacement in E22;
- no native/OpenGL readiness claim;
- no package-signature dependency installation;
- no changes to `.pond`, AI command registry, Inspector command binding, SR2D seams, package/project manifests, Player/export, or L3/L4 activation/lifecycle semantics;
- no Git cleanup, staging, commit, or revert of existing work.


## E22 Completion Record (2026-07-21)

### Delivered Module and Interface

- Added Qt-free `core/VitaLoom/core/manual_plugin_reload_host.py` with the deep `ManualPluginReloadHost` Interface.
- The Module composes the existing `RuntimePluginHost` and `build_plugin_reload_plan`; it does not create another registry, manifest system, framework root, or plugin model.
- It owns reloadable-target filtering, source/candidate preflight, activation-contract validation, reload planning, reverse-dependent deactivation, registry replacement, dependency-first reactivation, skip propagation, failed-plugin facts, canonical report publication, and truthful `blocked` / `failed` / `partial` / `settled` outcomes.
- It publishes the exact hot-reload report into `RuntimePluginHost.last_lifecycle_report` and supports one narrow observer for legacy lifecycle visibility.

### Legacy Adapter result

`PluginLoader` now constructs one `ManualPluginReloadHost` and preserves:

- `list_reloadable_plugins()` through explicit delegation;
- `reload_plugin(plugin_name)` through explicit delegation;
- `last_reload_report` as a compatibility observation property;
- the old private candidate-import seam as a pass-through to the Runtime Host, so existing compatibility tests and adapters remain valid.

The Loader no longer owns reload report construction, candidate validation, `build_plugin_reload_plan`, deactivation/activation loops, registry replacement, or failure/rollback semantics. It retains concrete UI contribution cleanup/registration, command bridging, kernel signals, legacy editor-ready behavior, and other Editor Adapter duties.

### Evidence

| Check | Result |
|---|---|
| Red proof before Module existed | `12 failed in 0.82s` (`ModuleNotFoundError` / missing authority) |
| New headless E22 Interface suite | `12 passed in 0.21s` |
| Focused new/legacy reload + E20/E21 compatibility | `48 passed in 1.17s` |
| Reload architecture and project-plugin guardrail focus | `38 passed in 0.62s`; `project plugin model OK` |
| Expanded plugin/project/operator/architecture regression | `131 passed, 1 skipped in 4.37s` |
| Architecture guardrails | `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK` |
| Source/syntax audit | changed Python files compile; no replacement/NUL characters; Loader has zero direct reload-plan/new-report markers |
| First full non-signature run | `1249 passed, 25 skipped, 34 subtests passed`, with one project-scale timing failure: cold asset index `11.65s` exceeded the existing `10.0s` threshold |
| Timing failure audit | isolated project-scale test immediately passed in `8.05s`; no E22 asset-index code was changed |
| Final full non-signature run | `1250 passed, 25 skipped, 34 subtests passed in 99.20s` |
| Signature-only suite | still blocked at collection because `.venv` lacks `cryptography`; no dependency was installed and no signature proof is claimed |

### Stable boundary and remaining work

E22 proves that manual L3 hot reload is now a Qt-free engine-plugin Host capability, shared with the legacy Editor Adapter. It does **not** prove overall engine completion, legacy PyQt Host replacement, native/OpenGL default-readiness, or package-signature verification.

**Unique next Gate: Phase E23 -- Qt-free Nested Plugin Host Composition Root and Legacy `PluginLoader` UI Adapter.** Consolidate construction and shared report/bootstrap orchestration for `RuntimePluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` behind one Qt-free L1 nested-plugin Host Interface. Require both headless and legacy Editor composition evidence. Keep `PluginLoader` as the concrete UI contribution/signal/command Adapter; do not duplicate any registry or begin a UI-shell migration in E23.
