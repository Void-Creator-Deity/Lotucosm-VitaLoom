# Phase E28 -- Qt-free Plugin Catalog Metadata Projection and Legacy PackageManager Consumer Decoupling

- **Status:** completed
- **Date:** 2026-07-21
- **Previous Gate:** E27 completed ProjectManager Project World lifecycle routing through the exact published recursive plugin Host capability.
- **Unique objective:** remove Package Manager production reads/control through live `kernel.plugin_loader` and live plugin objects without creating another Host, registry, planner, metadata authority, or composition root.

## Architecture truth

```text
L0 FrameCore (only root framework)
└─ L1 lotucosm-vitaloom (only engine/product mega-plugin)
   ├─ recursive downstream plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain packages
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

The exact `NestedPluginHost` remains the sole composition/control authority. `ProjectScopedPluginHost` remains the sole L4 lifecycle authority. PyQt6/QPainter/current OpenGL remain legacy/current UI Host Adapters and do not define engine or downstream plugin rules.

## Previous gate proof

E27 replaced direct `ProjectManager -> kernel.plugin_loader` L4 scan/sync access with `resolve_plugin_host(editor_context)`. Open ordering, close flush/teardown ordering, fail-closed retention, manifests, reports, and the single L4 authority were preserved.

Recorded proof:

- focused migration tests: `4 passed`, then `70 passed` and `38 passed` related suites;
- cross-domain regression: `391 passed, 2 skipped, 17 subtests passed`;
- final non-signature suite: `1302 passed, 25 skipped, 34 subtests passed in 127.29s`;
- real offscreen Editor smoke: `plugins=13/20`, zero discovery/load failures, deterministic shutdown;
- all four architecture guardrails passed;
- signature-only collection remains blocked because the repository `.venv` lacks `cryptography`.

## Current E28 audit target

`builtin/editor_extensions/package_manager_plugin.py` still has these legacy accesses:

1. `_populate_plugin_list_tab()` reads active IDs from `kernel.plugin_loader.loaded_plugins`.
2. `_render_plugin_detail()` calls `get_plugin_info()` on a live plugin instance.
3. `_disable_selected()` asks the Loader facade for protection facts.
4. `_disable_selected()` calls Loader `unload_plugin()` for immediate session teardown.

The shared `PluginRuntimeOpsMixin` already routes selected-plugin reload/unload/protection/project sync through the exact capability; E28 must reuse that seam rather than duplicate it.

## Required invariants

- Reuse `resolve_plugin_host(...)`, `observe_plugins()`, `unload_plugin()`, and the canonical AI command registry.
- Observation output is deterministic, sorted, JSON-safe, fresh-copy, and mutation-isolated.
- Display metadata may include only copied declarative facts needed by Package Manager (for example name, author, description, dependencies, provides, activation context).
- Never expose plugin instances, bound methods, Qt objects, Host-owned mutable mappings, another registry, or another catalog authority.
- Project-persistent enable/disable remains owned by the canonical AI command registry.
- Immediate session unload remains validated by the exact recursive plugin Host.
- Protected plugins cannot be disabled or unloaded through Package Manager.
- `.pond`, package/project manifests, Inspector command binding, SR2D, Project World lifecycle, reload/shutdown, Player/export, and startup behavior remain unchanged.
- Loader compatibility aliases remain available for external callers; E28 removes only targeted Package Manager production consumption.
- Localization/menu/toolbar provider refresh remains a later concrete legacy Editor Adapter Gate.

## Implementation plan

### Task 1 -- Genuine red tests

Add focused tests that prove the current code is wrong before production edits:

- Package Manager list uses capability observation active IDs with a kernel that has no Loader.
- Detail rendering uses copied observation metadata and never calls a live plugin object.
- Package disable derives protection from observation rows and invokes canonical project commands only for unprotected IDs.
- Successful disable requests immediate unload through the exact capability, not Loader.
- Source guard forbids `kernel.plugin_loader`, `.loaded_plugins`, and live `get_plugin_info()` consumption in Package Manager.
- Observation metadata is JSON-safe, sorted/fresh, and isolated from source plugin metadata mutation.

Record the actual failing count/output before implementation.

### Task 2 -- Deepen the existing observation Module

If Package Manager detail needs facts absent from `PluginHostCatalogEntry`, extend the existing Host-owned catalog projection at the exact runtime Host seam. Prefer enriching the canonical catalog entry during validated discovery/load rather than re-reading live plugin objects during observation. Keep the Interface small and declarative.

### Task 3 -- Migrate Package Manager

- Resolve one observation snapshot for list/detail/protection operations.
- Use snapshot `active_plugin_ids`/catalog rows for state and detail.
- Preserve package index as package-to-plugin association authority.
- Keep persistent commands on the AI command registry.
- Route immediate unload through `resolve_plugin_host(...).unload_plugin()` and handle non-settled reports truthfully.
- Do not add Loader fallback for tests or production.

### Task 4 -- Verification ladder

1. Focused observation + Package Manager red/green tests.
2. Expanded plugin lifecycle/reload/shutdown/Project World/package/command/Inspector/SR2D/Player/export/startup tests.
3. Real offscreen Editor smoke.
4. Full suite excluding only `tests/test_package_signature_warn_only.py`.
5. `tools/check_project_plugin_model.py`.
6. `tools/check_core_boundaries.py`.
7. `tools/check_gui_boundaries.py`.
8. `tools/check_release_consistency.py`.
9. Signature-only collection attempt, recording the `cryptography` blocker without installing dependencies.

## Explicit non-goals

- Localization live menu/toolbar contribution migration.
- Broad deletion of the `PluginLoader` compatibility facade.
- Replacement UI Host selection or parity claim.
- Native acceleration completion.
- Real current-context OpenGL default-ready claim.
- Signature dependency installation.

## Closure rule

Record actual red/green/expanded/full/smoke/guardrail evidence here. Update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`. Create exactly one fresh-session prompt naming exactly one next Gate. The persistent objective `彻底完善` remains active unless every remaining engine requirement has current evidence.

## Completion evidence

- Original Package Manager/Host red baseline: `5 failed in 0.30s`.
- Supplementary single-plugin protection red proof: `1 failed, 25 passed in 0.71s`; the failure showed that the old individual-selection path still sent `plugin.disable` to a protected plugin.
- Focused production fix green: `26 passed in 0.50s`.
- Final focused Package Manager/Host/lifecycle/reload/Project World coverage: `87 passed, 1 skipped in 1.30s`.
- Expanded cross-domain plugin, Project World, package, command, Inspector, SR2D, Player/export, startup, Editor/runtime coverage: `650 passed, 2 skipped, 17 subtests passed in 29.20s`.
- Real offscreen Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`; zero discovery/load failures and deterministic reverse shutdown.
- Full repository suite excluding only the signature module: `1309 passed, 25 skipped, 34 subtests passed in 82.84s`.
- Architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'`; no dependency was installed and signature verification is not claimed complete.

## Stable vs unfinished

### Stable at E28 closure

- The sole L1 `lotucosm-vitaloom` engine plugin remains a recursive downstream plugin Host/derived framework inside the sole L0 `FrameCore` root. No second Host, registry, planner, manifest authority, composition root, or UI framework was introduced.
- `PluginHostCatalogEntry` now owns deterministic copied `description` and canonical `provides` metadata. Registration, observation, manual reload replacement, and L4 embedded-addon clearing share one normalization/locality path.
- String, mapping, scalar, and sequence `provides` values project to deterministic JSON-safe tuples/lists; a scalar string such as `"dock"` is not split into characters.
- Package Manager list, detail, protection, persistent disable, and immediate unload now consume the exact published plugin Host capability plus the canonical AI command registry. Production code no longer reads Loader registries or live plugin objects.
- Both package-selection and individual-plugin-selection disable paths reject protected plugins and unload only through the exact Host after a successful canonical persistent command.

### Still unfinished

- `LocalizationPlugin._refresh_all_menu_providers()` still enumerates `kernel.plugin_loader.loaded_plugins` and calls live `IMenuProvider` objects. This is concrete legacy Editor UI contribution behavior and must move behind the existing `LegacyEditorPluginAdapter` seam, not into the Qt-free Host observation Interface.
- The legacy PyQt6/QPainter/current OpenGL UI Host has not been replaced and no replacement Host parity has been proved.
- Native acceleration is not complete until build/import, parity, and benchmark evidence exists.
- OpenGL is not default-ready until a real current-context canvas renders pixels and passes parity, interaction smoke, and benchmark checks.
- Signature verification remains environment-blocked by missing `cryptography`.
- Therefore the persistent objective `彻底完善` remains active.

## Unique next Gate

**Phase E29 — Legacy Editor Localization Menu/Toolbar Contribution Refresh Adapter Isolation.** First write the E29 plan and genuine red tests. Keep locale data, `i18n_tr`, language selection, and `language_changed` in `LocalizationPlugin`; move live `IMenuProvider` enumeration and `LayoutManager` remove/add refresh behavior into the existing `LegacyEditorPluginAdapter`. Do not expose plugin instances through `observe_plugins()`, invent a generic UI capability framework, or create another Host/registry/composition authority.
