# Phase E108 -- Splash Deferred-Deletion Real-Qt Event-Loop Parity Audit

Date: 2026-07-31
Status: complete

## Previous gate

E107 proved with a deterministic scheduler double that the E106 private splash-adapter callback preserves the successful ordering: one zero-delay scheduling call follows `finish`, no deletion occurs before the successful `app.exec()` handoff, and one later successful deletion emits no warning.

## Objective

Validate that the E106/E107 callback contract also behaves as intended under a real offscreen Qt event cycle. Exercise the actual `QTimer.singleShot(0, ...)` callback delivery for both a successful deletion and a controlled deletion failure, proving callback execution, observation, and ordering parity without granting Launcher Qt callback or splash lifecycle authority.

## Required evidence

1. Use a real offscreen `QApplication` and Qt event processing to deliver the actual zero-delay callback.
2. Prove a successful real callback deletes once after scheduling and emits no E106 warning.
3. Prove a controlled callback-time deletion failure is logged and does not escape the event-processing caller.
4. Preserve E102 event-loop ordering, E103 no-splash behavior, E104 message cleanup, E105 synchronous finish/scheduling failure semantics, E106 callback-failure containment, E107 success ordering, and normal real `QApplication` startup behavior.
5. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
6. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result and evidence

- Real-Qt proof used `QT_QPA_PLATFORM=offscreen`, a real `QApplication`, real `QTimer.singleShot(0, ...)`, and a nested `QEventLoop`. It confirmed the callback does not run until `finish_splash(...)` returns and Qt processes the queued timer.
- On the successful path, the callback invoked `deleteLater()` exactly once and did not log `Failed to delete splash after editor startup handoff`. On a controlled callback-time `deleteLater()` failure, the private adapter callback logged that warning and the exception did not escape the Qt event-processing caller.
- Result: no new product defect or E108 production-code change was demonstrated. E106's adapter-owned callback has parity under real offscreen Qt delivery; Launcher still has no QApplication callback or splash-lifecycle authority.
- Evidence: focused real-Qt proof `2 passed, 55 deselected in 0.39s`; interface suite `57 passed in 0.77s`; adjacent offscreen slice `100 passed in 1.21s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.17s`. `.venv` lacks `cryptography`, so no dependency was installed for the signature test. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E109 -- Editor Launcher Event-Loop Entry Failure Splash Cleanup Audit**. Audit a synchronous `app.exec()` entry failure after a splash has finished and its deferred deletion is successfully scheduled, preserving primary-error identity and splash-lifecycle boundaries without giving Launcher asynchronous callback authority.
