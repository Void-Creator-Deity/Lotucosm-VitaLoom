# Phase E145 -- Versioned Runtime Launcher No-Splash Kernel-Show Cleanup-Failure Primary-Error Audit

Date: 2026-07-31
Status: complete

## Previous gate

E144 proved that, with `use_splash=False`, a `kernel.show()` RuntimeError or SystemExit preserves the primary error through the safe `dismiss_splash(None)` path, while KeyboardInterrupt intentionally bypasses cleanup. Successful Kernel construction and layered plugin loading were exercised before the show seam.

## Objective

Audit the combined no-splash Kernel-show controlled-exit and cleanup-failure path. The primary `SystemExit` must remain authoritative even when the UI adapter's nominally safe null cleanup hook itself raises an ordinary exception.

## Evidence required

- Add a direct deterministic regression that reaches successful Kernel construction and plugin loading with `use_splash=False`, then makes `kernel.show()` raise a specific `SystemExit` and `dismiss_splash(None)` raise a distinct ordinary `RuntimeError`.
- Prove exact primary SystemExit identity and exit code survive; prove cleanup is attempted once, its failure is warning-only, splash show/message/finish and `app.exec()` are unreachable, and no secondary cleanup error replaces the primary exit.
- Retain E144's explicit KeyboardInterrupt boundary: do not broaden exception handling to BaseException merely to cover cleanup behavior.
- Add production code only for a demonstrated defect; do not transfer Kernel/Host/Project World/recovery/shutdown authority to the Launcher or FrameCore.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_no_splash_kernel_show_cleanup_failure.py`: it reaches successful no-splash Kernel construction and layered plugin loading, raises `SystemExit(213)` from `kernel.show()`, and injects a distinct ordinary cleanup `RuntimeError` from `dismiss_splash(None)`.
- The direct proof preserves the exact primary SystemExit object and exit code. It proves one null-cleanup attempt, warning-only cleanup failure, no splash show/message/finish, and no `app.exec()` entry.
- No production correction was warranted. Launcher already preserves a primary `Exception`/`SystemExit` when cleanup has an ordinary secondary failure, without expanding the boundary to `BaseException` or claiming host lifecycle ownership.

## Verification

- Focused offscreen regression: `1 passed in 0.33s`.
- Complete versioned-runtime composition: `67 passed in 5.77s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.18s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E145 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E146 -- Versioned Runtime Launcher No-Splash Kernel-Show Ordinary-Failure Cleanup-Failure Audit**.