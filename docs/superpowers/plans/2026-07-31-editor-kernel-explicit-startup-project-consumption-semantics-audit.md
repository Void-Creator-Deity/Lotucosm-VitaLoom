# Phase E98 -- Editor Kernel Explicit Startup-Project Consumption Semantics Audit

Date: 2026-07-31
Status: complete

## Previous gate

E97 proved the deferred project-path selection contract without a production change: a valid explicit project wins over fallback; absent/invalid input uses the existing fallback; timer scheduling is single per invocation and layout precedes project startup; an explicit Host failure is contained without fallback replay.

`EditorKernel._startup_project_path` remains stored after `_try_open_last_project_on_startup()` returns. The adjacent lifecycle question is whether that persistence is intentional under a repeated post-plugin callback, versus a stale explicit-project replay or an incorrect loss of retry behavior after a failed open.

## Objective

Audit explicit startup-project state consumption and retry semantics inside the existing Editor Kernel. Correct only a demonstrated stale-state, duplicate-open, or retry-contract defect while preserving the singular Kernel, configured Project World session Host, capability registry, plugin lifecycle, `.pond` semantics, and legacy Qt adapter boundary.

## Required evidence

1. Map all writers/readers of `_startup_project_path`, including repeated plugin-load scheduling and direct startup callbacks.
2. Reproduce two deferred callbacks after a valid explicit-project open; prove the intentional one-shot or repeat contract and its externally observable Host calls.
3. Reproduce explicit-open failure followed by a later callback; prove the intentional retry/non-retry behavior without fallback replay or hidden cleanup.
4. Reproduce invalid explicit input followed by later valid assignment; prove no stale invalid state blocks a new explicit project.
5. Preserve error containment, project fallback semantics, and the absence of process-global environment mutation or Launcher authority.
6. Run focused offscreen tests, adjacency, source/hygiene checks, root smoke, guardrails, independent signature proof, and record all skips/blockers plus exactly one next gate.

## Explicit non-goals

Do not change `.pond`, Project World commands, Inspector binding, AI command registry, SR2D, Player/export, plugin discovery/loading contracts, manifests, public imports, MRO, renderer choice, or application shell. Do not add a second Host, registry, event bus, fallback Kernel, force cleanup, recovery controller, cache, serializer, renderer, or UI framework. Do not reintroduce `VITALOOM_SKIP_AUTO_OPEN` mutation. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- Defect reproduced: successful `host.open_project(pending)` retained `_startup_project_path`; a later deferred callback reopened the same explicit project. New regressions were red: `3 failed in 0.38s`.
- Narrow correction: after successful `host.open_project(pending)`, Kernel clears `self._startup_project_path` and returns. A throwing open leaves the state intact for the existing contained retry path; it does not replay fallback.
- Coverage proves success then fallback, failure then retry then fallback, and a valid replacement after invalid input. No Launcher/environment/Host/Project World/registry authority changed.
- Evidence: focused green `8 passed in 0.25s`; adjacency `138 passed in 2.97s`; root smoke `plugins=13/20`; four guardrails OK; Anaconda signatures `2 passed in 0.19s`. Kernel/test compilation passed. The changed test has CRLF/no trailing whitespace. Legacy untracked Kernel source retains 456 bare-LF and 15 pre-existing trailing-whitespace lines; only the new consumption line was checked clean. `.venv` lacks `cryptography`; no install. E68 (`1678 passed, 34 skipped, 34 subtests`) is historical only. QPainter default; OpenGL/native not default-ready; whole refactor is not claimed complete.

## Next gate

Exactly one next gate: **E99 -- Editor Launcher Project-Path Canonicalization and Type Boundary Audit**. Audit public input acceptance/normalization without moving descriptor validation or lifecycle authority from Kernel/Project World.
