# Phase E164 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Null-Cleanup Failure Audit

Date: 2026-07-31
Status: complete

## Previous gate

E163 established the no-splash explicit-service project-binding failure boundary: primary RuntimeError/SystemExit identity is preserved, downstream startup is blocked, and the generic exception path performs one safe `dismiss_splash(None)` cleanup call.

## Objective

Audit the secondary-failure boundary of that established null cleanup. Prove that ordinary and controlled failures from `dismiss_splash(None)` cannot mask the original explicit-service `set_startup_project()` failure, that the expected warning is recorded, and that no splash allocation, plugin work, or event-loop entry becomes reachable.

## Implementation and evidence

- Added `tests/test_versioned_runtime_launcher_no_splash_explicit_service_startup_project_null_cleanup_failure.py`.
- With real explicit `InMemoryRuntimeCapabilityRegistry` and `InMemoryRuntimeEventBus`, the Launcher validates registry then event bus, forwards both exact objects to `EditorKernel`, and binds the explicit absolute `.pond` path before any plugin work.
- A primary `RuntimeError("no-splash explicit project binding failed")` and primary `SystemExit(313)` both remain the exact raised object when `dismiss_splash(None)` subsequently raises, respectively, `RuntimeError("no-splash explicit null cleanup failed")` and `SystemExit(314)`.
- Cleanup is attempted exactly once with `None`; its ordinary or controlled failure is secondary and logs `Failed to dismiss splash after editor startup failure`. Splash creation/message/finish, default-registry construction, plugin-layer resolution/loading, and `app.exec()` are unreachable.
- Focused offscreen regression: `2 passed in 0.25s`.
- Full versioned-runtime suite: `103 passed in 9.14s`.
- Editor smoke: `plugins=13/20`; project-plugin-model, core-boundaries, GUI-boundaries, and release-consistency guards: `OK`; Anaconda package-signature regression: `2 passed in 0.25s`; `git diff --check`: exit 0 with pre-existing LF/CRLF warnings only.
- No production correction was warranted. FrameCore stays Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; `.pond`, AI command registry, Inspector binding, SR2D, package manifests, and project manifests remain unchanged.

## Next gate

Exactly one next gate: **E165 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Interrupt Escape Audit**.
