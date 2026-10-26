# Phase E162 -- Versioned Runtime Launcher Explicit-Service Startup-Project Failure Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E161 proved valid explicit registry/event-bus services compose correctly with a normalized startup-project request before plugin loading in the no-splash branch.

## Objective

Audit owned-splash startup failure when `Kernel.set_startup_project()` raises after valid explicit service composition. Prove exact primary-error propagation, one owned splash dismissal, no plugin-layer/loading or event-loop entry, and stable explicit-service identities at the construction seam.

## Completion record

- Added `tests/test_versioned_runtime_launcher_explicit_service_startup_project_failure_ownership.py`. It exercises an ordinary RuntimeError and `SystemExit(301)` from project binding after real explicit registry/event-bus validation, splash acquisition, and Kernel construction.
- Each case preserves the exact primary object, forwards explicit services unchanged by identity, dismisses the owned splash once, and makes plugin-layer resolution, plugin loading, splash finish, and app-loop entry unreachable. No cleanup warning is emitted when dismissal succeeds.
- No production change was needed. The existing owned-splash startup boundary already covers project-binding failures without widening service or project lifecycle ownership. FrameCore remains Qt-free L0, QPainter remains default, `.pond`, AI, Inspector, SR2D, and manifest seams remain intact, and OpenGL/native is not default-ready.

## Verification record

- Focused offscreen compile plus regression: `2 passed in 0.25s`.
- Complete versioned-runtime suite: `99 passed in 8.50s`.
- Editor smoke: `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`.
- Independent Anaconda package-signature regression: `2 passed in 0.20s`.
- `git diff --check` exited 0 with only existing LF/CRLF working-copy warnings; unrelated dirty worktree content was preserved.

## Next gate

E163 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Failure Boundary Audit.