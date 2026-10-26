# Phase E23 -- Qt-free Nested Plugin Host Composition Root and Legacy PluginLoader UI Adapter

- **Date:** 2026-07-21
- **Status:** completed
- **Previous Gate:** E22 completed `ManualPluginReloadHost`, Loader reload delegation, final non-signature `1250 passed, 25 skipped, 34 subtests passed`, and all four architecture guardrails.
- **Single objective:** replace legacy `PluginLoader` as the practical sub-Host composition root with one Qt-free L1 `NestedPluginHost` Module that composes E20/E21/E22 over exactly one runtime registry; preserve Loader as the concrete legacy UI contribution/signal/command Adapter and public compatibility facade.

## Immutable architecture

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       one engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 engine extension / host adapter
            -> L4 Project World addon
```

The new composition root remains inside the L1 version runtime. It is not a FrameCore plugin, second framework root, Project World root, UI shell, or replacement registry.

## Remaining PluginLoader audit

| Current Loader responsibility | E23 classification | Destination |
|---|---|---|
| construct `RuntimePluginHost`, `ProjectScopedPluginHost`, `ManualPluginReloadHost` | Qt-free composition authority | `NestedPluginHost` |
| alias registry/loaded/dependency/order/failure/discovery/scope/source/protected facts | compatibility observation seam | delegate/alias the one Runtime Host exposed by `NestedPluginHost` |
| directory/layered discovery and final dependency resolution | Qt-free nested Host bootstrap | `NestedPluginHost` |
| eager vs bootstrap/Player target selection and dependency expansion | Qt-free nested Host bootstrap | `NestedPluginHost` with narrow resolvers |
| lifecycle/reload report synchronization across sub-Hosts | Qt-free composition authority | `NestedPluginHost` |
| L4 project scan/sync/inspection/recovery and L3 manual reload | compatibility delegation | Loader -> `NestedPluginHost` sub-Interfaces |
| activation context projection from current Host context | concrete Host resolver seam | Loader callback passed to `NestedPluginHost` |
| dock/menu/viewport/theme/command registration, editor-ready callback, cleanup, kernel signals, layout settling | legacy UI Adapter duty | remain in `PluginLoader` |
| candidate import/invalidate/unload/load helper names | compatibility pass-through | Loader -> `NestedPluginHost.runtime_plugin_host` |
| operator adapter binding | compatibility/runtime publication seam | remain until its consumers are separately migrated |

## Target Module

Create:

```text
core/VitaLoom/core/nested_plugin_host.py
```

Primary Interface:

```python
NestedPluginHost(...)
  .runtime_plugin_host
  .project_scoped_plugin_host
  .manual_plugin_reload_host
  .last_lifecycle_report
  .load_from_directories(...)
  .load_from_layered_directories(...)
  .set_scope_overrides(...)
  .execute_lifecycle_target(...)
  .activate_plugins_matching(...)
  .clear_embedded_plugins / scan_project_addons / sync_plugins_for_project
  .inspect_plugin_host / list_plugin_host_recoveries / resolve_plugin_host_recovery
  .list_reloadable_plugins / reload_plugin
```

The Interface may expose additional narrow compatibility facts, but it must not mirror every Loader UI method.

## Composition invariants

- Exactly one `RuntimePluginHost` object owns all registry facts.
- E21 and E22 sub-Hosts receive that exact object.
- No sub-Host may create, copy, or shadow registry dictionaries.
- Lifecycle reports produced by bootstrap/Project World/manual reload remain canonical and visible as one coherent `NestedPluginHost.last_lifecycle_report` fact.
- The legacy Loader's `last_lifecycle_report` and `last_reload_report` remain compatible observation seams.
- A narrow post-transition callback may let the concrete UI Adapter settle layout, but Qt-free lifecycle execution and report ownership remain in `NestedPluginHost`.
- Bootstrap target selection preserves eager mode, Player allowlist, bootstrap package IDs, dependency expansion, and activation-only semantics.
- Candidate import remains owned by the Runtime Host; the legacy private pass-through remains patchable for compatibility tests.

## Red tests

1. Headless construction creates all three sub-Hosts over one registry without PyQt/legacy interfaces.
2. Headless layered discovery and bootstrap activation use the same lifecycle rules and produce coherent reports.
3. Project-scoped sync and manual reload update the same composition-level lifecycle observation.
4. A post-transition Adapter callback receives exact reports without becoming the authority.
5. Legacy Loader constructs only `NestedPluginHost`, aliases the one Runtime Host state, and delegates bootstrap/project/reload Interfaces.
6. Loader retains UI contribution Adapter markers and `RuntimePluginHostAdapter` behavior.
7. Static architecture gates reject direct Loader construction of E20/E21/E22 sub-Hosts and reject Qt/Loader/interface imports in the new Module.

## Implementation sequence

1. Add this plan and red tests.
2. Implement `NestedPluginHost` with headless defaults and narrow resolver/Adapter callbacks.
3. Move Loader directory/layered/bootstrap/report/sub-Host construction into the new Module.
4. Preserve Loader public methods and state aliases through explicit delegation.
5. Update `tests/test_engine_plugin_host_architecture.py` and `tools/check_project_plugin_model.py`.
6. Run focused plugin Host/bootstrap/project/reload tests.
7. Run expanded Editor/Player/startup/package/project regressions.
8. Run all four architecture guardrails and full non-signature suite.
9. Record the signature environment blocker without installing dependencies.
10. Close status/context/index/prompt with exactly one next Gate.

## Non-goals

- no PyQt replacement or new UI framework;
- no editor contribution contract redesign;
- no native/OpenGL readiness claim;
- no signature dependency installation;
- no `.pond`, AI command, Inspector, SR2D, manifest, Player/export, L3/L4 lifecycle, or ID/schema change;
- no Git cleanup/staging/commit/revert of unrelated work.


## Completion record

- Red baseline: the new headless composition and Loader-delegation tests initially produced `7 failed`, proving that the composition-root Module and Loader wiring were absent.
- Implementation: added Qt-free `core/VitaLoom/core/nested_plugin_host.py`; it constructs exactly one `RuntimePluginHost` and composes `ProjectScopedPluginHost` plus `ManualPluginReloadHost` over that exact runtime object. Legacy `PluginLoader` now constructs only `NestedPluginHost`, exposes compatibility aliases/delegates, and retains concrete Editor contribution duties.
- Focused proof after final cleanup: `45 passed in 1.14s` across nested/runtime/project/reload/activation/architecture tests; relevant `py_compile` checks passed.
- Expanded regression: `145 passed, 1 skipped in 11.09s` across plugin activation, operator, Loader, Player/startup/export/layout and FrameCore paths.
- Final full non-signature proof: `1258 passed, 25 skipped, 34 subtests passed in 120.27s` on 2026-07-21.
- Final architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Environment blocker: `tests/test_package_signature_warn_only.py` still fails during collection with `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed, so package-signature verification is not claimed.
- Stable now: one Qt-free L1 nested plugin Host composition root owns E20/E21/E22 wiring, bootstrap and coherent lifecycle/reload observations; headless and legacy Editor compositions use the same Host contracts.
- Still open: the legacy Editor contribution Adapter remains embedded in `PluginLoader`; PyQt/QPainter/OpenGL remain legacy/current Host Adapter implementations; no replacement UI Host, native acceleration completion, or OpenGL default-readiness is claimed.

**Unique next Gate: Phase E24 -- Legacy Editor Plugin Contribution Adapter Extraction and `PluginLoader` Compatibility Facade.** Extract the concrete legacy Editor contribution/command/signal/editor-ready/cleanup/layout behavior behind the existing Qt-free `RuntimePluginHostAdapter` seam, keep `PluginLoader` as a narrow compatibility facade, and preserve all L0-L4, manifest, command, Inspector, SR2D, Player/export, and public Loader semantics. Do not begin a UI-shell replacement in E24.
