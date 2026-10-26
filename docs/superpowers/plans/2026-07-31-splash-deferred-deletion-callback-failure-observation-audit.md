# Phase E106 -- Splash Deferred-Deletion Callback Failure Observation Audit

Date: 2026-07-31
Status: complete

## Previous gate

E105 established that failures synchronously raised by `finish_splash(...)` before `launch_editor()` enters `app.exec()` are correctly handled by the existing E95 Launcher boundary: immediate finish and timer-scheduling errors retain the primary exception, dismiss exactly once, and suppress event-loop entry.

## Objective

Audit the distinct asynchronous boundary after `QTimer.singleShot(0, splash.deleteLater)` has successfully scheduled work. Map callback-time `deleteLater()` failures to determine whether the splash adapter provides deterministic observation and logging without pretending Launcher can catch errors raised after it has handed control to the Qt event loop. Correct only a demonstrated gap while retaining splash-adapter ownership of deferred presentation cleanup.

## Required evidence

1. Distinguish synchronous `singleShot(...)` scheduling failure from a later scheduled callback failure.
2. Reproduce callback-time deletion failure through a deterministic scheduler double and prove its handling/observation does not alter the successful Launcher `app.exec()` handoff.
3. Preserve E102 event-loop ordering, E103 conditional no-splash behavior, E104 message cleanup, E105 synchronous finish cleanup, and real `QApplication` behavior.
4. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not change `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
5. Run focused red/green proof if a defect exists, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Boundary map: `QTimer.singleShot(0, ...)` may succeed before `launch_editor()` returns its final `app.exec()` handoff, while its callback executes only later on Qt's event loop. E105 covered only a synchronous `singleShot(...)` scheduling exception; it could not own a later callback exception.
- Failure proof: a deterministic timer double retained the scheduled callback. `launch_editor()` successfully reached and returned from `app.exec()` before the callback was manually invoked. Under the old direct-bound-method callback, `splash.deleteLater()` then re-raised its exact `RuntimeError` with no local observation. This demonstrated a real callback-time gap.
- Correction: `finish_splash(...)` now schedules a private adapter-owned callback that invokes `deleteLater()` and catches/logs `Exception` with `Failed to delete splash after editor startup handoff`. The immediate `splash.finish(...)` and synchronous `singleShot(...)` calls remain outside that wrapper, so E105 primary-error identity, exactly-once Launcher dismissal, and event-loop suppression semantics are unchanged.
- Green proof: the deferred callback now records the warning and returns normally, while the successful Launcher handoff still calls `app.exec()` exactly as before. Launcher neither receives the callback nor gains QApplication/splash lifecycle authority.
- Evidence: focused red `1 failed, 53 deselected in 1.03s`; focused green with E105 adjacency `3 passed, 51 deselected in 0.23s`; registry/event-bus interface `54 passed in 1.97s`; offscreen adjacent slice `97 passed in 2.85s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.83s`. Scoped hygiene, compilation, and diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E107 -- Splash Deferred-Deletion Success and Ordering Audit**. Prove the successful deferred callback is scheduled once at zero delay, does not delete before the `app.exec()` handoff, deletes once after callback execution without warning, and retains E105 synchronous-scheduling failure semantics.