# Phase E151 -- Versioned Runtime Launcher Splash-Finish Controlled-Cleanup-Exit Primary-Error Audit

Date: 2026-07-31
Status: complete

## Previous gate

E150 covered primary RuntimeError, SystemExit, and KeyboardInterrupt at the real owned-splash `finish_splash` seam after successful Kernel construction, layered plugin load, and Kernel show. Classified failures get one owned cleanup; KeyboardInterrupt remains unclassified.

## Objective

Verify the E147 cleanup classification remains correct when both the primary post-show finish failure and the owned cleanup failure are controlled exits. A secondary cleanup SystemExit must not mask the active primary finish SystemExit.

## Evidence required

- Add a deterministic direct regression that owns a splash, successfully constructs/loads/shows the Kernel, then makes `finish_splash(splash, kernel)` raise a specific primary `SystemExit` and `dismiss_splash(splash)` raise a distinct secondary `SystemExit`.
- Prove exact primary SystemExit identity/code survive; owned cleanup is once-only and warning-only; the complete pre-finish sequence occurs; and `app.exec()` is unreachable.
- Preserve the explicit KeyboardInterrupt boundary: do not catch BaseException or reclassify interruption semantics.
- Add production code only for a demonstrated defect; retain FrameCore Qt-free L0 and Launcher non-ownership of host/kernel/project lifecycle.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_splash_finish_controlled_cleanup_exit.py`: it owns a splash, successfully constructs/loads/shows the Kernel, raises primary `SystemExit(231)` from `finish_splash(splash, kernel)`, and injects secondary `SystemExit(232)` from `dismiss_splash(splash)`.
- The direct proof preserves the exact primary SystemExit object and exit code. Owned cleanup is attempted once and logged warning-only; the full pre-finish sequence occurs and `app.exec()` remains unreachable.
- No production correction was warranted. E147's existing inner `(Exception, SystemExit)` cleanup classification prevents a controlled owned cleanup exit from masking the active primary finish exit without catching KeyboardInterrupt.

## Verification

- Focused offscreen regression: `1 passed in 0.37s`.
- Complete versioned-runtime composition: `75 passed in 5.72s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.25s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E151 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E152 -- Versioned Runtime Launcher Splash-Finish Ordinary-Primary Controlled-Cleanup-Exit Audit**.