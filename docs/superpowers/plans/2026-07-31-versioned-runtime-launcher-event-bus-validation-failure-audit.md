# Phase E136 -- Versioned Runtime Launcher Event-Bus Validation Failure Audit

Date: 2026-07-31
Status: complete

## Previous gate

E135 proved that construction of the default L1 capability registry is a no-resource boundary: ordinary failure, controlled `SystemExit`, and `KeyboardInterrupt` preserve their primary object and prevent all later Launcher work without splash cleanup.

## Objective

Audit the immediately following caller-supplied event-bus validation step:

```python
runtime_event_bus = (
    None if event_bus is None else require_runtime_event_bus(event_bus)
)
```

When `require_runtime_event_bus(event_bus)` fails before application event-loop validation or splash allocation, prove exact ordinary/controlled-exit propagation, explicit `KeyboardInterrupt` behavior, no cleanup, and no later UI/Kernel/plugin/event-loop work.

## Audit result

- New direct regressions patch the actual `runtime_event_bus` module object that Launcher dynamically imports. They keep default registry construction successful, then make `require_runtime_event_bus(event_bus)` raise `SystemExit(171)` or an ordinary RuntimeError. Both propagate as the exact primary object before app-loop lookup, splash, Kernel, plugin layers, or `app.exec()`.
- The same seam propagates `KeyboardInterrupt` without classification; no splash exists and `dismiss_splash()` remains forbidden. Call ordering proves registry construction occurs before the validator and no later work starts.
- The first combined run revealed only a regression-harness cache issue: the pre-existing event-bus interface test reloads its module, so package attributes can be stale relative to `sys.modules`. E136 now uses `importlib.import_module()` to patch the current dynamic-import target. The corrected combined suite passes; no production defect or ownership change was found.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_event_bus_validation_failure.py` (3 cases).
- Focused E128--E136/interface slice: `119 passed in 3.61s` with `QT_QPA_PLATFORM=offscreen`.
- Complete `test_versioned_runtime*.py` composition slice: `50 passed in 3.39s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.29s`. The repository `.venv` lacks `cryptography`; no dependency was installed.
- Scoped compilation, UTF-8-no-BOM, CRLF, trailing-whitespace checks, and `git diff --check` are recorded in the mainline status. Existing worktree line-ending warnings and unrelated dirty files remain untouched.

## Next gate

Exactly one next gate: **E137 -- Versioned Runtime Launcher Plugin-Layer Resolution Failure Cleanup Audit**. Audit failures from `default_plugin_layers(normalized_repo_root)` after Launcher has acquired a splash; prove normal/controlled startup errors preserve their primary object while exactly one cleanup occurs, and keep KeyboardInterrupt explicit.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change, or broad L1 event-bus contract redesign without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.