# Phase E91 -- Editor Kernel CloseEvent Plugin-Host Capability Release Failure Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E90 closed the Editor Kernel composition-root audit. The Kernel publishes exactly one recursive `NestedPluginHost` through `PLUGIN_HOST_CONTROL_OBSERVATION`, legacy consumers resolve that public capability rather than `PluginLoader` internals, and the E13 lease keeps last-writer-wins exact-unpublication semantics. A publication-release exception retains the exact lease and is retryable; no predecessor stack or second Host authority is permitted.

The remaining adjacent lifecycle boundary is `EditorKernel.closeEvent()`: after a settled nested Host shutdown it calls `_release_project_world_host_lease()`, which includes Plugin Host capability unpublication. Audit whether a failed exact release truthfully blocks close, preserves retryable state, and cannot accept a window while its published Host authority remains active.

## Objective

Audit EditorKernel's actual Qt close-event handling for Plugin Host capability-release failures. Correct only a demonstrated close/retry or error-reporting defect while preserving shutdown order, Project World ownership, public capability resolution, and the Qt-free L0-L4 engine contracts.

## Required evidence

1. Map `closeEvent()` ordering from layout/runtime-capability cleanup, nested Host shutdown, Plugin Host capability unpublication, Project World capability removal, and composition lease release.
2. Reproduce a failed Plugin Host publication release at the close-event boundary with public/lifecycle doubles; prove the event is ignored, no acceptance occurs, and exact retry state remains.
3. Prove a subsequent normal close retry only succeeds after the nested Host has settled and the exact lease has released; preserve later replacement safety and do not add a force path.
4. Run focused offscreen Kernel-close/capability/Project World tests, relevant adjacent Host tests, source compilation/whitespace, guardrails, root smoke, and independent signature proof.
5. Record evidence, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, plugin discovery/loading semantics, package manifests, Project World commands, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not create a Host, registry, event bus, cache, serializer, renderer, UI framework, app shell, forced shutdown path, or alternate capability authority. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Delivery and evidence

- E91 mapped the real close sequence: optional dirty-project flush; layout persistence and viewport runtime-capability cleanup; the sole `PluginLoader.shutdown_plugins()` authority; exact Plugin Host capability unpublication; Project World capability removal and composition-lease release; finally `event.accept()`. Every failure before acceptance reports an error and calls `event.ignore()`.
- Added an isolated lifecycle proof in `tests/test_editor_kernel_close_shutdown.py`. It publishes one protocol-complete public Host double through a real exact-object `CapabilityPublicationLease`, makes the first release raise, and drives `EditorKernel.closeEvent()` through a settled shutdown report. The first close is ignored, has no acceptance, retains the exact active lease and published Host, and does not force Project World release. A second settled close retries the same lease, unpublishes the exact capability, and only then accepts.
- The first test version used the process-wide `EditorContext` before the test module's `QApplication` fixture. That made later Qt-backed tests observe the known uninitialized-QObject singleton state. The proof was corrected to use an isolated `InMemoryRuntimeCapabilityRegistry`; this is test isolation only, not a production lifecycle change, and it preserves the one-Host/one-registry authority rule.
- No production correction was warranted: the existing `closeEvent()` already fail-closes correctly when `_release_project_world_host_lease()` returns `False`, and the helper retains the failing Plugin Host publication lease for a deterministic retry.
- Evidence: final focused E91 close suite `7 passed in 0.19s`; Kernel/capability/Project World/Host adjacency `99 passed in 2.62s`; root offscreen smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all `OK`; independent package-signature proof `2 passed in 0.28s` through `D:\app\anaconda3\python.exe`. Scoped source compilation covered four Python files; changed-file whitespace was clean. `docs/mainline_status.md` has two pre-existing historical trailing-whitespace lines (2020-2021), deliberately left untouched.
- Environment truth: `.venv` still lacks `cryptography`; no dependency was installed. E68 remains the older broad proof (`1678 passed, 34 skipped, 34 subtests`; regular/eager smokes `13/20`/`20/20`). QPainter remains the default UI renderer; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

E92 -- Editor Kernel CloseEvent Project World Capability Release Failure Semantics Audit. Audit the next exact teardown segment after successful Plugin Host unpublication: Project World capability removal and composition-lease release must block window acceptance on failure, retain correct retry state, and preserve Project World command ownership.
