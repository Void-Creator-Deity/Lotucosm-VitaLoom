# Phase E147 -- Versioned Runtime Launcher No-Splash Kernel-Show Controlled-Cleanup-Exit Primary-Error Audit

Date: 2026-07-31
Status: complete

## Previous gate

E146 completed the ordinary-primary and ordinary-cleanup-failure branch at no-splash `kernel.show()`: the primary RuntimeError survives by identity, cleanup is warning-only, and splash/event-loop operations remain unreachable after successful Kernel construction and plugin load.

## Objective

Audit the remaining classified cleanup-failure category: a secondary controlled `SystemExit` raised by `dismiss_splash(None)`. A cleanup controlled exit must not mask the already-active primary Kernel-show controlled exit, while `KeyboardInterrupt` remains intentionally unclassified.

## Evidence required

- Add a deterministic regression that reaches successful no-splash Kernel construction and plugin loading, then makes `kernel.show()` raise a specific primary `SystemExit` and `dismiss_splash(None)` raise a distinct secondary `SystemExit`.
- Prove exact primary SystemExit identity/code remain authoritative; cleanup is attempted once, its controlled exit is warning-only, splash show/message/finish and `app.exec()` are unreachable, and the secondary exit does not replace the primary failure.
- If the direct regression exposes a masking defect, narrowly correct only the cleanup handler to classify `SystemExit` alongside ordinary cleanup exceptions. Do not catch BaseException; preserve the KeyboardInterrupt boundary.
- Keep FrameCore Qt-free L0 and do not move Kernel/Host/Project World/recovery/shutdown authority into Launcher.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.
## Completion record

- Added `tests/test_versioned_runtime_launcher_no_splash_kernel_show_controlled_cleanup_exit.py`: it reaches successful no-splash Kernel construction and layered plugin loading, raises primary `SystemExit(217)` from `kernel.show()`, and injects secondary `SystemExit(218)` from `dismiss_splash(None)`.
- The direct regression exposed a real masking defect: the cleanup handler only caught `Exception`, so its secondary `SystemExit(218)` replaced the primary exit.
- Corrected only the inner cleanup handler in `core/VitaLoom/editor_launcher.py` to catch `(Exception, SystemExit)`. It now logs a controlled cleanup exit warning-only and re-raises the original active primary error. The outer handler still excludes `KeyboardInterrupt`; no lifecycle authority moved to Launcher or FrameCore.

## Verification

- Focused offscreen regression: initially failed with secondary `SystemExit(218)` masking primary `SystemExit(217)`; after the narrow correction, `1 passed in 0.35s`.
- Complete versioned-runtime composition: `69 passed in 5.32s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.22s`; scoped `py_compile` for production/test files passed.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the changed production file and E147 test/plan/prompt. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E148 -- Versioned Runtime Launcher Splash-Enabled Kernel-Show Controlled-Cleanup-Exit Regression Audit**.