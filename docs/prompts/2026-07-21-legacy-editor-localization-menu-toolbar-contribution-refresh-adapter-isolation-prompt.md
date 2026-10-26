# Fresh-session prompt — Phase E29 Legacy Editor Localization Menu/Toolbar Contribution Refresh Adapter Isolation

Continue the persistent VitaLoom objective **“彻底完善”** from the completed E28 checkpoint. E28 completion is not whole-engine completion.

## Immutable architecture authority

```text
L0 FrameCore (the only root framework)
└─ L1 lotucosm-vitaloom (the sole engine/product mega-plugin)
   ├─ recursive downstream plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain packages
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

This is a self-developed Unity/Godot-class engine architecture, not a project to migrate into Unity, Godot, Unreal, Electron, or another application shell. The sole L1 engine plugin is itself recursively plugin-shaped and may host engine plugins and Project World addons.

The exact `NestedPluginHost` remains the sole downstream composition/control authority over one `RuntimePluginHost`, `ManualPluginReloadHost`, `ProjectScopedPluginHost`, shutdown, and observation. PyQt6/QPainter/current OpenGL are legacy/current concrete UI Host Adapters only; they do not define the engine root, plugin rules, manifests, lifecycle authority, or future UI-host architecture.

## Previous gate evidence

E28 added deterministic copied `description`/canonical `provides` to Host catalog observation and migrated Package Manager away from `kernel.plugin_loader` and live plugin objects. Both package and individual-plugin disable paths now reject protected plugins, persist via the canonical AI command registry, and request immediate unload only through the exact published Host capability.

Recorded E28 proof: original red `5 failed`; supplementary red `1 failed, 25 passed`; final focused `87 passed, 1 skipped`; expanded `650 passed, 2 skipped, 17 subtests passed`; full non-signature `1309 passed, 25 skipped, 34 subtests passed`; real offscreen Editor smoke `plugins=13/20`; all four guardrails passed. Signature-only collection remains blocked because the repository `.venv` lacks `cryptography`; do not install it unless the user explicitly changes direction.

## E29 single objective

Isolate concrete Localization-driven menu/toolbar contribution refresh inside the existing legacy Editor UI Adapter seam.

Current production debt is in:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/editor_extensions/localization_plugin.py`

Its `_refresh_all_menu_providers()` currently:

- reaches `kernel.plugin_loader.loaded_plugins`;
- identifies live `IMenuProvider` instances;
- calls live `get_plugin_info()`, `get_menu_items()`, and `get_toolbar_items()`;
- directly asks `LayoutManager` to remove and add concrete UI contributions.

This behavior is not declarative plugin catalog observation. It belongs to the concrete legacy Editor Adapter because it operates on live UI providers and LayoutManager. Do **not** expose plugin instances through `observe_plugins()` and do **not** invent a generic UI capability framework in E29.

## Required first actions

1. Read `AGENTS.md`, `CONTEXT.md`, relevant ADRs, `docs/mainline_status.md`, the completed E28 plan, and this prompt.
2. Write an E29 phase plan under `docs/superpowers/plans/` before production changes.
3. Audit `LocalizationPlugin`, `LegacyEditorPluginAdapter`, `PluginLoader` compatibility delegates, LayoutManager contribution ownership, language-change events, startup ordering, reload, and shutdown cleanup.
4. Write genuine red tests proving that Localization no longer needs Loader/live-provider access and that refresh behavior still occurs through the existing Adapter.
5. Then implement the smallest deepening that concentrates live UI contribution refresh in `LegacyEditorPluginAdapter`.

## Required ownership split

### Keep in `LocalizationPlugin`

- locale catalog/data loading;
- `i18n_tr`;
- language selection and persistence;
- `language_changed` event publication;
- invoking a narrow already-existing Editor Adapter refresh seam, if a call is required.

### Move/keep in `LegacyEditorPluginAdapter`

- enumerating live legacy `IMenuProvider` instances;
- deriving the canonical plugin identity needed for UI cleanup;
- `LayoutManager.remove_plugin_ui(...)`;
- menu and toolbar contribution re-addition;
- concrete PyQt/editor ordering, warning, and cleanup behavior.

## Invariants

- Reuse the existing `LegacyEditorPluginAdapter`; do not create another UI Host, Adapter hierarchy, registry, planner, manifest authority, or composition root.
- Keep `PluginLoader` compatibility aliases where external callers still require them, but remove Localization production consumption of Loader mutable registries/live objects.
- Keep the Qt-free L0–L4 engine/plugin Interfaces free of PyQt, Qt objects, live UI-provider objects, and LayoutManager concerns.
- Preserve menu and toolbar ordering, plugin naming, translation refresh, duplicate prevention, startup behavior, reload behavior, and shutdown cleanup.
- Preserve `.pond`, package/project manifests, AI command registry, Inspector binding, SR2D seams, Project World L4 lifecycle, Player/export, reload, and shutdown semantics.
- Do not stage, commit, reset, restore, clean, delete, or rewrite unrelated uncommitted work. Use `.\.venv\python.exe`.

## Explicit non-goals

- selecting or implementing a replacement UI Host;
- broad `PluginLoader` facade deletion;
- a generic menu/toolbar capability framework;
- exposing live plugins through Host observation;
- native acceleration completion;
- real current-context OpenGL default-ready claims;
- signature dependency installation.

## Verification ladder

1. Record genuine E29 red tests.
2. Run focused Localization, LegacyEditorPluginAdapter, menu/toolbar, LayoutManager, Loader compatibility, reload, and language-change tests.
3. Run expanded plugin lifecycle/observation/reload/shutdown/Project World/package/command/Inspector/SR2D/Player/export/startup tests.
4. Run real offscreen Editor smoke.
5. Run the full suite excluding only `tests/test_package_signature_warn_only.py`.
6. Run all four architecture guardrails.
7. Attempt signature-only collection and record the missing-`cryptography` blocker honestly.

## Closure rule

Update the E29 plan, `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`; create exactly one fresh-session prompt naming exactly one next Gate. Do not claim the persistent objective “彻底完善” is complete unless every remaining engine requirement has current build/import, behavior, parity, benchmark, smoke, and guardrail evidence as applicable.
