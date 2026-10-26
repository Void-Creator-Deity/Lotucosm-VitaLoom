# Phase E153 -- Versioned Runtime Launcher Event-Loop Entry/Return Contract Audit

Date: 2026-07-31
Status: complete

## Previous gate

E152 completed the owned-splash `finish_splash` failure matrix complement: a primary RuntimeError retains identity when classified owned cleanup raises a secondary SystemExit. Startup cleanup remains narrow and KeyboardInterrupt remains outside its classification.

## Objective

Audit the next real Launcher boundary after successful startup: `return app.exec()`. Establish that Launcher enters the UI-host event loop exactly once after a successful owned-splash finish, preserves a normal loop return value unchanged, and does not retroactively treat event-loop exceptions as startup failures.

## Evidence required

- Add deterministic direct regression coverage that successfully owns/shows/messages/finishes a splash, constructs/loads/shows the Kernel, then proves `app.exec()` is called exactly once and its ordinary integer return value is returned unchanged.
- At the same fully successful startup boundary, prove RuntimeError, SystemExit, and KeyboardInterrupt raised by `app.exec()` retain natural identity/code/interrupt semantics; neither `dismiss_splash` nor startup-cleanup warning behavior may occur after a successful `finish_splash`.
- Preserve the exact ordered pre-loop sequence and prove no repeated finish, cleanup, or loop entry occurs.
- Add production code only for a demonstrated defect. Keep FrameCore Qt-free L0, preserve Launcher non-ownership of Kernel/Host/Project World/recovery/shutdown, retain QPainter as default, and do not claim OpenGL/native default readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.


## Completion record

- Added `tests/test_versioned_runtime_launcher_event_loop_entry_return_contract.py`: after the complete owned-splash sequence, its four direct cases prove one `app.exec()` call, an unchanged normal integer return, and exact RuntimeError/SystemExit(237)/KeyboardInterrupt propagation.
- Every case preserves the ordered show/message/Kernel/layer/load/show/finish sequence. After successful `finish_splash`, no late `dismiss_splash` call or startup-cleanup warning occurs, and neither finish nor the event loop is repeated.
- No production correction was warranted. `app.exec()` is already correctly outside Launcher startup's cleanup `try` block, so event-loop outcomes retain UI-host semantics without granting Launcher or FrameCore extra lifecycle authority.

## Verification

- Focused offscreen regression: `4 passed in 0.41s`; scoped `py_compile` passed.
- Complete versioned-runtime composition: `80 passed in 7.34s`.
- Offscreen editor smoke: passed, `plugins=13/20`.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all `OK`.
- Anaconda package-signature regression: `2 passed in 0.26s`.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for E152/E153 tests, plans, and prompts. `git diff --check` exited 0; it reported only existing LF/CRLF conversion warnings.

## Next gate

Exactly one next gate: **E154 -- Versioned Runtime Launcher No-Splash Event-Loop Entry/Return Contract Audit**.
