# Phase E159 -- Versioned Runtime Launcher Explicit-Service Event-Loop Handoff Audit

Date: 2026-07-31
Status: complete

## Previous gate

E158 completed the invalid explicit-service matrix. It proves malformed caller registry/event-bus values fail at the intended real validator before UI allocation, with registry validation observably preceding event-bus validation and no cleanup ownership.

## Objective

Audit the complementary completed-startup boundary with valid caller-supplied registry and event-bus services. Prove these exact service identities survive the owned-splash startup sequence into the one-time app event-loop handoff; normal return and event-loop exceptions must preserve their result/identity without re-entering Launcher startup cleanup.

## Completion record

- Added `tests/test_versioned_runtime_launcher_explicit_service_event_loop_handoff.py`. For real caller-supplied `InMemoryRuntimeCapabilityRegistry` and `InMemoryRuntimeEventBus`, it exercises normal `app.exec()` return, an ordinary `RuntimeError`, and `SystemExit(269)` after completed owned-splash startup.
- Each case records registry-then-event-bus validation, exact service identities in Kernel kwargs, the full splash-to-Kernel-to-event-loop order, and exactly one event-loop call. The normal result and both raised objects retain their exact values/identities. A forbidden splash dismiss and absent warning prove post-handoff event-loop outcomes do not re-enter Launcher startup cleanup.
- No production change was needed. The existing event-loop boundary is already outside the startup `try` scope and preserves caller-owned L1 services without global lifecycle authority. FrameCore remains Qt-free L0; QPainter remains default; .pond, AI, Inspector, SR2D, and manifest seams remain intact. OpenGL/native is not default-ready and whole-refactor completion is not claimed.

## Verification record

- Focused offscreen compile plus regression: `3 passed in 0.34s`.
- Complete versioned-runtime suite: `93 passed in 5.92s`.
- Editor smoke: `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`.
- Independent Anaconda package-signature regression: `2 passed in 0.20s`.
- `git diff --check` exited 0; it emitted only existing LF/CRLF working-copy warnings. Unrelated dirty worktree content was preserved.

## Next gate

E160 -- Versioned Runtime Launcher No-Splash Explicit-Service Event-Loop Handoff Audit.