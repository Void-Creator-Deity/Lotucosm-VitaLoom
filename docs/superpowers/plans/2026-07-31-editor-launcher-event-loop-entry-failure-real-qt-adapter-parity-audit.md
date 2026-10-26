# Phase E110 -- Editor Launcher Event-Loop Entry Failure Real-Qt Adapter Parity Audit

Date: 2026-07-31
Status: complete

## Previous gate

E109 proved deterministically that a synchronous `app.exec()` entry exception occurs after completed splash handoff: it remains the exact primary exception, does not trigger E95 failed-startup dismissal, and leaves the adapter-owned zero-delay callback available for later delivery. No production correction was required.

## Objective

Use a real offscreen Qt application and actual zero-delay timer delivery to validate the E109 lifecycle boundary around a controlled event-loop entry failure. Prove that the splash adapter, rather than Launcher, retains deferred deletion and callback-time observation authority even when an application adapter's `exec()` method raises synchronously. Correct only a demonstrated parity gap.

## Required evidence

1. Use a real offscreen `QApplication` plus actual `QTimer.singleShot(0, ...)`/`QEventLoop` delivery, with a controlled application adapter that raises only at `exec()` entry.
2. Prove the exact entry failure remains primary after successful `finish_splash(...)` scheduling and that Launcher does not invoke E95 dismissal or duplicate deletion.
3. Prove the retained real timer callback can subsequently deliver exactly once; cover both successful deletion and controlled callback-time deletion failure observation where practical.
4. Preserve E102--E109 ordering, cleanup, no-splash, real-application, and public-boundary contracts.
5. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
6. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- A real offscreen `QApplication`, actual `QTimer.singleShot(0, ...)`, and nested `QEventLoop` delivered the retained splash-adapter callback after a controlled app adapter raised synchronously from `exec()` entry. The exact entry `RuntimeError` remained the primary raised object.
- Both real-timer paths preserve the completed-handoff ownership split. On success, `deleteLater()` runs exactly once; with a controlled callback-time deletion failure, the splash adapter logs `Failed to delete splash after editor startup handoff` and the error does not escape Qt event processing. Launcher never invokes E95 `dismiss_splash()` and performs no duplicate `hide()` or deletion.
- Result: no product defect or E110 production-code change was demonstrated. This confirms E109 under actual Qt timer delivery: Launcher owns synchronous startup only; the splash adapter owns deferred deletion and callback-time observation.
- Evidence: focused real-Qt proof `2 passed, 58 deselected in 0.50s`; interface suite `60 passed in 0.81s`; adjacent offscreen slice `103 passed in 1.55s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.17s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E111 -- Editor Launcher Event-Loop Return Lifecycle Boundary Audit**. Audit normal `app.exec()` return-code propagation and the lifecycle/observation boundary between callbacks delivered before return and callbacks that remain pending afterward, without granting Launcher splash shutdown authority.
