# Phase E123 -- FrameCore Root Hub Argument Forwarding Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Objective

Audit the non-empty default Hub argument path: exact Hub argument forwarding, Frame-plugin exit-code propagation, no product selection/dispatch, and one root finally lifecycle unload.

## Required evidence

Execute root `main.py` as `__main__` with controlled non-product Hub arguments; prove exact Hub entry/args, exact exit code, absence of product routing, one unload, and Qt-free L0 ownership. Preserve E94--E122 contracts; run focused/adjacent/smoke/guardrail/signature/hygiene proof and leave exactly one next gate.

## Explicit non-goals

QPainter remains default; OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Root forwarded non-product arguments [--safe-mode, workspace.pond] exactly to Frame plugin hub, preserved controlled exit code 29, made no product call, and unloaded once.
- Root remained Qt-free; no production correction was warranted.

## Evidence

- Focused 10 passed in 0.59s; bootstrap 30 passed in 0.80s; adjacent 122 passed in 1.56s; smoke plugins=13/20; guardrails OK; signature 2 passed in 0.26s.

## Next gate

E124 -- FrameCore Root Branch-Matrix Completion Audit.

