# Phase E114 -- Product Main Qt Exit-Code and Shutdown Ownership Audit

Date: 2026-07-31
Status: complete

## Previous gate

E113 passed a real offscreen `QApplication` directly to `launch_editor()`. Its actual Qt event loop delivered the adapter-owned zero-delay splash deletion callback, ended through the controlled callback-owned quit, returned `0`, and caused no Launcher-side post-loop shutdown work.

## Objective

Audit the product `main()` boundary around real Qt application construction, `launch_editor()` return-code handoff, and process-exit behavior. Prove it preserves the event-loop result and does not duplicate QApplication, splash, Kernel, or plugin shutdown behavior. Correct only a demonstrated defect.

## Required evidence

1. Map `main()`'s real QApplication construction, `launch_editor()` invocation, exit-code path, and startup-failure behavior.
2. Use deterministic seams to prove a normal launcher return becomes the correct product process result without a second application/splash/Kernel shutdown action.
3. Preserve E94 rollback distinction, E95 startup cleanup, E102--E113 application-loop and splash ownership contracts, and smoke behavior.
4. Validate relevant real offscreen application adjacency where practical.
5. Do not change Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- The audit mapped the actual boundary precisely: repository `main.py` delegates the selected `editor` entry through `FrameApi.run_product_entry(...)`; the product-version runtime `main.py`, rather than the repository root, creates `QApplication`, applies the baseline, and raises `SystemExit(launch_editor(...))`.
- A deterministic product-runtime test proved a normal `launch_editor()` return becomes the exact product `SystemExit` code after baseline application and correct project-path parsing. The runtime main neither calls application shutdown methods nor adds a second splash/Kernel lifecycle action; E94 startup diagnostics remain in the existing exception path.
- Result: no product defect or E114 production-code change was demonstrated. The plan's initial direct-root-QApplication hypothesis was disproved and corrected in the audit result; Qt ownership remains in the versioned runtime entrypoint.
- Evidence: focused E114 proof `1 passed, 14 deselected in 0.28s`; runtime-main/bootstrap slice `20 passed in 0.87s`; adjacent offscreen slice `112 passed in 1.18s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.16s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E115 -- FrameCore Root Editor Delegation Exit and Lifecycle-Unload Audit**. Verify the repository root's delegated editor `SystemExit` propagation and unconditional Frame lifecycle unload without pulling product Qt ownership upward.
