# Phase E104 -- Editor Launcher Splash-Message Failure Cleanup Audit

Date: 2026-07-31
Status: complete

## Previous gate

E103 established the splash adapter's conditional `processEvents()` protocol boundary: the no-splash environment branch stays capability-free, invalid event processing cannot create a splash, and presentation-time failures dismiss a constructed splash while preserving the primary exception.

## Objective

Audit Launcher calls to `splash_message(...)` after a splash already exists. Map `showMessage(...)` and `app.processEvents()` failures at the initial, plugin-loading, and restore-status messages to prove whether E95's Launcher cleanup dismisses exactly once and preserves the original error. Correct only a demonstrated gap without moving Qt, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment authority into Launcher.

## Required evidence

1. Map all three Launcher message sites and their existing-splash/no-splash reachability.
2. Reproduce message rendering and message event-processing failures with exact primary-exception identity, dismissal count, and no entry into Kernel/plugin work when failure occurs early.
3. Preserve E102 `exec()` ordering, E103 no-splash protocol behavior, E95 cleanup-warning behavior, and valid real `QApplication` behavior.
4. Do not create, own, cache, replace, close, or globally type-check QApplication or splash objects; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, renderer defaults, or project opening/recovery.
5. Run focused red/green proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Call map: Launcher calls `splash_message(...)` only after `show_vitaloom_splash(...)` has returned a non-`None` splash. The messages occur (1) before Kernel construction, (2) after construction but before plugin-layer resolution/loading, and (3) after plugins load but before `kernel.show()`. Both `use_splash=False` and the E103 `VITALOOM_NO_SPLASH` branch leave all three sites unreachable.
- Failure proof: six deterministic cases cover `showMessage(...)` and `app.processEvents()` failure at each of those three sites. In every case, the exact primary exception object escapes, Launcher invokes E95 `dismiss_splash(...)` exactly once, and `app.exec()` is not reached. The initial failure constructs neither Kernel nor plugin layers; the plugin-loading failure never resolves layers; the restore-status failure never shows the Kernel or finishes the splash.
- Cleanup proof: an initial message-rendering error with a failing `dismiss_splash(...)` retains its exact primary error and logs the existing `Failed to dismiss splash after editor startup failure` warning. This proves the E95 cleanup-warning rule applies to message failures too.
- Result: no product defect was demonstrated. `splash_message(...)` intentionally renders/events only; the existing outer Launcher startup `try` owns exactly-once cleanup after its successfully-returned splash. No Qt, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment authority moved, and no production code changed.
- Evidence: focused characterization proof `7 passed, 43 deselected in 0.32s`; registry/event-bus interface `50 passed in 0.68s`; offscreen adjacent slice `93 passed in 1.32s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.18s`. Scoped hygiene, compilation, and diff verification are recorded after the documentation update.

## Next gate

Exactly one next gate: **E105 -- Editor Launcher Splash-Finish Failure Cleanup Audit**. Audit `finish_splash(...)` failures after Kernel presentation for exact primary-error identity, dismissal count, event-loop suppression, and deferred-deletion semantics without granting Launcher splash or application lifecycle authority.