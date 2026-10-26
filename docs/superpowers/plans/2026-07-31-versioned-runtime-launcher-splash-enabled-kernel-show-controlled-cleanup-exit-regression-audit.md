# Phase E148 -- Versioned Runtime Launcher Splash-Enabled Kernel-Show Controlled-Cleanup-Exit Regression Audit

Date: 2026-07-31
Status: complete

## Previous gate

E147 corrected a proven primary-error masking defect in the Launcher cleanup handler: a no-splash secondary cleanup SystemExit can no longer replace an active primary Kernel-show SystemExit. The correction catches `(Exception, SystemExit)` only inside cleanup; KeyboardInterrupt remains unclassified.

## Objective

Cover the same corrected cleanup classification when Launcher owns a real splash object. Verify that the normal splash-enabled pre-show flow does not change, and a controlled cleanup exit cannot mask the primary Kernel-show controlled exit.

## Evidence required

- Add a deterministic direct regression that creates a splash, reaches successful Kernel construction and plugin loading, then makes `kernel.show()` raise a primary `SystemExit` and `dismiss_splash(splash)` raise a distinct secondary `SystemExit`.
- Prove exact primary SystemExit identity/code survive; splash show and both expected pre-show messages occur in order; cleanup receives the owned splash exactly once; cleanup is warning-only; finish and `app.exec()` remain unreachable.
- Confirm the E147 correction still excludes KeyboardInterrupt and does not introduce host/FrameCore lifecycle authority.
- Add production code only for a demonstrated defect; preserve FrameCore Qt-free L0.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_splash_enabled_kernel_show_controlled_cleanup_exit.py`: it owns a splash, performs the normal ordered pre-show messages, reaches successful Kernel construction and layered plugin loading, then injects primary `SystemExit(221)` from `kernel.show()` and secondary `SystemExit(222)` from `dismiss_splash(splash)`.
- The direct regression proves the E147 correction applies to an owned splash: the exact primary exit object/code survives, cleanup receives the owned splash exactly once and logs warning-only, while finish and `app.exec()` remain unreachable.
- No additional production correction was warranted. E147's narrow cleanup classification handles both null and owned splash references without catching KeyboardInterrupt or assigning host lifecycle authority to Launcher/FrameCore.

## Verification

- Focused offscreen regression: `1 passed in 0.35s`.
- Complete versioned-runtime composition: `70 passed in 5.63s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.23s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E148 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E149 -- Versioned Runtime Launcher Splash-Enabled Kernel-Show Ordinary-Primary Controlled-Cleanup-Exit Audit**.