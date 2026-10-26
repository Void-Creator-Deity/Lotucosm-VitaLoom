# Phase E154 -- Versioned Runtime Launcher No-Splash Event-Loop Entry/Return Contract Audit

Date: 2026-07-31
Status: complete

## Previous gate

E153 verified the complete owned-splash startup handoff: after successful finish, Launcher calls `app.exec()` once, returns its ordinary value unchanged, and leaves RuntimeError/SystemExit/KeyboardInterrupt to the UI-host event-loop boundary without late startup cleanup.

## Objective

Complete the no-splash counterpart at the same event-loop boundary. Verify that successful Kernel construction/layer loading/show with `use_splash=False` enters `app.exec()` exactly once, preserves its ordinary return, and propagates event-loop outcomes naturally while no splash or cleanup adapter work occurs.

## Evidence required

- Add deterministic direct regression coverage that uses `use_splash=False`, reaches successful Kernel construction/layer loading/show, and proves a single `app.exec()` call plus unchanged ordinary integer return.
- In the same no-splash path, prove RuntimeError, SystemExit, and KeyboardInterrupt from `app.exec()` preserve identity/code/interrupt semantics; splash show/message/finish/dismiss and startup-cleanup warning behavior must remain absent.
- Preserve order and single execution of kernel/layer operations; do not infer splash ownership from the no-splash mode.
- Add production code only for a demonstrated defect. Keep FrameCore Qt-free L0, retain Launcher non-ownership of Kernel/Host/Project World/recovery/shutdown, keep QPainter default, and do not claim OpenGL/native default readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added tests/test_versioned_runtime_launcher_no_splash_event_loop_entry_return_contract.py: four direct no-splash cases prove one app.exec() call, unchanged normal integer return, and exact RuntimeError/SystemExit(239)/KeyboardInterrupt propagation after successful Kernel construction, layered loading, and show.
- Every case makes splash show/message/finish/dismiss a failing seam, proving no splash adapter or startup-cleanup warning is consumed in no-splash mode. Kernel/layer operations occur once in order.
- No production correction was warranted. The existing post-startup return app.exec() boundary already preserves UI-host ownership and never infers splash cleanup from no-splash operation.

## Verification

- Focused offscreen regression: 4 passed in 0.20s; scoped py_compile passed.
- Complete versioned-runtime composition: 84 passed in 7.34s.
- Offscreen editor smoke: passed, plugins=13/20.
- Guards: project plugin model, core boundary, GUI boundary, and release consistency all OK.
- Anaconda package-signature regression: 2 passed in 0.22s.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks and git diff --check are re-run after this documentation closure; existing LF/CRLF conversion warnings alone are non-blocking when git diff --check exits 0.

## Next gate

Exactly one next gate: **E155 -- Versioned Runtime Launcher Explicit-Service Success-Composition Audit**.
