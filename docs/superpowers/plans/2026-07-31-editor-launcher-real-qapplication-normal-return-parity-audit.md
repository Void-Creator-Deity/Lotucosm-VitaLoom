# Phase E113 -- Editor Launcher Real-QApplication Normal-Return Parity Audit

Date: 2026-07-31
Status: complete

## Previous gate

E112 observed both splash and no-splash normal `app.exec()` returns with deterministic doubles. Launcher passed the return code through and did not access Kernel/plugin-host/Project World shutdown seams, dispose splash objects, or terminate the application after normal return. E111 had already proven real Qt timer delivery with an application adapter.

## Objective

Use an actual offscreen `QApplication` and its own `exec()` implementation to validate the normal-return path. Prove a real zero-delay splash deletion callback can run inside the real application event loop, cause a controlled normal quit, and return to the caller without transferring QApplication or splash shutdown authority into Launcher.

## Required evidence

1. Use a real offscreen `QApplication` passed directly to `launch_editor()` and actual `QTimer.singleShot(0, ...)` delivery.
2. Cause a controlled normal `QApplication.quit()` only from the adapter-owned deferred lifecycle path; prove `launch_editor()` returns the actual Qt loop exit code after one deletion.
3. Prove Launcher does not issue its own quit/close/delete/shutdown action and does not duplicate splash cleanup after `app.exec()` returns.
4. Preserve E95 and E106--E112 failure, callback, no-splash, ordering, and authority contracts.
5. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- A real offscreen `QApplication` was passed directly into `launch_editor()`. Its actual `exec()` ran the real zero-delay timer callback, the splash adapter executed `deleteLater()` exactly once, and only that adapter-owned callback scheduled the controlled `QApplication.quit()` that ended the loop.
- The real Qt event loop returned code `0` to `launch_editor()` unchanged. Launcher did not invoke splash hide, startup-failure dismissal, or Kernel shutdown after the real loop returned; a watchdog quit did not fire.
- Result: no product defect or E113 production-code change was demonstrated. E111/E112's normal-return and lifecycle-ownership conclusion now has direct `QApplication.exec()` parity evidence.
- Evidence: focused E113 proof `1 passed, 67 deselected in 0.32s`; interface suite `68 passed in 0.72s`; adjacent offscreen slice `111 passed in 1.39s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.15s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E114 -- Product Main Qt Exit-Code and Shutdown Ownership Audit**. Audit `main()`'s direct real-Qt application construction and process-exit handoff so the product boundary preserves E113 exit and lifecycle ownership without adding a second shutdown authority.
