# Phase E149 -- Versioned Runtime Launcher Splash-Enabled Kernel-Show Ordinary-Primary Controlled-Cleanup-Exit Audit

Date: 2026-07-31
Status: complete

## Previous gate

E148 verified E147's narrow cleanup classification with an owned splash and a controlled primary Kernel-show exit. The normal splash display/message order remains intact, and an owned cleanup SystemExit is warning-only rather than masking the primary exit.

## Objective

Complete the complementary owned-splash primary category: a RuntimeError from `kernel.show()` must retain identity when owned splash cleanup raises a controlled `SystemExit`.

## Evidence required

- Add a deterministic direct regression that creates a splash, reaches successful Kernel construction and plugin loading, then injects primary `RuntimeError` at `kernel.show()` and a distinct secondary `SystemExit` at `dismiss_splash(splash)`.
- Prove the exact RuntimeError object survives; splash pre-show order is intact; owned cleanup occurs exactly once and is warning-only; finish and `app.exec()` remain unreachable; the secondary exit does not mask the primary ordinary error.
- Preserve the deliberately unclassified KeyboardInterrupt boundary; do not catch BaseException or alter FrameCore/Launcher ownership.
- Add production code only for a demonstrated defect; keep FrameCore Qt-free L0.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_splash_enabled_kernel_show_ordinary_primary_controlled_cleanup_exit.py`: it owns a splash, preserves the ordered pre-show flow through successful Kernel construction and layered plugin loading, then injects a primary RuntimeError from `kernel.show()` and secondary `SystemExit(224)` from `dismiss_splash(splash)`.
- The direct proof preserves the exact primary RuntimeError object. It verifies owned cleanup happens exactly once and is warning-only, while splash finish and `app.exec()` remain unreachable.
- No production correction was warranted. E147's narrow inner cleanup classification already prevents a controlled secondary cleanup exit from masking either ordinary or controlled primary startup errors, without catching KeyboardInterrupt.

## Verification

- Focused offscreen regression: `1 passed in 0.37s`.
- Complete versioned-runtime composition: `71 passed in 5.37s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.29s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E149 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E150 -- Versioned Runtime Launcher Splash-Finish Failure Matrix Audit**.