# Phase E143 -- Versioned Runtime Launcher No-Splash Plugin-Load KeyboardInterrupt Null-Cleanup Audit

Date: 2026-07-31
Status: complete

## Audit result

- A direct `use_splash=False` regression reaches the actual `kernel.load_plugins_layered()` seam and raises one retained `KeyboardInterrupt` object. It propagates by identity exactly as intended.
- Because `KeyboardInterrupt` is outside Launcher's `except (Exception, SystemExit)` boundary, no splash show/message/finish operation or even `dismiss_splash(None)` call occurs. Kernel show and application event-loop entry remain unreachable.
- No production correction was warranted. The no-splash branch preserves intentional interruption semantics without expanding cleanup to `BaseException` or moving UI/Kernel/FrameCore authority. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_no_splash_plugin_load_keyboard_interrupt.py` (1 case).
- E143 direct proof: `1 passed in 0.19s`; complete `test_versioned_runtime*.py` composition: `63 passed in 3.39s`, with `QT_QPA_PLATFORM=offscreen`.
- Real editor smoke: `plugins=13/20`; project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.17s`.
- Scoped `py_compile` passed. The E143 files are UTF-8 without BOM, CRLF-only, and trailing-whitespace-free. `git diff --check` exited 0 with only existing LF/CRLF warnings; unrelated dirty worktree content was preserved. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E144 -- Versioned Runtime Launcher No-Splash Kernel-Show Failure Matrix Audit**. Advance past successful plugin load to `kernel.show()` with `use_splash=False`, audit ordinary, controlled, and interruption failures while preserving null-cleanup and non-ownership boundaries.
