# Phase E111 -- Editor Launcher Event-Loop Return Lifecycle Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E110 used a real offscreen `QApplication`, actual zero-delay `QTimer` delivery, and a nested `QEventLoop` to confirm E109 under a controlled synchronous `app.exec()` entry failure. The original entry exception remains primary after a completed splash handoff; Launcher does not re-dismiss the splash, and the splash adapter retains deferred deletion plus callback-time exception observation.

## Objective

Audit the normal return boundary of `app.exec()`. Prove whether the event-loop return code is passed through exactly, distinguish callbacks that were delivered before return from callbacks still pending after return, and preserve the ownership rule that Launcher does not acquire post-loop splash hide, deletion, or callback-observation authority. Correct only a demonstrated lifecycle or return-value defect.

## Required evidence

1. Use deterministic application-loop doubles to prove `launch_editor()` returns the exact normal `app.exec()` return value after successful Kernel show, splash finish, and timer scheduling.
2. Cover a callback delivered while the loop is active and a callback left pending when `exec()` returns; prove that their deletion/exception observation behavior remains owned by the splash adapter rather than Launcher.
3. Prove Launcher neither calls E95 `dismiss_splash()` nor duplicates `hide()`/`deleteLater()` merely because the loop returned.
4. Where practical, validate the delivered-callback path with a real offscreen `QApplication`, actual zero-delay `QTimer.singleShot(0, ...)`, and nested `QEventLoop`.
5. Preserve E102--E110 ordering, cleanup, no-splash, startup-failure, real-application, and public-boundary contracts.
6. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher; do not alter `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, or renderer defaults.
7. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- A deterministic app double proved the exact normal `app.exec()` return code is passed through unchanged. It covered a deferred splash callback delivered during `exec()` and another left pending after `exec()` returns; each success/failure path retains the splash adapter's one-shot deletion and warning observation behavior.
- A real offscreen `QApplication`, actual zero-delay `QTimer.singleShot(0, ...)`, and nested `QEventLoop` proved the delivered-callback path under a normal app adapter return. The callback ran during the event loop, `deleteLater()` executed exactly once, and the app adapter's return code was preserved.
- In neither timing case did Launcher call E95 `dismiss_splash()` or duplicate `hide()`/`deleteLater()` after normal loop return. The pending deterministic callback remains adapter-owned and can be observed safely after Launcher has already returned.
- Result: no product defect or E111 production-code change was demonstrated. `launch_editor()` correctly delegates normal exit-code and deferred splash lifecycle behavior to their existing owners.
- Evidence: focused E111 proof `5 passed, 60 deselected in 0.48s`; interface suite `65 passed in 0.50s`; adjacent offscreen slice `108 passed in 1.48s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.22s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E112 -- Editor Launcher Post-Event-Loop Shutdown Ownership Audit**. Audit whether normal event-loop exit causes any hidden Launcher-side Kernel, plugin-host, splash, or application shutdown behavior, preserving existing lifecycle ownership and correcting only a demonstrated defect.
