# Phase E150 -- Versioned Runtime Launcher Splash-Finish Failure Matrix Audit

Date: 2026-07-31
Status: complete

## Previous gate

E149 completed the owned-splash Kernel-show cleanup classification: both ordinary and controlled primary Kernel-show failures retain authority when owned cleanup raises a controlled SystemExit. The narrow handler preserves the intentional KeyboardInterrupt boundary.

## Objective

Advance to the next actual post-show startup seam: `finish_splash(splash, kernel)`. Audit primary ordinary failure, controlled exit, and retained KeyboardInterrupt after Kernel show has succeeded, without giving Launcher broader lifecycle authority.

## Evidence required

- Add deterministic direct regressions that create an owned splash, successfully construct/load/show the Kernel, then inject `RuntimeError`, `SystemExit`, and retained `KeyboardInterrupt` at `finish_splash`.
- Prove ordinary/SystemExit preserve exact primary object/code and invoke `dismiss_splash(splash)` exactly once; KeyboardInterrupt preserves identity and invokes no cleanup; `app.exec()` is unreachable in every case.
- Prove the complete pre-finish sequence is real: splash show/messages, Kernel construction, layered plugin load, and Kernel show all occur before the injected seam.
- Do not broaden handling to BaseException, modify Project World/Host ownership, or migrate FrameCore away from Qt-free L0.
- Add production code only for a demonstrated defect; run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_splash_finish_failure.py`: a three-case direct matrix owns a splash, successfully constructs/loads/shows the Kernel, then injects RuntimeError, `SystemExit(229)`, or retained KeyboardInterrupt at `finish_splash(splash, kernel)`.
- The direct proof preserves exact primary identity/code. RuntimeError and SystemExit each call `dismiss_splash(splash)` exactly once; KeyboardInterrupt preserves identity and calls no cleanup. All cases reach the real pre-finish sequence and block event-loop entry.
- No production correction was warranted. The existing classified startup handler and explicit KeyboardInterrupt boundary already apply at the post-show finish seam without changing FrameCore or Launcher lifecycle authority.

## Verification

- Focused offscreen regression: `3 passed in 0.38s`.
- Complete versioned-runtime composition: `74 passed in 5.92s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.24s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the E150 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E151 -- Versioned Runtime Launcher Splash-Finish Controlled-Cleanup-Exit Primary-Error Audit**.