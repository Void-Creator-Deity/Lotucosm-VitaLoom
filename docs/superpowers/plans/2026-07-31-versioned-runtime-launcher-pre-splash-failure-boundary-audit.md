# Phase E133 -- Versioned Runtime Launcher Pre-Splash Failure Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E132 completed the splash-handoff cleanup chain. It proved native finish and timer-scheduling controlled exits remain inside the existing Launcher startup cleanup boundary until deferred deletion has actually been accepted. E130, E131, E128, E132, and E129 distinguish adapter-owned pre-return, Launcher-held pre-handoff, incomplete-finish, and completed-handoff event-loop ownership states.

## Objective

Audit Launcher failures before a splash has been allocated. Validate repository/project path normalization, injected runtime-registry/event-bus protocol validation, and application event-loop protocol validation. Prove ordinary exceptions and controlled `SystemExit` preserve their primary identity/code while no splash, Kernel, plugin host, Project World, or event loop is created or entered.

## Audit result

- New direct regressions exercise path-like `SystemExit(141)` from both repository-root and project-path normalization. Each exit preserves the exact object/code before dynamic Launcher composition can create a splash, Kernel, plugin host, Project World, or event loop.
- A property-backed application `exec` lookup proves ordinary `RuntimeError` and controlled `SystemExit(145)` retain exact identity/code during event-loop protocol validation; neither enters `app.exec()` nor triggers splash cleanup.
- Invalid injected capability-registry/event-bus values fail with their existing protocol `TypeError` before application event-loop validation, splash presentation, Kernel construction, or plugin-layer resolution. `KeyboardInterrupt` from a path-like value remains unclassified and cleanup-free.
- No production correction was warranted. The current pre-splash ordering deliberately acquires no Launcher-owned resource until all path/service/application validation has succeeded. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regressions: `tests/test_versioned_runtime_launcher_pre_splash_failure_boundary.py` (7 cases).
- Focused E128--E133/interface slice: `101 passed in 2.38s` with `QT_QPA_PLATFORM=offscreen`.
- Versioned runtime composition slice: `49 passed in 3.68s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`; independent Anaconda signature proof: `2 passed in 0.17s`. The repository `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E134 -- Versioned Runtime Launcher Dynamic-Import Pre-Splash Failure Audit**. Audit the version-runtime imports performed after input normalization but before `splash = None` is assigned; prove ordinary and controlled import-time failure propagation creates no UI/kernel resource and does not widen cleanup ownership.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change, or widening of Launcher resource ownership without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.