# Phase E135 -- Versioned Runtime Launcher Default-Registry Construction Failure Audit

Date: 2026-07-31
Status: complete

## Previous gate

E134 closed the dynamic import segment before splash allocation. After the imports succeed, Launcher either constructs its default L1 `InMemoryRuntimeCapabilityRegistry()` or validates a caller-supplied registry, then validates an optional event bus and the application event-loop capability.

## Objective

Audit default registry construction failures before any splash resource exists. Prove ordinary failures and controlled `SystemExit` preserve identity/code, prevent later event-bus/app validation and all UI/Kernel/plugin/event-loop work, and leave no cleanup responsibility.

## Audit result

- New direct regressions replace the actual imported `InMemoryRuntimeCapabilityRegistry` class used by `launch_editor()`. Constructor `SystemExit(161)` and ordinary `RuntimeError` propagate as the exact original object before event-bus validation, app-loop protocol lookup, splash allocation, Kernel construction, plugin-layer resolution, or `app.exec()`.
- The same class seam propagates `KeyboardInterrupt` without classification. Because `splash = None` has not yet been assigned and no resource has been acquired, `dismiss_splash()` must not run; the regression explicitly forbids it.
- No production correction was warranted. The existing construction order correctly isolates this no-resource L1 failure boundary. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_default_registry_construction_failure.py` (3 cases).
- Focused E128--E135/interface slice: `107 passed in 3.27s` with `QT_QPA_PLATFORM=offscreen`.
- Complete `test_versioned_runtime*.py` composition slice: `47 passed in 3.30s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.24s`. The repository `.venv` lacks `cryptography`; no dependency was installed.
- Scoped compilation, UTF-8-no-BOM, CRLF, trailing-whitespace checks, and `git diff --check` are recorded in the mainline status. Existing worktree line-ending warnings and unrelated dirty files remain untouched.

## Next gate

Exactly one next gate: **E136 -- Versioned Runtime Launcher Event-Bus Validation Failure Audit**. Audit the `require_runtime_event_bus(event_bus)` boundary after registry construction and before app-loop/splash allocation; prove ordinary, controlled-exit, and KeyboardInterrupt behavior with no cleanup or later startup effects.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change, or replacement of the L1 registry/event-bus contract without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.