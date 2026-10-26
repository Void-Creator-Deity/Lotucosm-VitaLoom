# Phase E96 -- Editor Launcher Project-Path Startup Environment Scope Audit

Date: 2026-07-30
Status: complete

## Previous gate

E95 corrected failed-startup splash ownership. A launcher failure now dismisses its presentation without changing the primary exception, Kernel/Host/registry authority, or Project World teardown semantics.

`launch_editor(..., project_path=...)` still wrote the process-global `VITALOOM_SKIP_AUTO_OPEN=1` before Kernel construction. Its scope across constructor failure, plugin-load failure, event-loop return, and later same-process programmatic launches had not been proven.

## Objective

Audit the ownership and observable behavior of the `VITALOOM_SKIP_AUTO_OPEN` mutation on the Editor Launcher `project_path` path. Correct only a demonstrated state-leak defect while retaining the singular Editor composition root, Project World ownership, runtime capability contracts, `.pond` semantics, plugin loading behavior, public imports, and legacy Qt adapter role.

## Required evidence

1. Map every launcher and Kernel read/write of `VITALOOM_SKIP_AUTO_OPEN`, including timing relative to splash, construction, explicit `set_startup_project()`, plugin load, show, and event-loop entry/return.
2. Reproduce `project_path` constructor failure and early plugin-load failure with deterministic seams; prove the original environment value is either preserved/restored or document the intentional contract.
3. Reproduce a later same-process launcher call after a `project_path` call and prove it does not inherit an unintended skip-auto-open state.
4. Preserve the primary exception object/chaining and avoid making the launcher a Project World recovery or cleanup authority.
5. Run focused offscreen tests, adjacency, source/hygiene checks, root smoke, guardrails, and independent signature proof.
6. Record results, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, Project World commands, Inspector binding, SR2D, Player/export, manifests, plugin discovery/loading contracts, public imports, MRO, or capability authority. Do not introduce a second Host, registry, event bus, fallback Kernel, force-cleanup path, application shell, renderer, cache, serializer, or UI framework. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- The process-global mutation was a real defect. `editor_launcher.launch_editor()` set `VITALOOM_SKIP_AUTO_OPEN=1` before `EditorKernel` construction, overwriting a caller-owned value and leaving `1` in the interpreter after a successful project-path launch or an early failure.
- The actual project-path ownership path is already instance-scoped: Launcher calls `kernel.set_startup_project(os.path.abspath(project_path))`; `EditorKernel` keeps `_startup_project_path`; its delayed post-plugin callback opens a valid explicit project through the configured Project World session Host before falling back to `open_last_project_on_startup()`. The only remaining environment-variable consumer is the legacy Project Manager fallback path.
- The narrow correction removes only Launcher?s global environment write. The `os` import remains solely for explicit absolute-path normalization. No Project World, Host, registry, event bus, fallback Kernel, recovery controller, or cleanup authority was added.
- Three deterministic regressions first demonstrated the leak and then pass: a successful project-path launch does not affect a later same-process launch; a constructor failure neither writes nor leaves the variable and preserves the exact raised object; a plugin-load failure preserves the caller?s `caller-managed` value and the exact raised object.
- Evidence: focused `tests/test_runtime_capability_registry_interface.py` `24 passed in 2.29s`; adjacent offscreen suite `130 passed in 6.04s`; root offscreen smoke reports `plugins=13/20`; project-plugin/core/GUI/release guardrails all report `OK`; independent Anaconda signature suite `2 passed in 0.28s`; scoped compilation and trailing-whitespace checks passed for `editor_launcher.py` and the focused test file, both with CRLF-only line endings.
- Environment/fallback: verification used `.venv\python.exe -B`, `QT_QPA_PLATFORM=offscreen`, and `PYTHONDONTWRITEBYTECODE=1`. `.venv` lacks `cryptography`, so the already provisioned `D:\app\anaconda3\python.exe` ran the signature proof; no dependency was installed. A restricted existing `.pytest-e53-dock` directory rejected broad recursive PowerShell enumeration; the deterministic fallback used `rg --files`/known guard scripts and all four guardrails completed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`), not a fresh E96 run. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E97 -- Editor Kernel Deferred Project-Path Startup Semantics Audit**. Audit the instance-scoped handoff from Launcher to the delayed post-plugin callback: valid explicit project precedence, absent/invalid explicit-path fallback, callback scheduling, and failure containment. Correct only a proven semantic or timing defect without returning environment, Project World, Host, registry, or UI-host authority to Launcher.
