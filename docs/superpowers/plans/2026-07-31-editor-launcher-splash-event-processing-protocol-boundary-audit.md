# Phase E103 -- Editor Launcher Splash Event-Processing Protocol Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E102 established the unconditional application protocol that Launcher itself consumes: a callable `app.exec` is required before splash, Kernel, or plugin-layer startup work, while earlier path and runtime-service validation precedence remains intact.

## Objective

Audit the conditional `app.processEvents()` requirement exercised only by the splash adapter. Map `use_splash`, `VITALOOM_NO_SPLASH`, splash creation/message timing, and E95 failure cleanup to determine whether an invalid application object can cause avoidable partial splash work or whether the current splash-owned failure boundary is intentional. Correct only a proven defect without moving Qt application lifecycle authority into Launcher.

## Required evidence

1. Map Launcher-to-splash application calls, the environment-controlled no-splash branch, and production/test callers using real applications or doubles.
2. Reproduce missing/non-callable `processEvents` behavior with splash requested and splash suppressed, including exact error identity and splash cleanup visibility.
3. Preserve the E102 unconditional `exec` boundary, E95 primary-error/dismissal semantics, E96 environment neutrality, and valid real `QApplication` behavior.
4. Do not make Launcher create, close, cache, replace, or globally validate an application beyond a proven direct handoff boundary; do not move Kernel/Host, Project World, runtime-service, bundle-path, project/recovery, or environment authority into Launcher.
5. Run focused red/green proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

Do not change `.pond`, AI-command registry, Inspector command binding, SR2D, manifests/public imports/MRO, plugin discovery/loading, renderer defaults, Player/export, Project World opening/fallback/recovery, application-shell direction, or default rendering. The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Call map: Launcher reaches the splash adapter only when `use_splash=True`. The adapter first honors `VITALOOM_NO_SPLASH`; only if it will display a splash does it consume `app.processEvents()`. Later `splash_message(...)` calls occur only for an existing splash. `runtime/main.py` still creates or reuses the real `QApplication`; Launcher retains only its E102 `exec()` handoff.
- Defect reproduced: with a callable `exec()` but missing or non-callable `processEvents`, the adapter previously created a splash before raising. Because `show_vitaloom_splash(...)` never returned, Launcher still held `splash=None`, so E95 cleanup could not dismiss that partial presentation. The focused red proof was `2 failed, 1 passed, 39 deselected in 0.45s`.
- Narrow correction: the splash adapter now checks its conditional `processEvents()` protocol after the no-splash environment branch but before constructing a presentation. If `splash.show()` or event processing itself raises after construction, the adapter synchronously uses the existing `dismiss_splash(...)`; cleanup failure is logged without replacing the primary exception. Launcher gained no global application validation, environment control, or Qt lifecycle authority.
- Regression proof: focused final `5 passed, 38 deselected in 0.39s`; registry/event-bus interface `43 passed in 0.49s`; offscreen adjacent runtime/kernel/smoke slice `86 passed in 1.23s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails all passed; independent Anaconda signature proof `2 passed in 0.16s`.
- Scoped UTF-8-sig compilation, CRLF/no-bare-LF, trailing-whitespace, and changed-file diff checks passed. `.venv` still lacks `cryptography`; no dependency was installed. Existing historical trailing whitespace in `docs/mainline_status.md` remains untouched. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E104 -- Editor Launcher Splash-Message Failure Cleanup Audit**. Audit the existing-splash `splash_message(...)` failure paths (`showMessage` and `processEvents`) for primary-error identity and exactly-once E95 dismissal without transferring splash or application ownership to Launcher.