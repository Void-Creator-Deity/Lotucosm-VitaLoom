# Phase E55 Historical Closure -- Declarative Viewport Surface Activation and Obsolete Legacy Viewport Provider Runtime Authority Retirement

Date: 2026-07-29
Status: completed

E55 is closed. Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, the E55 plan, `tests/test_viewport_surface_runtime_authority_lifecycle.py`, and the three viewport lifecycle suites when auditing this historical checkpoint; do not reopen it merely to change Editor-ready callback delivery.

The three built-in viewport shells (`CellEditorPlugin`, `GameViewportPlugin`, and `SceneViewportPlugin`) directly implement `IRuntimePlugin`; their copied `viewport_surface` facts are their sole built-in shell identity/configuration authority. `create_viewport_widget()` remains an Adapter-local concrete PyQt payload. `LegacyEditorPluginAdapter` no longer imports or gates built-ins through `IViewportProvider`, and `LayoutManager` remains the only concrete viewport registry/projection/removal authority. A bounded duck-typed community fallback remains only for declared viewport providers with callable `get_viewport_id()` and `create_viewport_widget()`.

A real eager smoke found and the Gate repaired a discovery regression: removing the old inherited provider base had made the three plugin classes invisible to `RuntimePluginHost._plugin_classes()`. Explicit `IRuntimePlugin` inheritance restores the existing Qt-free Host discovery contract without restoring `IViewportProvider`; source guards cover both facts.

Evidence: post-repair focused suite `45 passed in 0.82s`; expanded protection `126 passed in 3.89s`; final complete non-signature suite `1649 passed, 34 skipped, 34 subtests passed in 148.85s`; modified-file compileall and all four architecture guardrails pass; standard/eager real offscreen Editor smoke pass at `13/20` and `20/20`, with zero discovery errors and deterministic reverse cleanup. Signature-only collection remains blocked because `.venv` lacks `cryptography` (`ModuleNotFoundError`, `1 error in 0.37s`, exit code `2`); no dependency was installed and signature verification is not claimed.

E55 did not redesign viewport content, alter `.pond`, Project World, Inspector commands, SR/PS, Player/export, native/OpenGL, signature authority, public legacy interfaces, or create another Host/Registry/UI framework. The unique next Gate is E56: `docs/superpowers/plans/2026-07-29-capability-based-editor-ready-delivery-obsolete-legacy-editor-plugin-runtime-authority-retirement.md`.
