# Phase E163 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Failure Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E162 completed owned-splash cleanup evidence for explicit-service project-binding failures, preserving exact errors and preventing downstream plugin/event-loop work.

## Objective

Audit the complementary no-splash project-binding failure boundary after valid explicit service composition. Prove exact primary-error propagation with the established safe null cleanup, no default-service substitution, and no plugin-layer/loading or event-loop entry.

## Implementation and evidence

- Added `tests/test_versioned_runtime_launcher_no_splash_explicit_service_startup_project_failure_boundary.py`.
- With real explicit `InMemoryRuntimeCapabilityRegistry` and `InMemoryRuntimeEventBus`, the Launcher validates registry then event bus, forwards both original objects to `EditorKernel`, and calls `set_startup_project()` with the explicit absolute `.pond` path.
- For `RuntimeError("no-splash explicit project binding failed")` and `SystemExit(311)`, the captured primary error is the exact original object. Plugin-layer resolution/loading and `app.exec()` remain unreachable.
- `use_splash=False` forbids splash creation, messages, and finish. The established generic startup-exception path still invokes safe null cleanup exactly once as `dismiss_splash(None)`; successful cleanup does not emit `Failed to dismiss splash after editor startup failure`.
- Focused offscreen regression: `2 passed in 0.30s`.
- Full versioned-runtime suite: `101 passed in 6.81s`.
- Editor smoke: `plugins=13/20`; project-plugin-model, core-boundaries, GUI-boundaries, and release-consistency guards: `OK`; Anaconda package-signature regression: `2 passed in 0.18s`; `git diff --check`: exit 0 with pre-existing LF/CRLF warnings only.
- No production correction was warranted. FrameCore stays Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; `.pond`, AI command registry, Inspector binding, SR2D, package manifests, and project manifests remain unchanged.

## Next gate

Exactly one next gate: **E164 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Null-Cleanup Failure Audit**.
