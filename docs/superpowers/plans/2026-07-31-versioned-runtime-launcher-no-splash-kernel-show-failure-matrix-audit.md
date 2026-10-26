# Phase E144 -- Versioned Runtime Launcher No-Splash Kernel-Show Failure Matrix Audit

Date: 2026-07-31
Status: complete

## Previous gate

E143 proved that a no-splash plugin-load `KeyboardInterrupt` is intentionally unclassified: it preserves identity and bypasses even `dismiss_splash(None)`, Kernel show, splash operations, and event-loop entry. E142 already proves the corresponding ordinary/SystemExit plugin-load paths safely traverse the null cleanup no-op.

## Objective

Advance to the next actual startup seam after successful plugin loading: `kernel.show()` with `use_splash=False`. Audit primary-error, controlled-exit, and interruption behavior without reintroducing splash ownership, null-cleanup ambiguity, or FrameCore lifecycle authority.

## Evidence required

- Add direct deterministic regressions that reach successful Kernel construction and plugin load, then inject ordinary `RuntimeError`, `SystemExit`, and retained `KeyboardInterrupt` at `kernel.show()` while splash is disabled.
- Prove ordinary/SystemExit preserve exact primary object/code and invoke only `dismiss_splash(None)`; KeyboardInterrupt preserves identity and invokes no cleanup; no splash show/message/finish or `app.exec()` occurs in every case.
- Keep existing splash-enabled E138 behavior and plugin-load E139-E143 behavior green; do not broaden exception handling to BaseException or make Launcher own Kernel/Host/Project World/recovery/shutdown.
- Add production code only for a demonstrated defect; retain FrameCore Qt-free L0 and all project/plugin public seams.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_no_splash_kernel_show_failure.py`: a direct three-case seam matrix reaches successful Kernel construction and layered plugin loading, then injects `RuntimeError`, `SystemExit(211)`, or `KeyboardInterrupt` from `kernel.show()`.
- The direct proof preserves the exact primary exception object (and controlled-exit code), executes exactly one `dismiss_splash(None)` only for `RuntimeError`/`SystemExit`, leaves `KeyboardInterrupt` outside cleanup, never invokes splash show/message/finish, and never reaches `app.exec()`.
- No production correction was warranted. The existing Launcher exception boundary and the UI adapter's null-splash no-op already satisfy the required ownership and lifecycle boundary.

## Verification

- Focused offscreen regression: `3 passed in 0.20s`.
- Complete versioned-runtime composition: `66 passed in 5.05s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.17s`; scoped `py_compile` passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the new E144 test, plan, and prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E145 -- Versioned Runtime Launcher No-Splash Kernel-Show Cleanup-Failure Primary-Error Audit**.