# Phase E132 -- Versioned Runtime Splash-Finish Controlled-Exit Cleanup Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E131 proved every pre-handoff `splash_message()` site retains the Launcher-held splash and E128 cleanup semantics for ordinary failure and controlled `SystemExit`. The only remaining pre-event-loop splash transition was `finish_splash(splash, kernel)`, which invokes the native finish handoff and schedules a deferred deletion callback.

## Objective

Audit controlled `SystemExit` and ordinary failures from `finish_splash()` before the successful handoff is complete. Distinguish failures in native `splash.finish(kernel)` from failures while scheduling the deferred callback; prove exact primary error/exit preservation, one E128 cleanup when handoff did not complete, event-loop exclusion, and unchanged FrameCore L0 ownership.

## Audit result

- New direct regressions exercise `SystemExit(131)` from native `splash.finish(kernel)`, `SystemExit(133)` from `QTimer.singleShot(0, ...)`, and an ordinary native `RuntimeError`. Each preserves the exact primary exception object and exit code, performs exactly one Launcher-owned hide/deferred-delete cleanup, records no successful deferred callback, and never enters `app.exec()`.
- A cleanup-failure regression proves the warning-only E128 cleanup path cannot replace `SystemExit(135)`. `KeyboardInterrupt` deliberately remains outside the controlled-exit classification and bypasses Launcher cleanup.
- The timer-scheduling case is explicitly an incomplete handoff: native `finish()` had returned, but no callback was accepted for deferred ownership. It is therefore not conflated with E129's already-completed-handoff event-loop exits or E105--E111 callback-time behavior.
- No production correction was warranted. E128's existing `except (Exception, SystemExit)` Launcher startup boundary already covers both native-finish and timer-scheduling exits. FrameCore remains Qt-free L0; no QApplication, Kernel, Host, Project World, recovery, or shutdown authority moved. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regressions: `tests/test_versioned_runtime_splash_finish_controlled_exit_cleanup.py` (5 cases).
- Focused E128--E132/interface slice: `94 passed in 2.51s` with `QT_QPA_PLATFORM=offscreen`.
- Versioned runtime composition slice: `42 passed in 3.60s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.24s`. The repository `.venv` lacks `cryptography`; no dependency was installed.
- Scoped `py_compile`, UTF-8-without-BOM, CRLF-only, and trailing-whitespace checks passed for the affected production/test paths. `git diff --check` exited 0 with existing repository LF-to-CRLF warnings only.

## Next gate

Exactly one next gate: **E133 -- Versioned Runtime Launcher Pre-Splash Failure Boundary Audit**. Audit the argument/protocol validation edges before `splash = None` exists; prove ordinary errors and controlled exits preserve their primary failure while creating no splash, Kernel, plugin host, Project World, or event loop.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.