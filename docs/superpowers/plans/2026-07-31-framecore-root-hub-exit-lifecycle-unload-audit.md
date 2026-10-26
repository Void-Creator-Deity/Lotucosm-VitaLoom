# Phase E121 -- FrameCore Root Hub Exit Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E120 proved root `--version` prints deterministic suite/product metadata, does not dispatch a product entry, and still unloads Frame lifecycle exactly once through the real `__main__` finally path.

## Objective

Audit the default root Hub selector's normal exit. Prove root delegates only to the Frame plugin Hub entry, preserves its exit code, and unloads Frame lifecycle once without creating product runtime Qt resources or taking editor ownership.

## Required evidence

1. Execute root `main.py` as `__main__` with no arguments and controlled lifecycle/Frame API/plugin doubles.
2. Prove exact Hub exit-code propagation, exact hub entry and argument forwarding, one lifecycle unload, and suite/API/plugin/load/run ordering.
3. Prove no product version selection or `run_product_entry()` occurs, and no QApplication/splash/Kernel/plugin-host/Project World action occurs.
4. Preserve E94--E120 contracts and L0--L4 Qt-free boundaries.
5. Run focused proof, relevant adjacency, smoke, guardrails, signature proof, scoped hygiene, and leave exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- The root no-argument `__main__` path delegated exactly to Frame plugin entry `hub` with `[]`, preserving controlled exit code `19`.
- No product version was selected and no product entry was dispatched; lifecycle unload occurred exactly once after suite/API/plugin/load/Hub ordering.
- Root stayed Qt-free and no production correction was warranted.

## Evidence

- Focused `8 passed in 0.23s`; root/runtime bootstrap `28 passed in 1.27s`; adjacent offscreen `120 passed in 2.30s`.
- Smoke `plugins=13/20`; all four guardrails `OK`; independent signature `2 passed in 0.18s` via `D:\app\anaconda3\python.exe`.

## Next gate

E122 -- FrameCore Root Hub-Smoke Exit Lifecycle-Unload Audit.
