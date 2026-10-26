# Phase E146 -- Versioned Runtime Launcher No-Splash Kernel-Show Ordinary-Failure Cleanup-Failure Audit

Date: 2026-07-31
Status: complete

## Previous gate

E145 proved that a no-splash `kernel.show()` controlled exit remains primary when `dismiss_splash(None)` raises an ordinary secondary error. The original SystemExit identity/code, warning-only cleanup behavior, and event-loop exclusion were directly verified after successful Kernel construction and plugin loading.

## Objective

Complete the matching ordinary-primary branch at the same no-splash Kernel-show seam. A primary RuntimeError must retain object identity even when null cleanup itself raises a different RuntimeError.

## Evidence required

- Add a deterministic direct regression that reaches successful no-splash Kernel construction and plugin loading, then injects a primary `RuntimeError` from `kernel.show()` and a distinct cleanup `RuntimeError` from `dismiss_splash(None)`.
- Prove the original primary RuntimeError object survives; cleanup is attempted once and warning-only; splash show/message/finish and `app.exec()` are unreachable; the secondary cleanup error does not mask the primary error.
- Preserve E144's retained KeyboardInterrupt boundary: do not catch BaseException or alter interruption semantics merely to exercise ordinary cleanup failure.
- Add production code only for a demonstrated defect; do not move Kernel/Host/Project World/recovery/shutdown authority into Launcher or FrameCore.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_no_splash_kernel_show_ordinary_failure_cleanup_failure.py`: it reaches successful no-splash Kernel construction and layered plugin loading, raises a primary RuntimeError from `kernel.show()`, and injects a distinct ordinary cleanup RuntimeError from `dismiss_splash(None)`.
- The direct proof preserves the exact primary RuntimeError object. It proves one null-cleanup attempt, warning-only cleanup failure, no splash show/message/finish, and no `app.exec()` entry.
- No production correction was warranted. The existing startup handler already treats an ordinary cleanup error as secondary without expanding exception handling to BaseException or moving lifecycle ownership.

## Verification

- Focused offscreen regression: `1 passed in 0.35s`.
- Complete versioned-runtime composition: `68 passed in 4.65s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.19s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E146 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E147 -- Versioned Runtime Launcher No-Splash Kernel-Show Controlled-Cleanup-Exit Primary-Error Audit**.