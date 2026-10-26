# Phase E56 -- Capability-Based Editor-Ready Delivery and Obsolete Legacy Editor Plugin Runtime Authority Retirement

Date: 2026-07-29
Status: completed on 2026-07-30

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. `RuntimePluginHost` remains the Qt-free lifecycle and contribution authority. `LegacyEditorPluginAdapter` remains the single concrete PyQt UI-host adapter. Do not create a second Host, callback registry, event bus, widget DSL, renderer, UI framework, composition root, or peer engine root.

## Previous Gate

E55 retired obsolete built-in `IViewportProvider` runtime authority. Its final complete non-signature suite passed (`1649 passed, 34 skipped, 34 subtests passed in 148.85s`); modified-module compilation, all four guardrails, and standard/eager real Editor smokes (`13/20`, `20/20`) passed. Signature-only collection remained blocked by missing `cryptography`.

## Audited current truth

- Before this Gate, `LegacyEditorPluginAdapter.after_plugin_load()` used `isinstance(plugin, IEditorPlugin)` to decide whether to deliver `on_editor_ready()`.
- The Qt-free Host already owns lifecycle and copied contribution contracts. The old interface only supplied this Adapter-local type gate.
- `EditorWorkflowPlugin`, `LocalizationPlugin`, `HotReloadPlugin`, and `StandardUIPlugin` were still concrete `IEditorPlugin` subclasses even though their lifecycle contract is `IRuntimePlugin` plus `ICommandProvider` where applicable.
- `IEditorPlugin`, `IDockProvider`, `IViewportProvider`, `IThemeProvider`, `IEntityTypeProvider`, and `IComponentTypeProvider` remain public legacy/community compatibility surfaces. Their import paths and the entity/component inheritance layering are not in scope for removal.

## Completed work

1. Retired the Adapter import and `IEditorPlugin` runtime type gate. After existing contribution projection and before the existing `plugin_loaded` signal, the Adapter now performs only a bounded local callable lookup for `on_editor_ready()`.
2. Kept absent and non-callable callbacks as no-ops. A raising callback is logged best-effort and cannot mutate or abort the authoritative Host activation lifecycle.
3. Made the four built-ins direct Qt-free `IRuntimePlugin` subclasses while retaining `ICommandProvider` where already required.
4. Added executable lifecycle/source guards for direct `IRuntimePlugin` callbacks, missing/non-callable/raising callbacks, Adapter authority, and the four built-in declarations.
5. Corrected adjacent legacy assertions so a missing optional hook may be looked up once without changing activation, signaling, unload, or shutdown behavior.
6. Updated contributor, user, and built-in troubleshooting documentation: new plugins use `IRuntimePlugin`; `IEditorPlugin` is a compatibility import; `on_editor_ready()` is an optional Adapter-local best-effort notification and never a required initialization contract.

## Verification record

- Focused capability lifecycle coverage: `44 passed in 1.42s`.
- Adapter and runtime-contract directed regression: `18 passed in 0.62s`.
- Expanded non-signature protection set: `175 passed, 14 skipped in 4.12s`.
- Final complete non-signature suite:
  ```text
  1654 passed, 34 skipped, 34 subtests passed in 167.33s
  ```
- Modified modules and relevant tests passed `compileall`; all four guardrails passed: project plugin model, core boundaries, GUI boundaries, and release consistency.
- Real offscreen Editor smoke passed in standard mode at `plugins=13/20` and eager mode at `plugins=20/20`. The four migrated built-ins were discovered, loaded, and reverse-unloaded without discovery/load errors.
- Signature-only collection is an environment blocker, not a green claim: `tests/test_package_signature_warn_only.py --collect-only` stops with `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.36s`). No dependency was installed and signature verification is not claimed.

## Stable and intentionally unfinished

This Gate does not remove public legacy interfaces, redesign Editor-ready semantics, add portable callback metadata, change Host contribution authority, alter `.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export, native/OpenGL, package/signature authority, select a replacement UI Host, or claim editor/engine completion.

## Fresh post-E56 audit and unique next Gate

Runtime source now has no `IEditorPlugin` import, concrete built-in subclass, or `isinstance`/`issubclass` gate outside `kernel/plugin_interfaces.py`'s public compatibility definitions. No concrete built-in `IDockProvider`, `IViewportProvider`, or `IThemeProvider` subclasses remain. The remaining migration debt is author-facing: official community samples and the Dock/Viewport sections of the author guide still teach legacy interfaces as the normal creation path, while test fixtures must keep an explicit legacy-compatibility surface.

The unique next Gate is E57 -- Qt-Free Community Plugin Authoring Contract and Legacy Interface Compatibility Quarantine. It will move new official authoring examples to direct `IRuntimePlugin` and Host-copied contribution contracts while retaining explicit, tested legacy compatibility imports and fixtures.
