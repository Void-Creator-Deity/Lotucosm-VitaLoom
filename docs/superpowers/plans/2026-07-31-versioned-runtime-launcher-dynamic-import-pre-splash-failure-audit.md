# Phase E134 -- Versioned Runtime Launcher Dynamic-Import Pre-Splash Failure Audit

Date: 2026-07-31
Status: complete

## Previous gate

E133 established that public path/service/application validation executes before any Launcher-owned splash exists. The remaining pre-allocation segment imports the L1 registry, event bus, Kernel, and splash adapter modules after normalization but before `splash = None` is assigned.

## Objective

Audit ordinary exceptions, controlled `SystemExit`, and `KeyboardInterrupt` originating while Launcher imports its version-runtime dependencies. Prove exact primary propagation and absence of splash, Kernel, plugin-layer, Project World, or application event-loop work. Keep no-resource import failures distinct from E128--E132 cleanup states.

## Audit result

- New direct regressions intercept the first actual dynamic edge, `core.VitaLoom.core.runtime_capability_registry`, during `launch_editor()`. Its `SystemExit(151)` and ordinary RuntimeError propagate as the exact original object; no later import is attempted.
- The same direct edge propagates `KeyboardInterrupt` without classification. Kernel construction, splash presentation/dismissal, plugin-layer resolution, and `app.exec()` are all forbidden by the regression and are not reached.
- No production correction was warranted: dynamic imports occur before `splash = None` and before any resource is acquired. E128--E132 cleanup ownership must not be widened to this no-resource segment. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regressions: `tests/test_versioned_runtime_launcher_dynamic_import_pre_splash_failure.py` (3 cases).
- Focused E128--E134/interface slice: `104 passed in 2.42s` with `QT_QPA_PLATFORM=offscreen`.
- Versioned runtime composition slice: `52 passed in 3.94s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.20s`. The repository `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E135 -- Versioned Runtime Launcher Default-Registry Construction Failure Audit**. Audit default `InMemoryRuntimeCapabilityRegistry()` construction after dynamic imports but before app validation/splash allocation; prove ordinary and controlled failures preserve their primary error without UI/kernel/event-loop or cleanup side effects.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change, or broad import-system redesign without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.