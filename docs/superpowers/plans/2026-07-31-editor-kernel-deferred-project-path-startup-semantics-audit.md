# Phase E97 -- Editor Kernel Deferred Project-Path Startup Semantics Audit

Date: 2026-07-31
Status: complete

## Previous gate

E96 removed an incorrect process-global `VITALOOM_SKIP_AUTO_OPEN` write from `launch_editor(..., project_path=...)`. The launcher now passes the normalized explicit project only through `EditorKernel.set_startup_project()`, preserving caller environment ownership and startup-error identity.

The remaining adjacent question was the deferred Kernel behavior after layered plugins load: `_schedule_post_plugin_init()` invokes `_try_open_last_project_on_startup()` after layout restoration, where a valid pending project should take precedence and missing/invalid input reaches the existing Host fallback.

## Objective

Audit the instance-scoped project-path handoff from Launcher to Editor Kernel's deferred post-plugin callback. Correct only a demonstrated precedence, invalid-path, duplicate-scheduling, or failure-containment defect while preserving the singular Editor Kernel, Project World session Host, runtime capability registry, `.pond` semantics, plugin lifecycle, and legacy Qt UI-host adapter boundary.

## Required evidence

1. Map `set_startup_project()`, `_schedule_post_plugin_init()`, and `_try_open_last_project_on_startup()` relative to layered plugin completion, layout restoration, Host resolution, and event-loop entry.
2. Prove a valid explicit project with `project.json` opens once through the configured Project World session Host and does not fall back to the last-project path.
3. Prove absent and invalid explicit paths preserve the intentional Host fallback behavior without using or modifying process environment state.
4. Prove callback scheduling remains singular per real load invocation, preserves layout-before-project ordering, and does not create a second Kernel/Host/registry authority.
5. Prove a Host exception remains contained by the existing Kernel startup warning path, with no invented recovery object or Launcher-owned cleanup.
6. Run focused offscreen tests, adjacency, source/hygiene checks, root smoke, guardrails, independent signature proof, and record all skips/blockers plus exactly one next gate.

## Explicit non-goals

Do not change `.pond`, Project World command ownership, Inspector binding, AI command registry, SR2D, Player/export, plugin discovery/loading contracts, manifests, public imports, MRO, renderer choice, or application shell. Do not restore a global environment flag; add a second Host, registry, event bus, fallback Kernel, force cleanup, recovery controller, cache, serializer, renderer, or UI framework. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- No production correction was warranted. `set_startup_project()` owns normalized pending-path state; `load_plugins_layered()` finishes the existing Host loader before it schedules the post-plugin callback; and the callback restores/applies layout before it delegates project startup through the configured Project World session Host.
- E97 adds deterministic coverage that the callback is scheduled exactly once for its invocation and does not run synchronously; after the timer fires, layout restoration/defaulting happens before project startup. A valid explicit directory containing `project.json` calls `open_project()` exactly once and never calls the last-project fallback. An absent path or a directory without `project.json` calls only the established fallback. An explicit-project Host exception is logged and contained by the existing Kernel startup path and does not trigger a second fallback attempt.
- These observations retain the singular Kernel/Host/registry boundary and the E96 caller-owned environment contract. No global environment mutation, fallback Kernel, second Host, registry, event bus, recovery owner, or Launcher cleanup path was added.
- Evidence: focused `tests/test_editor_kernel_restore_timing.py` `5 passed in 0.28s`; adjacent offscreen suite `135 passed in 3.60s`; root smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all report `OK`; independent Anaconda signature suite `2 passed in 0.27s`.
- Hygiene: scoped compilation passed for `editor_kernel.py` and `test_editor_kernel_restore_timing.py`; the changed test has CRLF-only line endings and no trailing whitespace. The unchanged legacy `editor_kernel.py` has pre-existing mixed line endings (455 bare LF) and 15 pre-existing trailing-whitespace lines, so it was not reformatted as part of this semantic audit. `.venv` lacks `cryptography`; signature proof used existing `D:\app\anaconda3\python.exe` and no dependency was installed. E68 remains historical broad proof (`1678 passed, 34 skipped, 34 subtests`), not a fresh E97 run. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E98 -- Editor Kernel Explicit Startup-Project Consumption Semantics Audit**. Audit whether a pending explicit project remains intentionally reusable or must be consumed after the first deferred startup attempt, including repeated scheduling and open-failure retry behavior. Correct only a proven stale-state or duplicate-open defect without changing Host, Project World, registry, or Launcher authority.
