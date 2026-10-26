# Phase E95 -- Editor Launcher Initialization-Failure Splash Lifecycle Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E94 proved that `launch_editor()` propagates an incomplete-Kernel-rollback error and its root cause unchanged, without loading plugins, showing a partial Kernel, entering the event loop, or exposing a recovery object. Product `main()` preserves the explicit rollback marker in its startup diagnostic.

`launch_editor()` may create a splash before it constructs the Kernel. The adjacent remaining lifecycle question is whether a constructor or early-startup exception leaves that presentation object visible or otherwise authoritative after the launch has failed.

## Objective

Audit splash-screen ownership and release semantics at the Editor Launcher initialization-failure boundary. Correct only a demonstrated presentation-lifecycle or primary-error-preservation defect while retaining the singular Editor composition root, Qt-free L0-L4 engine-plugin contracts, Project World ownership, `.pond` semantics, and public imports.

## Required evidence

1. Map splash acquire/message/finish order relative to Kernel construction, plugin loading, show, and event-loop entry.
2. Reproduce Kernel-constructor failure and early plugin-load failure with a real/deterministic splash double; prove exact splash residual state and primary-exception behavior.
3. Verify an incomplete Project World rollback error remains distinguishable and chained after launcher presentation cleanup.
4. Verify no partial Kernel becomes a recovery object and no Host/registry/fallback authority is created.
5. Run focused offscreen launcher/Kernel tests, adjacency, source/hygiene checks, root smoke, guardrails, and independent signature proof.
6. Record results, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, plugin discovery/loading contracts, manifests, Project World commands, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not add a second Host, registry, event bus, cache, serializer, renderer, UI framework, app shell, force-cleanup path, or alternate capability authority. Do not turn the splash into a recovery controller. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- A defect was reproduced with deterministic splash doubles: launcher created and messaged splash before Kernel construction, yet constructor and early `load_plugins_layered()` failures had no release path. The failed presentation could remain visible.
- The narrow correction is presentation-only. `dismiss_splash()` calls `hide()` synchronously and `deleteLater()` for the Qt object. `launch_editor()` wraps only its initialization path, invokes that helper while unwinding an `Exception`, logs a cleanup failure, and uses bare re-raise so the primary error object and its existing exception chain are unchanged.
- Regression coverage proves successful order (`show splash -> messages -> construct -> load -> show Kernel -> finish splash -> exec`), constructor failure cleanup without plugin/event-loop progress, plugin-load failure cleanup without showing the local Kernel, and exact preservation of `EditorKernelInitializationRollbackError` plus `__cause__` when splash cleanup itself raises. The splash never becomes a recovery controller; no force cleanup, alternate Host/registry, fallback Kernel, or unrelated contract change was introduced.
- Evidence: focused `21 passed in 0.42s`; adjacency `132 passed in 2.03s`; root offscreen smoke `plugins=13/20`; all four guardrails passed; E95 compile/whitespace checks passed for three files; signature proof `2 passed in 0.18s` through `D:\app\anaconda3\python.exe`. `.venv` lacks `cryptography`; no dependency was installed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`), not a fresh run. QPainter remains default and OpenGL/native acceleration is not default-ready.

## Next gate

Exactly one next gate: **E96 -- Editor Launcher Project-Path Startup Environment Scope Audit**. Audit whether `VITALOOM_SKIP_AUTO_OPEN` leaks across failed or later same-process programmatic launches, and correct only a proven scope/rollback defect without changing Project World, plugin, registry, manifest, or UI-host authority.

