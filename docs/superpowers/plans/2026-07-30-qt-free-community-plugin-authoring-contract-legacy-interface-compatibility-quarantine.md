# Phase E57 -- Qt-Free Community Plugin Authoring Contract and Legacy Interface Compatibility Quarantine

Date: 2026-07-30
Status: completed on 2026-07-30

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. `RuntimePluginHost` remains the Qt-free lifecycle/metadata authority; copied `editor_contributions` remain the portable editor-shell authority; `LegacyEditorPluginAdapter` remains the single concrete PyQt payload bridge. No second Host, registry, callback registry, event bus, widget DSL, renderer, UI framework, app shell, composition root, or peer engine root was introduced.

## Previous Gate

E56 retired obsolete built-in/Adapter `IEditorPlugin` runtime authority. Its final non-signature suite passed (`1654 passed, 34 skipped, 34 subtests passed in 167.33s`), with compileall, four guardrails, and standard/eager Editor smokes (`13/20`, `20/20`) green. Its historical signature-only blocker is preserved as E56 history only: the current E57 environment collects and executes the signature test successfully.

## Completed work

- Migrated all four official `workspace/extensions/community` samples directly to Qt-free `IRuntimePlugin`: service provider/consumer stay headless; Dock and Viewport publish parseable Host-copied `dock_surface` / `viewport_surface` facts while retaining `create_dock_widget()` / `create_viewport_widget()` solely as `LegacyEditorPluginAdapter` PyQt payload seams.
- Repaired two direct-contract omissions exposed by fresh headless validation: `ExampleServiceConsumerPlugin` now supplies required `on_unload()`, and the Dock/Viewport samples import PyQt6 lazily inside their concrete payload factories. They can therefore be discovered and contribute metadata without PyQt6, while calling a factory without PyQt6 raises an explicit runtime error.
- Explicitly labelled `tests/fixtures/workspace/extensions/user/` as a compatibility-only regression surface, not a new-author template. Public `IEditorPlugin`, `IDockProvider`, `IViewportProvider`, and `IThemeProvider` imports remain available; `IEntityTypeProvider` / `IComponentTypeProvider` layering is unchanged.
- Rewrote `workspace/extensions/community/README.md` as the official Qt-free authoring path: direct `IRuntimePlugin`, JSON-safe Host-copied metadata, required `on_load()` work, optional best-effort `on_editor_ready()`, and Adapter-local Qt factories.
- Rewrote the USER_GUIDE theme example and FAQ to use `IRuntimePlugin` plus JSON-safe `theme_profile`. Palette/profile facts remain copied metadata; `get_stylesheet()` is documented only as the concrete Adapter-local QSS payload seam. The historical `IThemeProvider` compatibility import is no longer taught as a new-plugin template.
- Added migration proofs for exact direct bases, absent official legacy UI imports, exact Dock/Viewport contribution parsing, explicit legacy-fixture quarantine, and the new README/theme-guide authoring contract.

## Verification

- Static audit: official community `*_plugin.py` modules have no `plugin_interfaces`, `IEditorPlugin`, `IDockProvider`, `IViewportProvider`, `get_dock_config`, or legacy viewport ID/name reference. Author-doc audit confirms all four community rows name `IRuntimePlugin`, the theme sample names `IRuntimePlugin`/`theme_profile`, and it contains no `IThemeProvider` import; legacy fixture quarantine markers remain present.
- Compile: the four migrated community plugins plus `tests/test_community_example_migration.py` passed `compileall`; after the final lazy-PyQt repair, Dock/Viewport modules and the test module passed `compileall` again.
- Focused behavioral regression before final documentation-only closure: community migration, service registry examples, Dock/Viewport contribution contracts and legacy projections, legacy Adapter, PluginLoader lifecycle/shutdown, and RuntimePluginHost shutdown passed: `66 passed in 3.00s` using an in-repository `--basetemp` after the Windows user-Temp permission issue was isolated as an environment path issue.
- Final author/sample proof after the lazy-PyQt repair: `tests/test_community_example_migration.py` passed `9 passed in 0.81s`; signature-only verification passed `2 passed in 0.29s`.
- Full non-signature regression after the runtime/sample migration: `1640 passed, 50 skipped, 34 subtests passed in 161.41s` using `--ignore=tests/test_package_signature_warn_only.py` and an in-repository `--basetemp`.
- Guardrails: `check_project_plugin_model.py`, `check_core_boundaries.py`, `check_gui_boundaries.py`, and `check_release_consistency.py` all report OK.
- Real offscreen Editor smoke: both standard and eager plugin discovery/load paths pass with zero discovery/load failures, deterministic reverse shutdown, and `plugins=13/20` / `plugins=20/20` respectively.

## Stable and intentionally unfinished

Stable: official community and theme authoring guidance now starts at the existing Qt-free runtime contract; portable editor shell facts remain Host-owned/copied, and concrete PyQt content remains bounded to the one legacy Adapter. Intentionally unfinished: the PyQt6/QPainter/OpenGL editor remains the legacy UI-host adapter with no replacement Host; public legacy interfaces remain compatibility surface; native acceleration and OpenGL default-ready still lack required build/import/parity/benchmark evidence; Project World, SR2D, Player/export, package/signature authority, and broader engine completion are not claimed by E57.

## Fresh audit and unique next Gate

Fresh audit finds no remaining official community example or theme-guide path that recommends a legacy UI interface as the new-author base. The remaining work is to make the continuing public legacy interface surface explicit, bounded, and auditable without removing it or creating a second authority.

**Unique next Gate: Phase E58 -- Legacy Public Plugin Interface Compatibility Contract Audit and Deprecation Documentation.** Audit only public legacy `plugin_interfaces` import/behavior compatibility, document precise supported compatibility expectations and non-authoritative status, and add narrow regression coverage where needed. Preserve existing public imports, entity/component provider layering, Loader/Host/Adapter authority, `.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export, package/signature authority, and the single current UI Adapter. Do not implement a replacement UI Host, registry/event bus, widget DSL, renderer/UI framework, or peer engine root.