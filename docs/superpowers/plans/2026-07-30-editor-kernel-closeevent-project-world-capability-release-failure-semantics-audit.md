# Phase E92 -- Editor Kernel CloseEvent Project World Capability Release Failure Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E91 closed the preceding Qt close-event boundary. After a settled nested Plugin Host shutdown, a failed exact Plugin Host capability release causes `EditorKernel.closeEvent()` to reject the close, retain the exact active lease and published Host, and accept only after a later successful retry. The proof uses a real publication lease and an isolated registry; no forced teardown or second authority exists.

The next contiguous segment is `_release_project_world_host_lease()` after Plugin Host unpublication: it unregisters the Kernel's Project World capabilities, then releases the Project World composition lease. Audit whether failures in either operation truthfully prevent the window from accepting, retain only the correct retryable ownership state, and preserve Project World command ownership and later replacement safety.

## Objective

Audit `EditorKernel.closeEvent()` at the Project World capability-removal and composition-lease-release boundary. Correct only a demonstrated close/retry, exact-unpublication, or error-reporting defect while preserving the single composition root, public capability contracts, `.pond` semantics, and Qt-free L0-L4 engine-plugin contracts.

## Required evidence

1. Map the post-Plugin-Host teardown order: Project World capability removal, Project World composition-lease release, and Qt event acceptance.
2. Reproduce a Project World capability-removal failure at `closeEvent()` with public/lifecycle doubles; prove `event.ignore()`, no acceptance, no hidden force path, and valid retry state.
3. Reproduce a Project World composition-lease release failure after successful capability removal; prove correct residual state and a later settled retry without resurrecting stale capability authority.
4. Prove existing Project World command ownership, later replacement safety, nested Host shutdown gate, and legacy Adapter behavior remain intact.
5. Run focused offscreen Kernel-close/capability/Project World tests, relevant adjacent Host tests, source compilation/whitespace, guardrails, root smoke, and independent signature proof.
6. Record evidence, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, plugin discovery/loading, package manifests, Project World commands, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not create a Host, registry, event bus, cache, serializer, renderer, UI framework, app shell, force-close path, or alternate capability authority. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Findings and evidence

- The verified close teardown order after a settled nested Plugin Host shutdown is: exact Plugin Host publication release, exact Project World capability unregistration, Project World composition-lease release, then Qt `event.accept()`.
- Added an isolated real-close regression for Project World capability-unregistration failure. The first exception reaches the established error path and `event.ignore()`; the exact capability map and composition lease remain owned and retryable, with no lease release or forced close. A later settled retry unregisters the same capability, releases the lease, and accepts.
- Added an isolated real-close regression for Project World composition-lease release failure after capability unpublication. Exact unpublication removes the still-owned capability, preserves a later replacement, clears only the stale ownership map, retains the failing lease, and never resurrects a capability. A later retry releases that same lease and accepts.
- No production correction was warranted: `_release_project_world_host_lease()` already preserves the correct residual state in both failure modes. The regressions use only an isolated `InMemoryRuntimeCapabilityRegistry` and lifecycle doubles; they do not create a second runtime authority.
- Evidence: focused close suite `9 passed in 0.19s`; adjacent Kernel/capability/Project World/Host suite `101 passed in 1.76s`; root offscreen smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all OK; independent Anaconda signature suite `2 passed in 0.17s`; scoped source compilation and changed-file whitespace passed. `.venv` still lacks `cryptography`; no dependency was installed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`). QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E93 -- Editor Kernel Initialization-Rollback Project World Teardown Failure Semantics Audit**. Audit the constructor-exception rollback path that invokes the same release boundary after partial composition, and prove it cannot silently leave stale public capability or composition ownership behind when teardown itself fails.