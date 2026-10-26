# Phase E120 -- FrameCore Root Version Query Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E119 proved a delegated command `SystemExit(73)` travels exactly through root `main.py`; root forwarded command arguments and unloaded Frame lifecycle once without adopting product runtime ownership.

## Objective

Audit root's non-product `--version` branch. Prove suite and selected product version reporting remains deterministic and that the real root `__main__` finally unloads Frame lifecycle exactly once without dispatching a product entry or creating Qt-owned runtime resources.

## Required evidence

1. Execute root `main.py` as `__main__` with `--version` and controlled suite/Frame API doubles.
2. Prove exact printed version text, no `run_product_entry()` call, one lifecycle unload, and suite/API/plugin/select ordering.
3. Prove root does not create QApplication or invoke splash/Kernel/plugin-host/Project World recovery or shutdown actions.
4. Preserve E94--E119 contracts and L0--L4 Qt-free boundaries.
5. Run focused proof, relevant adjacency, smoke, guardrails, signature proof, scoped hygiene, and leave exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Executed root `main.py` as `__main__` with `--version` and controlled suite/Frame API doubles.
- Root printed exactly `VitaLoom Suite 2026.7 / lotucosm-vitaloom 1.0.0`, selected the product version only for formatting, never called `run_product_entry()`, and called lifecycle unload exactly once after suite/API/plugin/load/select ordering.
- The controlled L0 doubles expose no QApplication, splash, Kernel, plugin-host, or Project World recovery/shutdown seam. No production correction was warranted.

## Evidence

- Focused: `7 passed in 0.31s`.
- Root/runtime bootstrap: `27 passed in 1.18s`.
- Adjacent offscreen: `119 passed in 1.73s`.
- Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core, GUI, and release guardrails: `OK`.
- Independent signature: `2 passed in 0.20s` via `D:\app\anaconda3\python.exe`; `.venv` lacks `cryptography`, and no dependency was installed.

## Next gate

E121 -- FrameCore Root Hub Exit Lifecycle-Unload Audit.
