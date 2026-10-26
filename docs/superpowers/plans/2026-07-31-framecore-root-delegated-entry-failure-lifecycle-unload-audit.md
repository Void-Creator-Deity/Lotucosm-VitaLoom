# Phase E116 -- FrameCore Root Delegated-Entry Failure Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E115 executed root `main.py` as `__main__` with controlled editor delegation. A delegated normal `SystemExit` code passed through unchanged and the root `finally` unloaded Frame lifecycle exactly once; root did not acquire product runtime Qt or editor lifecycle authority.

## Objective

Audit the corresponding unexpected delegated product-entry failure. Prove root `main.py` preserves the exact primary exception while its `finally` still unloads Frame lifecycle exactly once, without translating the failure, adding a recovery Kernel, or moving QApplication/splash/Host/Project World shutdown authority into L0.

## Required evidence

1. Execute root `main.py` as `__main__` with a fake Frame API whose editor entry raises a controlled non-SystemExit exception.
2. Prove exact exception identity and one lifecycle unload, with established bootstrap/load/select/run ordering.
3. Prove root does not create QApplication or invoke product runtime splash/Kernel/plugin-host/Project World recovery or shutdown actions.
4. Preserve E94--E115 primary-error, deferred-splash, event-loop, lifecycle, and manifest version-selection contracts.
5. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant bootstrap/offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Executed root `main.py` through `runpy.run_path(..., run_name="__main__")` with a controlled `FrameApi.run_product_entry(...)` that raised one saved `RuntimeError` object.
- The root `try/finally` propagated that same object (`error_info.value is expected_error`) and still called `LifecycleRunner.unload_all()` exactly once.
- The only observed sequence is `lifecycle.construct`, `suite.load`, `frame_api.construct`, `frame_api.create_plugin`, `lifecycle.load`, `frame_api.select_product`, `frame_api.run_product_entry`, then `lifecycle.unload_all`.
- The controlled L0 doubles expose no QApplication, splash, Kernel, plugin-host, or Project World recovery/shutdown seam. No root ownership expansion or production correction was warranted.

## Evidence

- Focused: `2 passed in 0.12s`.
- Root/runtime bootstrap: `22 passed in 0.79s`.
- Adjacent offscreen: `114 passed in 1.67s`.
- Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core, GUI, and release guardrails: `OK`.
- Independent signature: `2 passed in 0.18s` via `D:\app\anaconda3\python.exe`; `.venv` lacks `cryptography`, and no dependency was installed.

## Next gate

E117 -- FrameCore Root Lifecycle-Unload Failure Precedence Audit.
