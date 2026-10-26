# 2026-07-18 Engine Plugin Host Architecture Reconciliation

**Status:** completed

## Purpose

Reconcile the written architecture and project instructions with the repository's implemented extension topology before continuing package-transaction work. This is a contract clarification only: it does not migrate the existing UI or change runtime loading behavior.

## Verified topology

```text
L0 FrameCore (root framework)
  └─ L1 lotucosm-vitaloom (the sole FrameCore engine/product plugin)
       ├─ hub (version selection and project portal)
       └─ versions/<version>/runtime (versioned engine runtime boundary)
            ├─ L2 engine capability packages (`vitalloom.*`)
            ├─ L3 engine extension plugins / adapters (official, installed, or workspace sourced)
            └─ L4 project addons (only discovered and activated after project-open)
```

- `FrameCore/suite_registry.py` discovers only the L1 `lotucosm-vitaloom` manifest and does not import product runtime capabilities.
- `plugin_manifest.json` selects `hub` and `versions/1.0.0`; `version_manifest.json` defines the runtime boundary and builtin capability catalog.
- `PluginLoader.scan_project_addons()` clears prior embedded plugins and scans `<project>/addons/` only after a project path is available.
- The package catalog declares `vitalloom.*` capability packages. Those packages do not become L0/L1 plugins merely because they contribute an editor plugin.
- The existing PyQt6 `EditorKernel` and related UI code are legacy host-adapter implementation. They are not the engine root, extension authority, or a requirement for new framework/plugin rules.

## Decisions

1. Preserve the single L1 engine-plugin invariant: no second peer FrameCore application plugin is introduced.
2. Treat L1 and its versioned runtime as a nested plugin-host framework. New engine extensions must bind to its runtime contracts, manifests, command authority, and lifecycle seams.
3. Keep capability declaration, extension implementation, and project addon scope distinct. A project addon cannot be pulled into cold-start global discovery.
4. Do not force an immediate UI-host migration. If a host is replaced later, preserve the Qt-free engine/plugin contracts first and implement the host as an adapter.
5. Continue Phase E3 only through Qt-free transaction-domain and command-registry seams; no recovery rule may depend on PyQt.

## Verification

- Manifest and loader inspection listed above.
- `python -B tools/check_project_plugin_model.py` must remain green after documentation/guard changes.
- Target architecture tests: `tests/test_suite_registry.py`, `tests/test_plugin_activation.py`, `tests/test_project_plugin_model_gate.py`, and `tests/test_package_index_architecture.py`.

## Follow-on

This clarification closes before implementation resumes. The only active engineering gate remains **Phase E3 — Package transaction operator recovery command surface and interlock decision**.