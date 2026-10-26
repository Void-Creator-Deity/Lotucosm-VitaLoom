# Phase E105 -- Editor Launcher Splash-Finish Failure Cleanup Audit

Date: 2026-07-31
Status: complete

## Previous gate

E104 established that the existing outer Launcher startup boundary already handles every existing-splash `splash_message(...)` failure: each message rendering/event-processing exception remains primary, invokes E95 dismissal exactly once, and prevents further startup work or `app.exec()`.

## Objective

Audit Launcher handling of `finish_splash(...)` after `kernel.show()`. Map failures raised by the immediate `splash.finish(widget)` step and the deferred-delete scheduling path to prove whether E95 cleanup preserves the primary exception, dismisses at most once, suppresses event-loop entry, and leaves the shown Kernel/splash lifecycle ownership coherent. Correct only a demonstrated gap without moving QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment authority into Launcher.

## Required evidence

1. Map successful and failing `finish_splash(...)` placement relative to `kernel.show()` and `app.exec()`.
2. Reproduce immediate finish and deferred-delete scheduling failures with exact primary-error identity, dismissal count, and no event-loop entry.
3. Preserve E102 `exec()` ordering, E103 conditional no-splash behavior, E104 message-failure semantics, E95 cleanup-warning behavior, and valid real `QApplication` behavior.
4. Do not create, own, cache, replace, close, or globally type-check QApplication or splash objects; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, renderer defaults, or project opening/recovery.
5. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Completion map: `finish_splash(...)` is called only after `kernel.show()` and before the final E102 `app.exec()` handoff. It immediately calls `splash.finish(kernel)`, then schedules `splash.deleteLater` through `QTimer.singleShot(0, ...)`. No-splash paths do not reach either operation.
- Failure proof: deterministic coverage reproduces an immediate `splash.finish(...)` error and a `QTimer.singleShot(...)` scheduling error. Both preserve the exact primary exception, call the existing E95 `dismiss_splash(...)` once, synchronously invoke hide/delete cleanup, and prevent `app.exec()`. The finish error correctly prevents any deferred scheduling; the scheduling error occurs only after the Kernel is shown and the splash has finished.
- Cleanup proof: when dismissal itself raises after an immediate finish error, the original finish exception remains primary and the existing `Failed to dismiss splash after editor startup failure` warning is recorded.
- Result: no product defect was demonstrated. The existing outer Launcher startup boundary is the correct owner for failures synchronously raised by its `finish_splash(...)` call. No product code changed, and no Qt, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment authority moved.
- Evidence: focused characterization proof `3 passed, 50 deselected in 0.38s`; registry/event-bus interface `53 passed in 0.62s`; offscreen adjacent slice `96 passed in 1.17s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.17s`. Scoped hygiene, compilation, and diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E106 -- Splash Deferred-Deletion Callback Failure Observation Audit**. Audit the post-scheduling `deleteLater` callback boundary owned by the splash adapter: distinguish synchronous schedule failures from callback-time failures and establish deterministic observation/logging semantics without making Launcher own Qt event-loop or splash lifetime.