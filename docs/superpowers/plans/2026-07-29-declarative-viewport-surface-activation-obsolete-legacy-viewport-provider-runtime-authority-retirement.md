# Phase E55 -- Declarative Viewport Surface Activation and Obsolete Legacy Viewport Provider Runtime Authority Retirement

Date: 2026-07-29
Status: completed on 2026-07-29

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. Reuse the existing `RuntimePluginHost`, copied `EditorViewportSurfaceContribution` facts, `LegacyEditorPluginAdapter`, and `LayoutManager`. Do not create a second Host, Viewport Registry/catalog, renderer, widget DSL, UI framework, app shell, composition root, or peer engine root.

## Previous Gate

E54 retired the obsolete Unity Dark `IThemeProvider` runtime authority. Its focused authority tests pass (`5 passed in 0.23s`), expanded protections pass (`175 passed, 1 skipped in 3.34s`), and the complete non-signature suite is green (`1641 passed, 34 skipped, 34 subtests passed in 169.63s`). Compileall, four guardrails, and standard/eager Editor smokes pass. Signature-only collection remains blocked because `.venv` lacks `cryptography` (`1 error in 0.29s`, exit code `2`).

## Audited current truth

- `CellEditorPlugin`, `GameViewportPlugin`, and `SceneViewportPlugin` already each publish an immutable Host-copied `viewport_surface` contribution.
- All three still import/inherit `IViewportProvider`; `LegacyEditorPluginAdapter` still uses that Interface as a type gate for legacy viewport activation and cleanup.
- `create_viewport_widget()` is current concrete PyQt content payload and must remain Adapter-local. The Qt-free contribution carries only viewport shell identity/name/order/refresh facts.
- `LayoutManager` is the one concrete viewport Registry/projection-deletion authority. Existing lifecycle and content behavior is substantial: CellEditor enter/exit flows; GameViewport SR Host, selected identity, simulation transport, input/render/playback; SceneViewport `.pond`, scene/entity/script/component/sprite/hierarchy flows.
- Unmigrated community `IViewportProvider` plugins require bounded compatibility, but must not remain built-in runtime authority.

## Tasks

### Task 1 -- Executable red viewport-authority contract

1. Prove an `IRuntimePlugin` that declares `viewport_surface` activates, projects, localizes, unloads, and restores exact LayoutManager/Host state without inheriting `IViewportProvider`.
2. Prove absent, non-callable, invalid, or exception-raising concrete widget factories fail explicitly and roll back Host publication, commands, contribution refresh subscriptions, projected viewport ownership, and UI/layout state.
3. Preserve collision-before-mutation, exact in-place localization refresh, retained-widget semantics, failure retry, reload, deterministic reverse shutdown, and bounded legacy/community fallback.

### Task 2 -- Retire obsolete built-in viewport Provider authority

1. Make copied `viewport_surface` facts the only built-in CellEditor/GameViewport/SceneViewport shell identity/configuration and activation/cleanup authority.
2. Keep `create_viewport_widget()` only as `LegacyEditorPluginAdapter`'s concrete current-PyQt payload factory; do not copy widgets, factories, callbacks, layout/kernel/renderer objects, or live viewport state into Host metadata.
3. Remove the three built-in `IViewportProvider` imports/inheritance and remove Adapter built-in type-gating only after all lifecycle parity holds.
4. Retain a minimal explicit community fallback for legacy getters/factory behavior without making it a second built-in authority.

### Task 3 -- Verification and closure

1. Run the new authority contract plus existing CellEditor/GameViewport/Scene viewport lifecycle, LayoutManager, Host activation/unload/reload/shutdown, command, localization, Project World, `.pond`, SR/PS, Inspector, package, Dock/theme, and community compatibility protections.
2. Run complete non-signature regression, modified-module `compileall`, all four guardrails, and standard/eager real offscreen Editor smoke.
3. Run signature-only collection and record the exact environment blocker without installing dependencies.
4. Update this plan, its fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, relevant contribution documentation, and `docs/INDEX.md`; name exactly one next Gate only after a fresh post-E55 audit.

## Completion boundary

E55 may retire only obsolete built-in viewport-provider runtime authority for the three already-declarative viewport shells. It does not redesign concrete CellEditor/GameViewport/SceneViewport content, alter `LayoutManager` Registry authority, change `.pond`, Project World, commands, Inspector, SR/PS, Player/export, native/OpenGL, signature authorities, select a replacement Host, or complete the editor/engine.
## Completion record

- Built-in viewport shell authority now comes exclusively from immutable Host-copied `EditorViewportSurfaceContribution` facts. `CellEditorPlugin`, `GameViewportPlugin`, and `SceneViewportPlugin` directly implement the Qt-free `IRuntimePlugin` lifecycle contract; none imports or inherits `IViewportProvider`.
- `LegacyEditorPluginAdapter` no longer imports, annotates, or type-gates viewport activation/cleanup through `IViewportProvider`. For a declarative viewport contribution it validates and invokes only the Adapter-local concrete `create_viewport_widget()` payload factory, while `LayoutManager` remains the sole concrete viewport registry/projection/removal authority. No QWidget, factory, callback, layout, kernel, renderer, or live state entered Host metadata.
- A real eager-Editor smoke exposed that the three plugins had silently disappeared from `RuntimePluginHost` discovery after their old inherited base was removed. The repair explicitly made all three subclasses of `IRuntimePlugin`; it restores the existing Qt-free discovery/lifecycle contract without restoring any legacy viewport-provider authority. Source guards now cover both the absence of `IViewportProvider` and the required `IRuntimePlugin` discovery base.
- Compatibility is deliberately narrow: an unmigrated community plugin declaring `provides: ["viewport"]` may use the legacy getter/factory shape only when both `get_viewport_id()` and `create_viewport_widget()` are callable. Built-ins do not use that fallback. `get_viewport_id()` remains temporarily for historical lifecycle tests and the bounded fallback, not built-in shell authority.

### Verification evidence

- Focused post-repair lifecycle/projection suite: `45 passed in 0.82s`.
- Earlier expanded protection selection: `126 passed in 3.89s`.
- Final complete non-signature suite, after the discovery repair: `1649 passed, 34 skipped, 34 subtests passed in 148.85s`.
- Modified-module `compileall` and all four architecture guardrails pass: project plugin model, core boundaries, GUI boundaries, and release consistency.
- Real offscreen Editor smoke passes in standard mode at `plugins=13/20` and in eager mode at `plugins=20/20`, each with zero discovery errors. Eager evidence creates and reverse-removes `cell_editor`, `game`, and `scene`; standard evidence creates/removes the enabled `game` and `scene` surfaces.
- Signature-only collection is an environmental blocker, not a green claim: `tests/test_package_signature_warn_only.py --collect-only` stops with `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.37s`, exit code `2`). No dependency was installed.

### Stable and intentionally unfinished

The declarative viewport boundary, Host discovery base, concrete Adapter payload boundary, LayoutManager authority, lifecycle rollback, reload/shutdown, `.pond`, Project World, Inspector commands, SR/PS behavior, package manifests, native/OpenGL, and signature authority remain as before. This Gate does not remove public legacy interfaces, redesign viewport content, select another UI Host, or claim default-ready OpenGL or whole-engine completion.

### Fresh post-E55 audit and unique next Gate

The audit finds no remaining concrete built-in subclasses of `IDockProvider`, `IViewportProvider`, or `IThemeProvider`; their Adapter paths are already declarative-first with bounded community fallback. The remaining live legacy UI-interface authority is `IEditorPlugin`: `LegacyEditorPluginAdapter.after_plugin_load()` still uses `isinstance(plugin, IEditorPlugin)` to decide delivery of `on_editor_ready()`, and four built-ins (`EditorWorkflowPlugin`, `LocalizationPlugin`, `HotReloadPlugin`, and `StandardUIPlugin`) still inherit it despite the Host's Qt-free `IRuntimePlugin` lifecycle being authoritative. The unique next Gate is E56: capability-based Editor-ready delivery and retirement of obsolete built-in `IEditorPlugin` runtime authority, while preserving the public compatibility import path and existing editor-ready behavior.
