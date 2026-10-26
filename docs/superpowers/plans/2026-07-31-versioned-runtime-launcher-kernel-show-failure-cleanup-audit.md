# Phase E138 -- Versioned Runtime Launcher Kernel-Show Failure Cleanup Audit

Date: 2026-07-31
Status: complete

## Audit result

- Direct regressions drive successful splash, Kernel construction, layer resolution, and plugin loading to the actual `kernel.show()` seam. Ordinary RuntimeError and `SystemExit(191)` retain their exact primary object/code, dismiss the Launcher-held splash exactly once, and never enter `finish_splash()` or `app.exec()`.
- `KeyboardInterrupt` remains deliberately outside the `except (Exception, SystemExit)` cleanup policy and propagates without splash cleanup.
- No production correction was warranted. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_kernel_show_failure.py` (3 cases).
- Complete `test_versioned_runtime*.py` composition: `56 passed in 4.34s` with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; four guards `OK`; Anaconda signature `2 passed in 0.27s`. `.venv` lacks cryptography; no dependency was installed.

## Next gate

Exactly one next gate: **E139 -- Versioned Runtime Launcher Plugin-Load Controlled-Exit Cleanup Audit**. Audit SystemExit from `kernel.load_plugins_layered()` while Launcher owns splash.