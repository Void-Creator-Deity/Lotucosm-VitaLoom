# Phase E94 -- Editor Kernel Initialization-Rollback Recovery-Ownership Observability Audit

Date: 2026-07-30
Status: complete

## Previous gate

E93 found and fixed the constructor rollback reporting defect. When initialization fails and owned Project World teardown does not settle, `EditorKernel.__init__()` now raises `EditorKernelInitializationRollbackError` chained from the original startup failure. Exact capability and lease residual state remains inside the existing composition boundary; no force cleanup or alternate authority was added.

The immediate remaining question was the public startup boundary: determine whether existing application/bootstrap callers present the new error truthfully, distinguish it from an ordinary startup exception, and avoid implying that a partially constructed Kernel is a supported recovery object.

## Objective

Audit public startup-entry diagnostics and recovery-ownership presentation for `EditorKernelInitializationRollbackError`. Correct only a demonstrated truthful-reporting or ownership-boundary defect while retaining the single Editor composition root, Qt-free L0-L4 engine-plugin contracts, Project World command ownership, `.pond` semantics, and public imports.

## Required evidence

1. Map every practical EditorKernel construction entry and its exception presentation path.
2. Prove the new rollback error is distinguishable from a normal startup exception at each supported public boundary, or document the exact unsupported/internal boundary.
3. Verify diagnostics retain the chained root startup failure without exposing a partially constructed Kernel as a public recovery mechanism.
4. Add narrowly scoped regression coverage only for a demonstrated presentation/ownership defect.
5. Run focused offscreen entry/Kernel/capability tests, relevant adjacency, source/hygiene checks, root smoke, guardrails, and independent signature proof.
6. Record results, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, plugin discovery/loading, manifests, Project World commands, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not add a second Host, registry, event bus, cache, serializer, renderer, UI framework, app shell, force-cleanup path, or alternate capability authority. Do not expose a partially constructed `EditorKernel` for caller-owned recovery. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Findings and evidence

- Practical construction paths are: product `main()` -> `launch_editor()` -> `EditorKernel`; the reusable programmatic `launch_editor()` seam; and private `_run_editor_smoke()` direct construction used only by the smoke command. The product entry catches ordinary `Exception`, prints the exception text, logs its traceback, and exits one. The smoke path is an internal verification helper rather than a recovery API.
- No production correction was warranted. `EditorKernelInitializationRollbackError` already carries a distinct, truthful marker in its message (`Project World rollback did not settle`) and standard exception chaining preserves the root startup error as `__cause__`. The normal startup error remains distinguishable because it lacks that marker.
- Added a launcher-boundary regression using the real rollback-error type. `launch_editor()` propagates that exact exception and its chained cause unchanged; because construction failed, it does not load plugin layers, show a window, or enter the event loop. It returns no partially constructed `EditorKernel` and creates no recovery owner.
- Added product-entry regression coverage for both an ordinary startup failure and the real rollback-error type. `main()` reports the common startup prefix and preserves the distinction through the explicit rollback marker before exiting one. The test replaces only the launch seam, Qt application lookup, and baseline styling; it does not construct a fallback Kernel or Host.
- Evidence: focused launcher/product-entry suite `30 passed in 0.44s`; adjacent Kernel/capability/Project World/Host/startup suite `127 passed in 2.02s`; root offscreen smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all OK; independent Anaconda signature suite `2 passed in 0.23s`; source compilation passed for six relevant production/test modules; E93/E94 hunk and documentation whitespace passed. `editor_kernel.py` retains 15 pre-existing whitespace-only indented blank lines outside the E93 hunk, intentionally not reformatted because the file is untracked migration work. `.venv` lacks `cryptography`; no dependency was installed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`), not a fresh E94 run. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E95 -- Editor Launcher Initialization-Failure Splash Lifecycle Semantics Audit**. Audit splash ownership when Kernel construction or early startup fails: it must neither outlive the failed attempt nor become a recovery authority, while preserving the primary startup/rollback exception and the singular Kernel composition root.
