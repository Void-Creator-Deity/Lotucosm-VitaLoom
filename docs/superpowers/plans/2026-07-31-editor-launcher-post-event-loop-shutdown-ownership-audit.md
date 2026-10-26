# Phase E112 -- Editor Launcher Post-Event-Loop Shutdown Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E111 proved that normal `app.exec()` return-code propagation is exact and that a deferred splash callback may be delivered during the loop or remain pending afterward without moving lifecycle authority to Launcher. The real offscreen Qt path delivered the callback within a nested event loop and returned the app adapter's code unchanged.

## Objective

Audit the post-event-loop boundary for hidden or accidental Launcher-side shutdown behavior. Determine whether normal event-loop return causes Launcher to close the splash, tear down the Kernel, unload plugins, mutate Project World state, or dispose the application, and prove that any such behavior remains with its existing owner unless a demonstrated defect requires a narrow correction.

## Required evidence

1. Use deterministic doubles to observe the entire normal `launch_editor()` path through a successful `app.exec()` return and record any Kernel, plugin-host, splash, or application shutdown calls.
2. Prove that the return code remains exact while Launcher does not introduce duplicate or premature shutdown work after `app.exec()` returns.
3. Preserve the E95 pre-handoff cleanup and E106--E111 deferred callback observation rules, including no-splash behavior.
4. Verify relevant real offscreen Qt adjacency where practical without making a `QApplication` lifecycle concern an engine or Launcher authority.
5. Preserve E102--E111 ordering, cleanup, public-boundary, project/recovery, manifest, `.pond`, AI command, Inspector binding, SR2D, and renderer-default contracts.
6. Do not move QApplication, splash, Kernel, Host, Project World, runtime-service, bundle-path, recovery, or environment ownership into Launcher.
7. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Deterministic normal-return coverage observed both splash and no-splash launch paths through `app.exec()` return. The exact return code was preserved, and Launcher did not call splash hide/close/shutdown/delete, Kernel close/shutdown/delete, plugin-host or Project World access, or application quit/close/shutdown/delete methods.
- The splash path deliberately left its zero-delay callback pending at the return boundary; no post-return cleanup was invented by Launcher. E106--E111 remain the owner and observation contract for that callback, while the no-splash path has no accidental lifecycle operation.
- Result: no product defect or E112 production-code change was demonstrated. Normal application shutdown remains outside Launcher rather than becoming a second Kernel, plugin-host, splash, Project World, or QApplication lifecycle authority.
- Evidence: focused E112 proof `2 passed, 65 deselected in 0.34s`; interface suite `67 passed in 0.66s`; adjacent offscreen slice `110 passed in 1.22s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.16s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E113 -- Editor Launcher Real-QApplication Normal-Return Parity Audit**. Use a real offscreen `QApplication.exec()` normal exit to confirm E111/E112 return and deferred-deletion ownership without making Qt application shutdown a Launcher concern.
