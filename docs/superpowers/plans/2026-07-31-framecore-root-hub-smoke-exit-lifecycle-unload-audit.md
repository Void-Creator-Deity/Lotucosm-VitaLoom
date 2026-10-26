# Phase E122 -- FrameCore Root Hub-Smoke Exit Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E121 proved the default root Hub selector delegates only to the Frame plugin Hub entry, preserves its exit code, does not select/dispatch a product, and unloads Frame lifecycle once.

## Objective

Audit root `--smoke-hub` routing: exact Hub-smoke entry/argument forwarding, exit-code propagation, no product dispatch, and exactly one lifecycle unload through the root finally path.

## Required evidence

1. Execute root `main.py` as `__main__` with `--smoke-hub` and controlled Frame plugin/lifecycle doubles.
2. Prove exact `hub_smoke` entry and argument forwarding, exact exit-code propagation, no product selection/entry, and one unload.
3. Preserve Qt-free L0 ownership and E94--E121 contracts.
4. Run focused proof, adjacency, smoke, guardrails, signature proof, hygiene, and leave exactly one next gate.

## Explicit non-goals

QPainter remains default; OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Root --smoke-hub delegated exactly hub_smoke / [--smoke-hub], preserved controlled exit code 23, selected/dispatched no product, and unloaded Frame lifecycle once.
- Root stayed Qt-free; no production correction was warranted.

## Evidence

- Focused 9 passed in 0.33s; bootstrap 29 passed in 1.19s; adjacent 121 passed in 1.90s; smoke plugins=13/20; guardrails OK; signature 2 passed in 0.29s.

## Next gate

E123 -- FrameCore Root Hub Argument Forwarding Lifecycle-Unload Audit.

