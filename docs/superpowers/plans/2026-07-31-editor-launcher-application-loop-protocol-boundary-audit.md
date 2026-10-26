# Phase E102 -- Editor Launcher Application-Loop Protocol Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E101 made injected runtime-service validation deterministic before splash, Kernel, and plugin-layer side effects, while preserving Kernel ownership of the default event bus and the existing Qt-free service validators.

## Objective

Audit the public `app` handoff accepted by `launch_editor()` across the optional splash/event-processing calls and the final `app.exec()` transition. Establish the real accepted application protocol, validation/error timing, and cleanup boundary for invalid application objects. Correct only a demonstrated early-side-effect defect without replacing the real Qt application contract or making Launcher an application lifecycle authority.

## Required evidence

1. Map every Launcher and splash use of `app`, the production caller in `runtime/main.py`, and the existing lightweight test doubles.
2. Reproduce invalid `app` behavior with and without splash, including whether Kernel/plugin startup can occur before a missing required application capability is reported.
3. If correction is warranted, preserve valid `QApplication` behavior and compatible deterministic test doubles; retain primary error identity and E95 splash dismissal semantics.
4. Do not make Launcher create, own, close, replace, or globally cache an application; do not move UI lifecycle, Kernel/Host, Project World, runtime-service, bundle-path, project/recovery, or environment authority into Launcher.
5. Run focused red/green proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

Do not change `.pond`, AI-command registry, Inspector command binding, SR2D, manifests/public imports/MRO, plugin discovery/loading, renderer defaults, Player/export, Project World opening/fallback/recovery, or application-shell direction. The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Application map: `runtime/main.py` creates or reuses the real `QApplication`, applies its UI baseline, then passes it to Launcher. Launcher always executes `app.exec()` after a successful startup. When splash is enabled, the splash adapter owns its optional `app.processEvents()` calls; existing deterministic test doubles deliberately provide only the subset needed by each tested path.
- Defect reproduced: an object without callable `exec` could start a Kernel when splash was disabled, or display a splash when it was enabled, before later failing at the unavoidable final event-loop call. The two explicit cases were red as `2 failed, 36 deselected in 0.47s`, proving both side-effect leaks.
- Narrow correction: Launcher now checks only its unconditional minimum application protocol, a callable `app.exec`, after earlier repo/project/runtime-service input validation but before splash, Kernel construction, or plugin-layer resolution. This deliberately retains E99/E100/E101 validation precedence for their own invalid public inputs, preserves real `QApplication` and compatible test doubles, and leaves splash-specific `processEvents()` behavior in the splash adapter rather than creating a Launcher-owned application lifecycle rule.
- Test adaptation: two E96 constructor/plugin-failure tests previously used a bare `object()` because the old path never reached `app.exec()`. They now use minimal `exec()` doubles that explicitly fail if the event loop is entered; their intended environment/primary-error assertions are unchanged. No production caller, application creation, close, caching, replacement, Kernel/Host, Project World, runtime-service, bundle-path, project/recovery, or environment authority changed.
- Evidence: focused red/green `2 failed, 36 deselected in 0.47s` -> `2 passed, 36 deselected in 0.40s`; current registry/event-bus interface proof `47 passed in 0.93s`; adjacent offscreen lifecycle suite `149 passed in 4.17s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails all passed; independent Anaconda signature proof `2 passed in 0.30s`; scoped UTF-8-sig compilation, CRLF/no-bare-LF, trailing-whitespace checks, and scoped `git diff --check` passed. The existing `docs/mainline_status.md` trailing whitespace remains limited to historical lines 2020-2021 and was not changed. `.venv` still lacks `cryptography`; no dependency was installed. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E103 -- Editor Launcher Splash Event-Processing Protocol Boundary Audit**. Audit conditional splash `app.processEvents()` requirements, failure timing, and E95 cleanup behavior without turning Launcher into a Qt application lifecycle authority.