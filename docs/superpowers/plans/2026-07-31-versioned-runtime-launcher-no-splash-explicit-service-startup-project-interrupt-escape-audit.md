# Phase E165 -- Versioned Runtime Launcher No-Splash Explicit-Service Startup-Project Interrupt Escape Audit

Date: 2026-07-31
Status: complete

## Previous gate

E164 proved that ordinary and controlled failures from the established `dismiss_splash(None)` path remain secondary to an explicit-service project-binding failure and are recorded as cleanup warnings.

## Objective

Audit the intentionally distinct `KeyboardInterrupt` boundary at no-splash explicit-service project binding. Prove that the interrupt escapes as its original object without entering the Launcher `Exception`/`SystemExit` cleanup policy, while preserving real service validation, Kernel identity forwarding, and downstream non-reachability.

## Implementation and evidence

- Added `tests/test_versioned_runtime_launcher_no_splash_explicit_service_startup_project_interrupt_escape.py`.
- Real explicit `InMemoryRuntimeCapabilityRegistry` and `InMemoryRuntimeEventBus` validate in registry-to-event-bus order and are forwarded unchanged to `EditorKernel` before explicit absolute `.pond` binding.
- When `set_startup_project()` raises a specific `KeyboardInterrupt` instance, that exact object escapes. It is intentionally outside the Launcher `except (Exception, SystemExit)` cleanup policy.
- Default-registry construction, every splash adapter including `dismiss_splash`, plugin-layer resolution/loading, and `app.exec()` are unreachable.
- Focused offscreen regression: `1 passed in 0.38s`.
- Full versioned-runtime suite: `104 passed in 8.95s`.
- Editor smoke: `plugins=13/20`; project-plugin-model, core-boundaries, GUI-boundaries, and release-consistency guards: `OK`; Anaconda package-signature regression: `2 passed in 0.17s`; `git diff --check`: exit 0 with pre-existing LF/CRLF warnings only.
- No production correction was warranted. FrameCore stays Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; `.pond`, AI command registry, Inspector binding, SR2D, package manifests, and project manifests remain unchanged.

## Next gate

Exactly one next gate: **E166 -- VitaLoom Whole-Refactor Completion Evidence and Remaining-Architecture Audit**.
