# Phase E142 -- Versioned Runtime Launcher No-Splash Plugin-Load Failure Null-Cleanup Audit

Date: 2026-07-31
Status: complete

## Audit result

- Direct regressions reach the actual `kernel.load_plugins_layered()` seam with `use_splash=False` and cover both a primary ordinary `RuntimeError` and `SystemExit(205)`. In each case the exact primary object (and controlled-exit code) remains unchanged.
- No splash show/message/finish operation occurs. Launcher reaches the existing `dismiss_splash(None)` adapter no-op once, then re-raises before Kernel show or application event-loop entry. This does not create UI-host or FrameCore lifecycle authority.
- No production correction was warranted: `dismiss_splash(None)` is intentionally a safe no-op. E139 remains the explicit splash-enabled KeyboardInterrupt proof; the no-splash KeyboardInterrupt boundary is the sole next gate. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_no_splash_plugin_load_failure.py` (2 cases).
- E142 direct proof: `2 passed in 0.22s`; complete `test_versioned_runtime*.py` composition: `62 passed in 3.90s`, with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.20s`.
- Scoped `py_compile` passed. The E142 files are UTF-8 without BOM, CRLF-only, and trailing-whitespace-free. `git diff --check` exited 0 with only existing LF/CRLF warnings; unrelated dirty worktree content was preserved. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E143 -- Versioned Runtime Launcher No-Splash Plugin-Load KeyboardInterrupt Null-Cleanup Audit**. At the same `use_splash=False` seam, prove `KeyboardInterrupt` remains unclassified, does not invoke even the safe null cleanup adapter, and cannot enter Kernel show or the event loop.
