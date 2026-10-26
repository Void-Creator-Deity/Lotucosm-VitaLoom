# Phase E141 -- Versioned Runtime Launcher Plugin-Load Ordinary-Failure Cleanup-Failure Audit

Date: 2026-07-31
Status: complete

## Audit result

- A direct regression reaches the actual `kernel.load_plugins_layered()` seam after Launcher has created splash and constructed Kernel, then raises a chosen primary `RuntimeError` while Launcher-owned `dismiss_splash()` raises a distinct ordinary `RuntimeError`. The original plugin-load exception object remains primary.
- Cleanup is attempted exactly once with the owned splash and its exception is warning-observed; no `kernel.show()`, `finish_splash()`, or `app.exec()` call occurs. E139 remains the explicit direct proof that `KeyboardInterrupt` is outside the controlled-cleanup policy.
- No production correction was warranted. Launcher already limits secondary cleanup handling to ordinary `Exception`, which preserves ordinary primary errors as well as the E140 controlled-exit case without swallowing `KeyboardInterrupt` or unrelated `BaseException`. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_plugin_load_ordinary_failure_cleanup_failure.py` (1 case).
- E141 direct proof: `1 passed in 0.34s`; complete `test_versioned_runtime*.py` composition: `60 passed in 4.16s`, with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.16s`.
- Scoped `py_compile` passed. The E141 files are UTF-8 without BOM, CRLF-only, and trailing-whitespace-free. `git diff --check` exited 0 with only existing LF/CRLF warnings; unrelated dirty worktree content was preserved. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E142 -- Versioned Runtime Launcher No-Splash Plugin-Load Failure Null-Cleanup Audit**. With `use_splash=False`, audit ordinary and controlled plugin-load failure paths through the existing `dismiss_splash(None)` no-op handoff, retaining primary exception behavior without inventing UI ownership.
