# Phase E93 -- Editor Kernel Initialization-Rollback Project World Teardown Failure Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E92 closed the real Qt close-event path through Project World teardown. After nested Plugin Host shutdown settles, Project World capability unregistration and composition-lease release each fail closed: close is ignored, no stale authority is resurrected, and the exact residual fact is retryable. No production correction was required.

`EditorKernel.__init__()` also invokes `_release_project_world_host_lease()` from its broad constructor-exception handler after partial composition. That rollback path has no Qt close event and previously re-raised only the constructor failure even when its owned Project World teardown did not settle. This gate audited whether that distinct failure fact was truthfully composed with the startup failure while retaining the same exact capability and lease semantics.

## Objective

Audit Editor Kernel initialization rollback when Project World capability unregistration or Project World composition-lease release fails after partial composition. Correct only a demonstrated reporting, exact-unpublication, ownership, or retry-semantics defect while preserving the single Editor composition root, Qt-free L0-L4 engine-plugin contracts, Project World command ownership, `.pond` semantics, and existing public imports.

## Required evidence

1. Map the constructor publication/acquisition order, exception boundary, rollback release order, and exception propagation.
2. Reproduce a rollback where exact Project World capability unregistration fails; prove no hidden force cleanup or second authority, and determine the observable exception plus residual ownership state.
3. Reproduce a rollback where composition-lease release fails after exact capability unpublication; prove later-replacement safety, absence of capability resurrection, and truthful residual ownership facts.
4. Verify successful rollback, public Plugin Host publication semantics, Project World command ownership, and close-event behavior remain unchanged.
5. Run focused offscreen Kernel/capability/Project World tests, relevant adjacent tests, source compilation/whitespace, guardrails, root smoke, and independent signature proof.
6. Record results, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, plugin discovery/loading, manifests, Project World command APIs, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not create a Host, registry, event bus, cache, serializer, renderer, UI framework, app shell, force-cleanup path, or alternate capability authority. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Findings and evidence

- The constructor publishes the exact Plugin Host observation capability, acquires the Project World composition lease and its owned capability map, then initializes transport/coordinator. Its broad exception boundary releases the exact Plugin Host publication first, then exact Project World capabilities, then the Project World composition lease.
- A real reporting defect existed: `_release_project_world_host_lease()` returned `False` after a Project World cleanup failure, but `EditorKernel.__init__()` ignored that result and re-raised only the startup exception. The caller therefore could not distinguish a settled startup failure from a startup failure whose owned Project World rollback remained incomplete.
- Added `EditorKernelInitializationRollbackError`. When the release boundary does not settle, construction raises this explicit error and chains the original startup exception as `__cause__`; existing `logger.exception` records the concrete failed cleanup. When rollback settles, the original startup exception remains the raised exception unchanged.
- Added isolated constructor rollback coverage for both residual states. A capability-unregistration failure retains the exact owned capability map and composition lease for retry, while public Plugin Host publication is released. A composition-lease failure after exact unpublication clears only the owned capability map, retains the failing lease, preserves a later registry replacement, and never resurrects stale authority. Both residual states can settle on a later explicit retry in the regression harness.
- No force cleanup, second Host, second registry, fallback authority, or Qt-close behavior change was introduced. Project World command ownership and exact unpublication semantics remain in the existing Project World lease boundary.
- Evidence: focused constructor rollback suite `8 passed in 0.48s`; close-event regression suite `9 passed in 0.20s`; adjacent Kernel/capability/Project World/Host suite `103 passed in 2.29s`; root offscreen smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all OK; independent Anaconda signature suite `2 passed in 0.16s`. Source compilation passed for `editor_kernel.py`, `project_world_capabilities.py`, and both affected test modules. E93 hunk and documentation files have no trailing whitespace. `editor_kernel.py` retains 15 pre-existing whitespace-only indented blank lines outside the E93 hunk, intentionally not reformatted because the file is untracked migration work. `.venv` lacks `cryptography`; no dependency was installed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`), not a fresh E93 run. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E94 -- Editor Kernel Initialization-Rollback Recovery-Ownership Observability Audit**. Audit the public startup boundary and diagnostic presentation of `EditorKernelInitializationRollbackError` so callers can distinguish a normal startup exception from an incomplete owned rollback without exposing a recoverable internal object, adding fallback authority, or changing lifecycle ownership.
