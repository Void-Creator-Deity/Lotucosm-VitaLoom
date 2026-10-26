# Phase E152 -- Versioned Runtime Launcher Splash-Finish Ordinary-Primary Controlled-Cleanup-Exit Audit

Date: 2026-07-31
Status: complete

## Previous gate

E151 verified that a primary owned-splash `finish_splash` SystemExit remains authoritative when the subsequent owned cleanup raises a distinct SystemExit. The narrow cleanup classification retained the primary exit without catching KeyboardInterrupt.

## Objective

Complete the complementary primary category at the same real finish seam: a primary RuntimeError must retain identity when owned cleanup raises a classified controlled `SystemExit`.

## Evidence required

- Add a deterministic direct regression that owns a splash, successfully constructs/loads/shows the Kernel, makes `finish_splash(splash, kernel)` raise a primary RuntimeError, and makes `dismiss_splash(splash)` raise a distinct secondary SystemExit.
- Prove exact primary RuntimeError identity survives; owned cleanup is once-only and warning-only; the complete pre-finish sequence occurs; finish does not continue; and `app.exec()` is unreachable.
- Keep KeyboardInterrupt outside the cleanup classification; do not catch BaseException or alter FrameCore/Launcher lifecycle boundaries.
- Add production code only for a demonstrated defect; retain FrameCore Qt-free L0.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added `tests/test_versioned_runtime_launcher_splash_finish_ordinary_primary_controlled_cleanup_exit.py`: it owns a splash, successfully constructs/loads/shows the Kernel, raises a primary RuntimeError from `finish_splash(splash, kernel)`, and injects secondary `SystemExit(234)` from `dismiss_splash(splash)`.
- The direct proof preserves the exact primary RuntimeError object. Owned cleanup receives the same splash exactly once and is warning-only; the complete pre-finish sequence occurs, finish does not continue, and `app.exec()` remains unreachable.
- No production correction was warranted. E147's narrow inner `(Exception, SystemExit)` cleanup classification already prevents a controlled owned-cleanup exit from masking an ordinary primary failure without catching KeyboardInterrupt.

## Verification

- Focused offscreen regression: `1 passed in 0.34s`.
- Complete versioned-runtime composition: `76 passed in 5.60s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.24s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks and `git diff --check` are re-run after this documentation closure; existing LF/CRLF conversion warnings alone are non-blocking when `git diff --check` exits 0.

## Next gate

Exactly one next gate: **E153 -- Versioned Runtime Launcher Event-Loop Entry/Return Contract Audit**.
