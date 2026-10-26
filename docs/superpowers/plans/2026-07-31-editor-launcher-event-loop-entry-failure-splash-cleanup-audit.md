# Phase E109 -- Editor Launcher Event-Loop Entry Failure Splash Cleanup Audit

Date: 2026-07-31
Status: complete

## Previous gate

E108 proved with a real offscreen Qt event loop that E106's private splash-adapter callback deletes once on success and logs, rather than leaks, a controlled callback-time `deleteLater()` failure. Launcher remains responsible only for synchronous startup work before its final `app.exec()` handoff.

## Objective

Audit the boundary where all startup work, `splash.finish(kernel)`, and zero-delay deletion scheduling have succeeded, but `app.exec()` itself synchronously raises on entry. Determine and prove the correct primary-error identity, completed-splash cleanup semantics, and behavior of the already-scheduled callback without transferring QApplication, callback, or splash-lifecycle authority into Launcher. Correct only a demonstrated defect.

## Required evidence

1. Use a deterministic application-loop double that raises from `exec()` only after successful Kernel show, splash finish, and timer scheduling.
2. Prove the exact `exec()` exception remains primary; do not spuriously invoke E95 failed-startup dismissal after successful splash handoff unless a real lifecycle defect requires it.
3. Observe the completed splash state and the retained zero-delay callback both before and after controlled event processing; distinguish synchronous event-loop entry failure from callback-time deletion failure.
4. Preserve E102--E108 ordering and cleanup contracts, no-splash behavior, existing startup-failure cleanup, real `QApplication` startup behavior, and all public boundaries.
5. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
6. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result and evidence

- A deterministic `App.exec()` double raised only after successful splash presentation/messages, Kernel construction/load/show, `splash.finish(kernel)`, and one successful zero-delay timer schedule. The exact raised `RuntimeError` remained primary.
- The completed-splash handoff is outside Launcher's startup `try` block by design: no E95 `dismiss_splash()` call or duplicate synchronous `hide()`/`deleteLater()` occurred after the successful finish/schedule boundary. The retained adapter callback could still be delivered later and deleted exactly once without a warning.
- Result: no product defect or E109 production-code change was demonstrated. Synchronous event-loop entry failure is distinct from a pre-handoff startup failure and from callback-time deletion failure; the existing ownership split remains correct.
- Evidence: focused E109 proof `1 passed, 57 deselected in 0.39s`; interface suite `58 passed in 0.62s`; adjacent offscreen slice `101 passed in 1.49s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.19s`. `.venv` lacks `cryptography`, so no dependency was installed for the signature test. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E110 -- Editor Launcher Event-Loop Entry Failure Real-Qt Adapter Parity Audit**. Validate the E109 ownership conclusion using a real offscreen `QApplication` and actual timer delivery around a controlled event-loop entry failure without making Qt failure behavior a Launcher concern.
