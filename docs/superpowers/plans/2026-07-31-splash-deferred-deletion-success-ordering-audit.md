# Phase E107 -- Splash Deferred-Deletion Success and Ordering Audit

Date: 2026-07-31
Status: complete

## Previous gate

E106 corrected a demonstrated asynchronous observation gap: after successful `QTimer.singleShot(0, ...)` scheduling, a callback-time `splash.deleteLater()` error is caught and logged by a private splash-adapter callback. Launcher still owns only synchronous startup failures before its `app.exec()` handoff.

## Objective

Audit the successful side of the corrected deferred-deletion callback. Establish deterministic proof that the splash adapter schedules exactly one zero-delay callback after `splash.finish(widget)`, does not delete the splash before the successful Launcher `app.exec()` handoff, deletes exactly once when the callback runs, and does not issue the E106 warning on success. Correct only a demonstrated gap while retaining splash-adapter ownership of deferred cleanup.

## Required evidence

1. Use a deterministic scheduler double to separately observe scheduling, successful `app.exec()` handoff, and later callback execution.
2. Prove finish-before-schedule ordering, one zero-delay schedule, no pre-handoff delete, exactly one successful callback delete, and no warning.
3. Preserve E102 event-loop ordering, E103 no-splash behavior, E104 message cleanup, E105 synchronous finish/scheduling failure semantics, E106 callback-failure logging, and real `QApplication` behavior.
4. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
5. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Success map: after `splash.finish(kernel)`, the splash adapter invokes `QTimer.singleShot(0, ...)` once. Its callback remains deferred while Launcher enters and returns from its final `app.exec()` call; the callback only then invokes `splash.deleteLater()`.
- Proof: a deterministic scheduler double recorded one callback and asserted the zero delay. A successful `app.exec()` double returned before callback execution, proving no pre-handoff deletion. Manually running the retained callback produced exactly one deletion and no `Failed to delete splash after editor startup handoff` warning.
- Result: no new product defect was demonstrated. E106's private callback preserves the original successful asynchronous cleanup ordering while providing failure observation. No production code changed in E107.
- Evidence: focused E105/E106/E107 proof `3 passed, 52 deselected in 0.22s`; registry/event-bus interface `55 passed in 0.57s`; offscreen adjacent slice `98 passed in 1.18s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.17s`. Scoped hygiene, compilation, and diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E108 -- Splash Deferred-Deletion Real-Qt Event-Loop Parity Audit**. Exercise the adapter's deferred success and callback-failure paths using a real offscreen `QApplication` event cycle to confirm that the deterministic scheduler proofs match Qt callback execution without moving lifecycle authority into Launcher.