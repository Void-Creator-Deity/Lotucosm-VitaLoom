# Phase E17 — Plugin Activation Contract Schema, External Extension Compatibility, and Context-Kind Manifest Validation Authority

- **Date:** 2026-07-20
- **Status:** Complete
- **Previous Gate:** E16 Plugin Activation Context Projection and Legacy UI Context Compatibility Authority is complete.
- **Unique scope:** turn `activation_context` from a loader-only metadata convention into one Qt-free runtime contract shared by plugin metadata validation, L3/L4 discovery, lifecycle catalog facts, reload candidate checks, and operator inspection.

## Architecture invariant

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin
       and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 engine extensions / Host Adapters
          -> L4 addons scoped to one Project World
```

The E17 contract remains inside `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. It must not create a new FrameCore plugin, a third registry, a Project World root, or a universal Host context.

## E16 gate evidence

```text
E16 red: 6 failed
E16 focused: 50 passed
E13–E16/plugin lifecycle/PS replay expanded: 65 passed
Current loader/lifecycle/operator recheck: 48 passed, 1 skipped
Full suite excluding unavailable signature file: 1207 passed, 25 skipped, 34 subtests passed
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
```

The repository `.venv` still lacks `cryptography`; `tests/test_package_signature_warn_only.py` is not claimed as verified.

## Audit findings

1. Official L3 plugin metadata currently comes from `get_plugin_info()` and is checked only opportunistically by `PluginLoader._discover_plugin`; there is no shared contract module for `activation_context` type, allowed values, default, or diagnostics.
2. L4 `addons/<id>/plugin.json` is validated by the Qt-free lifecycle Module, but `activation_context` is not part of `ProjectAddonSource`, catalog facts, manifest-to-code parity, or discovery diagnostics.
3. `PluginLoader._activation_context_for()` repeats the allowed-value rule locally, so discovery, activation, reload, and operator inspection can disagree.
4. Operator catalog reports expose plugin identity, scope, version, dependencies, and protection, but not context kind; an operator cannot distinguish legacy-default compatibility from explicit runtime activation.
5. Existing third-party/legacy manifests omit the field and must remain valid with a deterministic `legacy_ui` default. A declared value must be a string and one of `legacy_ui` or `runtime`; unknown/type-invalid values must fail closed before importing/activating code.

## Contract ruling

- Add a Qt-free `plugin_activation_contract.py` Module under `core/VitaLoom/core`.
- The formal contract owns:
  - `legacy_ui` and `runtime` constants;
  - deterministic default `legacy_ui` when the field is absent;
  - strict type/allowed-value validation;
  - explicit-vs-default fact reporting;
  - manifest/code parity validation;
  - JSON-safe diagnostics suitable for discovery/operator reports.
- Do not infer context from `provides`, imports, or callback signatures.
- L4 manifests may omit `activation_context` for compatibility; omission is reported as defaulted legacy UI, not as an error.
- If an L4 manifest declares a context kind, the imported plugin metadata must resolve to the same kind; mismatch blocks the candidate before it enters the active embedded catalog.
- Official/user/embedded plugin discovery and reload must use the same validator. Unknown values fail before `on_load`; malformed manifest values fail before plugin import.
- Catalog/operator facts include `activation_context` and whether it was explicit. The report remains read-only and JSON-safe.
- Do not migrate any additional UI plugin in E17.

## Red-test and implementation sequence

1. Add red tests for a Qt-free contract Module: default, explicit allowed values, type errors, unknown values, stable diagnostic facts, and manifest/code parity.
2. Add red tests proving L4 discovery rejects unknown/type-invalid manifest context before importing entry code, while old manifests default to `legacy_ui`.
3. Add red tests proving official PluginLoader discovery rejects invalid `get_plugin_info()` context before registry insertion, and reload candidate metadata uses the same validator.
4. Add red tests proving lifecycle catalog and operator inspection expose `activation_context` and `activation_context_explicit` without exposing UI objects.
5. Implement the contract Module and migrate Loader, L4 lifecycle discovery, catalog projection, and operator normalization to it.
6. Run focused contract/discovery/loader/reload/operator tests, then E13–E16 regressions, Project World/manifest/Player/export/command/Inspector/SR/PS suites, full suite, four architecture gates, AST/import/whitespace checks.
7. Update `CONTEXT.md`, `docs/mainline_status.md`, this plan, and create exactly one fresh-session prompt naming exactly one next Gate.

## Acceptance evidence

- One Qt-free contract Module is the authority for both plugin metadata and L4 manifest context kind.
- Missing field remains backward-compatible and deterministically resolves to `legacy_ui` with an explicit diagnostic fact.
- Invalid type and unknown value fail closed before import/activation and produce stable codes.
- Manifest/code mismatch is blocked before the candidate enters the active catalog.
- Official discovery, L4 discovery, reload, lifecycle catalog, and operator inspection use the same context-kind facts.
- No L0–L4 topology, `.pond` semantics, AI Command Registry, Inspector binding, SR2D seam, package/project manifest ownership, Player/export, or lifecycle authority is broken.

## Non-goals

- No universal RuntimeHostContext or god context.
- No automatic context inference.
- No one-shot removal of EditorContext/PyQt.
- No migration of explicit UI plugins.
- No new FrameCore plugin layer or Project World root framework.
- No change to the separate legacy event namespaces.

## E17 completion evidence (2026-07-20)

Implementation is complete inside the versioned L1 runtime boundary:

- Added Qt-free `core/VitaLoom/core/plugin_activation_contract.py` as the single authority for `legacy_ui`/`runtime`, strict type and allowed-value validation, default-vs-explicit facts, manifest/code parity, and stable diagnostics.
- L4 `discover_project_addons()` now validates manifest metadata before entry import, preserves omitted-field compatibility as default `legacy_ui`, and exposes context facts in `ProjectAddonSource`.
- `PluginHostCatalogEntry` and operator inspection now expose `activation_context`, `activation_context_explicit`, and `activation_context_source` without exposing UI/Host objects.
- `PluginLoader` now validates official/user/embedded discovery metadata, L4 manifest/code parity, activation dispatch, and hot-reload candidate metadata through the same contract. Invalid values fail closed before registry insertion or `on_load`.
- No additional UI plugin was migrated; the L0/L1/L2/L3/L4 topology and legacy PyQt Host Adapter boundary remain unchanged.

Verification:

```text
E17 focused contract tests: 8 passed
E17 loader/lifecycle/operator expansion: 45 passed, 1 skipped
E13?E17 combined regression: 131 passed, 1 skipped
Full suite excluding tests/test_package_signature_warn_only.py: 1214 passed, 25 skipped, 34 subtests passed, 1 failed
Architecture gates: project plugin model OK; core boundaries OK; GUI boundaries OK; release consistency OK
```

The single full-suite failure is the pre-existing 1000-asset project-scale performance threshold (`cold_seconds=14.0478569`, required `<10.0`) in `tests/test_asset_index_project_scale.py`; it is unrelated to E17 activation-contract changes and remains an explicit follow-up debt. The signature test remains unverified because the repository `.venv` lacks `cryptography`.

## Unique next Gate

**Project World Host Adapter Factory, Ownership and Disposal Composition Authority** ? make concrete Editor/Player Host acquisition, reuse, ownership, exact disposal, and capability cleanup explicit without changing the recursive framework/plugin topology.

