# Phase E139 -- Versioned Runtime Launcher Plugin-Load Controlled-Exit Cleanup Audit

Date: 2026-07-31
Status: complete

## Audit result

- Direct regressions reach the real `kernel.load_plugins_layered()` seam after Launcher has created and still owns splash. `SystemExit(201)` retains its exact primary object/code, dismisses that splash exactly once, and never reaches `kernel.show()`, `finish_splash()`, or `app.exec()`.
- `KeyboardInterrupt` at the same seam remains deliberately outside `except (Exception, SystemExit)`: it propagates unchanged without controlled splash cleanup or later UI/event-loop work.
- No production correction was warranted. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_plugin_load_controlled_exit.py` (2 cases).
- E139 direct proof: `2 passed in 0.27s`; complete `test_versioned_runtime*.py` composition: `58 passed in 3.65s`, all with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.32s`.
- Scoped `py_compile` passed. The E139 files are UTF-8 without BOM, CRLF-only, and trailing-whitespace-free. `git diff --check` exited 0 with only existing LF/CRLF warnings; unrelated dirty worktree content was preserved. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E140 -- Versioned Runtime Launcher Plugin-Load Cleanup-Failure Primary-Error Audit**. At the same plugin-load controlled-exit seam, make `dismiss_splash()` raise an ordinary exception and prove the original `SystemExit` remains primary while cleanup is warning-observed.
