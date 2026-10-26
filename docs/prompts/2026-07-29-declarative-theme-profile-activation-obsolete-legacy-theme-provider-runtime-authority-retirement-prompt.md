# Phase E54 Historical Closure -- Declarative Theme Profile Activation and Obsolete Legacy Theme Provider Runtime Authority Retirement

Date: 2026-07-29
Status: completed

E54 is closed. Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, the E54 plan, and `tests/test_theme_profile_runtime_authority_lifecycle.py` when auditing this historical checkpoint; do not reopen it merely to change viewport behavior.

The sole recursive architecture remains unchanged: `FrameCore` is L0; `lotucosm-vitaloom` is the sole L1 engine/product mega-plugin and downstream Plugin Host/derived framework; `versions/1.0.0/runtime` is the product boundary. `LegacyEditorPluginAdapter` remains the one current PyQt Host Adapter.

Completed truth: `UnityDarkThemePlugin` no longer imports or inherits `IThemeProvider`; it implements `IRuntimePlugin` and publishes immutable Host-copied `theme_profile` facts as its only built-in identity/configuration authority. The Adapter consumes `get_stylesheet()` only as a current-PyQt payload factory. Built-in activation no longer type-gates on `IThemeProvider`; the only legacy path is bounded community duck typing for a plugin declaring `theme` with callable `get_theme_name()` and `get_stylesheet()`.

Evidence: E54 lifecycle authority tests `5 passed in 0.23s`; expanded protection `175 passed, 1 skipped in 3.34s`; complete non-signature suite `1641 passed, 34 skipped, 34 subtests passed in 169.63s`; modified-file compileall and all four architecture guardrails pass; standard/eager real offscreen Editor smoke pass at `plugins=13/20` and `plugins=20/20`, with zero discovery/load failures and deterministic reverse shutdown. Signature-only collection remains blocked by `.venv` lacking `cryptography` (`ModuleNotFoundError`, `1 error in 0.29s`, exit code `2`); no dependency was installed and signature verification is not claimed.

E54 did not migrate viewport providers, create a style/widget DSL or another Registry, select a replacement UI Host, alter `.pond`, Project World, commands, Inspector, SR2D, native/OpenGL, package, Player/export, or claim the engine complete.

The unique next Gate is E55: retire only the obsolete built-in `IViewportProvider` authority for the already-declarative CellEditor, GameViewport, and SceneViewport shells. Keep concrete widget factories Adapter-local, preserve community fallback and all current viewport semantics, and use the separately prepared E55 plan/prompt before editing.