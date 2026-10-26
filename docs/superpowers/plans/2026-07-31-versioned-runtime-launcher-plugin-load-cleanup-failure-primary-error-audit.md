# Phase E140 -- Versioned Runtime Launcher Plugin-Load Cleanup-Failure Primary-Error Audit

Date: 2026-07-31
Status: complete

## Audit result

- A direct regression reaches the actual `kernel.load_plugins_layered()` controlled-exit seam after successful Launcher splash creation and Kernel construction, then makes Launcher-owned `dismiss_splash()` raise a distinct ordinary `RuntimeError`. The exact primary `SystemExit(203)` object/code remains unchanged.
- The cleanup is attempted once with the Launcher-held splash, its ordinary error is logged as a warning, and no later `kernel.show()`, `finish_splash()`, or `app.exec()` work begins. E139 remains the explicit proof that `KeyboardInterrupt` is outside this controlled-cleanup policy.
- No production correction was warranted: Launcher already catches ordinary `Exception` only around `dismiss_splash()`, retaining primary startup error precedence without swallowing `KeyboardInterrupt` or unrelated `BaseException`. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_plugin_load_cleanup_failure.py` (1 case).
- E140 direct proof: `1 passed in 0.33s`; complete `test_versioned_runtime*.py` composition: `59 passed in 3.21s`, with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.17s`.
- Scoped `py_compile` passed. The E140 files are UTF-8 without BOM, CRLF-only, and trailing-whitespace-free. `git diff --check` exited 0 with only existing LF/CRLF warnings; unrelated dirty worktree content was preserved. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E141 -- Versioned Runtime Launcher Plugin-Load Ordinary-Failure Cleanup-Failure Audit**. At the same direct seam, make plugin load raise an ordinary `RuntimeError` while `dismiss_splash()` also fails ordinarily; prove the original ordinary failure object remains primary and cleanup remains warning-observed.
