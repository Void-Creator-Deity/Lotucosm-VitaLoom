# Phase E115 -- FrameCore Root Editor Delegation Exit and Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E114 established that the repository root does not construct Qt applications. It selects and delegates a product entry through FrameCore; the versioned runtime entry creates QApplication and forwards `launch_editor()`'s exit result as `SystemExit`. A normal return does not add runtime-main shutdown work.

## Objective

Audit the final root entrypoint boundary when the delegated editor product exits normally. Prove root `main.py` preserves the exact delegated `SystemExit` code and executes its unconditional Frame lifecycle unload exactly once, without acquiring versioned runtime Qt, splash, Kernel, plugin-host, or Project World shutdown authority.

## Required evidence

1. Execute root `main.py` under a controlled `--editor` delegation with a fake Frame API/lifecycle runner and a delegated `SystemExit` result.
2. Prove exact exit-code propagation and one lifecycle unload in the root `finally` path, including correct load/select/run ordering.
3. Prove root never creates a QApplication or triggers product runtime splash/Kernel shutdown actions.
4. Preserve E94--E114 error, return, callback, app, and ownership contracts as well as the manifest-selected version boundary.
5. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant bootstrap/offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.
## Audit result and evidence

- Root `main.py` was executed as `__main__` under controlled `--editor` delegation. The fake Frame API selected the manifest product version and raised a delegated `SystemExit(77)` from `run_product_entry(...)`; root preserved that exact code.
- The root `finally` executed one and only one `LifecycleRunner.unload_all()` after the delegated exit. The verified ordering was lifecycle runner construction, suite load, Frame API construction, plugin creation/load, version selection, product-entry delegation, then lifecycle unload.
- No root Qt construction or splash/Kernel/Host/Project World lifecycle call was introduced. Result: no product defect or E115 production-code change was demonstrated; the root stays an L0 delegation/lifecycle boundary.
- Evidence: focused E115 proof `1 passed in 0.20s`; root/runtime bootstrap slice `21 passed in 0.69s`; adjacent offscreen slice `113 passed in 1.58s`; editor smoke passed with `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, and `plugins=13/20`; project-plugin, core, GUI, and release guardrails passed; independent Anaconda signature proof `2 passed in 0.16s`. `.venv` lacks `cryptography`, so no dependency was installed. Scoped hygiene, compilation, and explicit diff verification are recorded after documentation updates.

## Next gate

Exactly one next gate: **E116 -- FrameCore Root Delegated-Entry Failure Lifecycle-Unload Audit**. Audit an unexpected delegated product-entry exception to prove root retains the exact primary failure while still unloading Frame lifecycle once, without moving runtime recovery or Qt shutdown authority upward.
