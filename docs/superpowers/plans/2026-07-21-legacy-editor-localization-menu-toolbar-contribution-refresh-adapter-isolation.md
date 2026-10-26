# Phase E29 -- Legacy Editor Localization Menu/Toolbar Contribution Refresh Adapter Isolation

- **Status:** completed
- **Date:** 2026-07-21
- **Previous Gate:** E28 completed deterministic Host-owned catalog metadata projection and removed Package Manager production consumption of Loader registries/live plugin objects.
- **Unique objective:** remove `LocalizationPlugin` production knowledge of `PluginLoader`, `loaded_plugins`, live `IMenuProvider` instances, and `LayoutManager` contribution mechanics by concentrating that concrete behavior in the existing `LegacyEditorPluginAdapter`.

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

This is a self-developed Unity/Godot-class engine architecture, not a migration to another engine or application shell. The exact `NestedPluginHost` remains the sole downstream composition/control authority over one `RuntimePluginHost`, manual reload, Project World addon lifecycle, shutdown, and observation. PyQt6/QPainter/current OpenGL remain legacy/current concrete UI Host Adapters only.

## Previous gate proof

E28 established one deterministic copied catalog metadata locality and migrated Package Manager list/detail/protection/disable/unload to the exact published plugin Host capability plus the canonical AI command registry.

Recorded E28 proof:

- original red: `5 failed in 0.30s`;
- supplementary protected-plugin red: `1 failed, 25 passed in 0.71s`;
- final focused: `87 passed, 1 skipped in 1.30s`;
- expanded cross-domain: `650 passed, 2 skipped, 17 subtests passed in 29.20s`;
- full non-signature: `1309 passed, 25 skipped, 34 subtests passed in 82.84s`;
- real offscreen Editor smoke: `plugins=13/20` with deterministic reverse shutdown;
- all four architecture guardrails passed;
- signature-only collection remained blocked because `.venv` lacks `cryptography`.

## Current E29 audit

`builtin/editor_extensions/localization_plugin.py::_refresh_all_menu_providers()` currently:

1. checks the concrete kernel `layout_manager`;
2. reaches `kernel.plugin_loader`;
3. reads the Loader compatibility `loaded_plugins` mapping;
4. identifies live `IMenuProvider` instances;
5. reads live plugin metadata and menu/toolbar declarations;
6. removes and re-adds contributions directly through `LayoutManager`.

`LegacyEditorPluginAdapter` already owns initial menu/toolbar registration and unload cleanup. The missing depth is one Adapter-owned refresh operation over an exact, injected view of active plugin items. Localization should publish language state/events and invoke only a narrow concrete Editor Host refresh seam.

## Required invariants

- Reuse the existing `LegacyEditorPluginAdapter`; do not create another UI Host, Adapter hierarchy, registry, planner, metadata authority, or composition root.
- Bind the Adapter to the exact `NestedPluginHost.loaded_plugins` state through a narrow resolver; do not expose live plugins through Qt-free `observe_plugins()`.
- Preserve active plugin iteration order and per-provider best-effort failure isolation.
- Preserve canonical plugin identity used by `LayoutManager.remove_plugin_ui`, `add_menu_items`, and `add_toolbar_items`.
- `LocalizationPlugin` retains locale loading, `i18n_tr`, language selection, context injection, and `language_changed` publication.
- Language-change publication must happen before the fallback aggregate menu/toolbar refresh, preserving established behavior.
- `LocalizationPlugin` production source must no longer import/use `IMenuProvider`, `kernel.plugin_loader`, `loaded_plugins`, or direct `LayoutManager` add/remove calls.
- Loader compatibility aliases remain for external callers, but the Adapter resolver must bind to the exact nested Host state rather than treating those aliases as authority.
- Preserve `.pond`, AI command registry, Inspector binding, SR2D, package/project manifests, Project World L4 lifecycle, Player/export, reload, shutdown, and startup semantics.
- Use `.\.venv\python.exe`; do not install `cryptography` or modify unrelated uncommitted work.

## Implementation plan

### Task 1 -- Genuine red tests

Add focused behavior/source tests proving:

- language change publishes `language_changed`, then invokes a narrow legacy Editor Host refresh seam even when the kernel has no Loader or LayoutManager attribute;
- Localization source has no Loader/live-provider/LayoutManager contribution mechanics;
- `LegacyEditorPluginAdapter` refreshes all active `IMenuProvider` contributions from an injected exact active-plugin resolver;
- non-menu plugins are ignored, provider failures do not prevent later providers, and active iteration order is retained;
- the Loader binds that resolver to the exact `NestedPluginHost.loaded_plugins` state;
- the concrete `EditorKernel` exposes only the narrow refresh delegation needed by Localization.

Record actual failing output before production edits.

### Task 2 -- Deepen the existing legacy Editor Adapter

- Add an explicit active-plugin-items resolver binding to `LegacyEditorPluginAdapter`.
- Add one `refresh_menu_providers()` operation that owns live `IMenuProvider` filtering, canonical UI identity, remove/add sequencing, and best-effort error locality.
- Reuse the same menu registration helper where doing so preserves behavior and avoids duplicate mechanics.
- Keep all live object handling in this concrete Adapter.

### Task 3 -- Wire the existing Host and Localization consumer

- After `PluginLoader` constructs the exact `NestedPluginHost`, bind the Adapter resolver directly to the exact Host active mapping.
- Add a narrow concrete `EditorKernel` refresh method delegating to the existing Adapter.
- Replace Localization's Loader/live-object fallback with that narrow Host method, preserving publish-before-refresh ordering.
- Do not add a Qt-free UI capability, generic contribution framework, or Loader fallback.

### Task 4 -- Verification ladder

1. Focused E29 red/green tests.
2. Existing Localization, menu/toolbar, Adapter, Loader, reload, shutdown, and language-change tests.
3. Expanded plugin Host/observation/Project World/package/command/Inspector/SR2D/Player/export/startup tests.
4. Real offscreen Editor smoke.
5. Full suite excluding only `tests/test_package_signature_warn_only.py`.
6. `tools/check_project_plugin_model.py`.
7. `tools/check_core_boundaries.py`.
8. `tools/check_gui_boundaries.py`.
9. `tools/check_release_consistency.py`.
10. Signature-only collection attempt, recording the missing-`cryptography` blocker without installing dependencies.

## Explicit non-goals

- selecting or implementing a replacement UI Host;
- broad `PluginLoader` facade deletion;
- a generic menu/toolbar capability framework;
- exposing live plugin instances through Host observation;
- native acceleration completion;
- real current-context OpenGL default-ready claims;
- signature dependency installation.

## Closure rule

Record actual red/green/expanded/full/smoke/guardrail evidence here. Update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`. Create exactly one fresh-session prompt naming exactly one next Gate. The persistent objective `彻底完善` remains active unless every remaining engine requirement has current evidence.


## Implementation result

- `LegacyEditorPluginAdapter` now owns the active live `IMenuProvider` enumeration and the concrete remove -> add menu -> add toolbar refresh sequence.
- The Adapter receives a tuple snapshot from an injected resolver bound to the exact `NestedPluginHost.loaded_plugins` mapping. Host mapping keys remain the canonical UI contribution identities and Host insertion order is retained.
- Each provider is isolated: one failed provider does not prevent later providers from refreshing.
- `EditorKernel.refresh_legacy_menu_contributions()` is the only narrow concrete legacy UI Host seam consumed by Localization.
- `LocalizationPlugin` still owns locale state and `language_changed` publication, preserves publish-before-refresh ordering, and no longer imports/uses `IMenuProvider`, `kernel.plugin_loader`, `loaded_plugins`, or direct `LayoutManager` contribution calls.
- No second Host, registry, planner, manifest authority, composition root, or UI framework was introduced.

## Verification evidence

- Genuine red before production edits: `6 failed in 0.19s`.
- Initial focused green: `6 passed in 0.12s`; closure recheck on 2026-07-21: `6 passed in 0.11s`.
- Focused Adapter/Localization/shutdown/toolbar/manager/reload/Host group: `51 passed in 0.87s`.
- Expanded legacy Editor/plugin group: `219 passed, 1 skipped in 5.63s`.
- Changed-file `py_compile`: passed for the Adapter, Loader, EditorKernel, Localization, and E29 test Module.
- Full suite excluding only signature: `1315 passed, 25 skipped, 34 subtests passed in 128.21s`.
- Real offscreen Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`, zero discovery errors, deterministic reverse shutdown.
- Guardrails: `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK`.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'`; no dependency was installed and signature verification is not claimed.

## Stable vs unfinished

### Stable after E29

- `FrameCore` remains the sole L0 root framework.
- `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and recursive downstream plugin Host / derived framework.
- `versions/1.0.0/runtime` remains the product runtime boundary carrying L2 capability/domain Modules, L3 engine extensions/Host Adapters, and L4 Project World addons.
- The exact `NestedPluginHost` remains the sole recursive downstream composition/control authority.
- Production runtime has no external `kernel.plugin_loader` consumer. Live legacy menu/toolbar provider refresh is localized to the existing concrete `LegacyEditorPluginAdapter`.
- `.pond`, AI command registry, Inspector binding, SR2D public seams, package/project manifests, Project World lifecycle, Player/export, reload, startup, and shutdown evidence remained green.

### Still unfinished

- `PluginLoader` remains a compatibility facade owned by the current legacy Editor Host; E29 does not remove that facade or select a replacement UI Host.
- PyQt6/QPainter/current OpenGL remain legacy/current concrete UI Host Adapters. No replacement Host parity is claimed.
- SR2D C++/Rust extensions still do not build or import in this environment; native parity and benchmark proof are incomplete.
- OpenGL is not default-ready until real current-context pixels, interaction parity, and benchmark evidence pass.
- Signature verification remains unverified because `.venv` lacks `cryptography`.
- The persistent objective `彻底完善` remains active.

## Next Gate audit and decision

Fresh 2026-07-21 preflight proves that `_vitalloom_sr2d_cpp`, `_vitalloom_sr2d_rust`, and legacy `_vitalloom_sr2d` are not importable. C++ tools `cl/cmake/g++/clang++/nmake`, Rust tools `cargo/maturin`, and native Python build packages are unavailable. The fallback path is the existing mandatory Python SR2D Adapter; the unblock path is an explicitly approved supported native toolchain plus build packages, followed by real build/import/parity/benchmark commands. Tooling/check-only output alone cannot complete native acceleration.

**Unique next Gate: Phase E30 -- SR2D Native Extension Build/Import, Python Parity and Benchmark Evidence.** Build and import at least one real native Adapter behind the existing SR2D seam, prove parity against the Python oracle, benchmark both paths, and retain Python/default policy unless evidence justifies a change. Do not create another framework/plugin Host or change L0-L4 ownership.
