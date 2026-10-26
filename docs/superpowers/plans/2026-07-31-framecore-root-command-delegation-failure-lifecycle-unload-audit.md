# Phase E118 -- FrameCore Root Command Delegation Failure Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E117 exercised root `main.py` as `__main__` with a raising Frame lifecycle unload. A cleanup failure remained the exact surfaced object; when editor delegation also failed, the primary delegated exception was retained as Python exception context. Root made exactly one unload attempt and remained Qt-free.

## Objective

Extend lifecycle-boundary proof from the editor selector to root's `command` product-entry selector. Audit controlled command delegation failure and root-finally unload semantics without transferring runtime, Qt, splash, Kernel, Host, or Project World ownership into L0.

## Required evidence

1. Execute root `main.py` as `__main__` with `command` arguments and a fake Frame API whose selected product command entry raises a saved non-SystemExit exception.
2. Prove exact exception identity, exact command argument forwarding, one lifecycle unload, and suite/API/plugin/select/run ordering.
3. Prove root does not create QApplication or invoke splash/Kernel/plugin-host/Project World recovery or shutdown actions.
4. Preserve E94--E117 startup, splash, event-loop, exit-code, lifecycle, and manifest version-selection contracts.
5. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant bootstrap/offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Executed root `main.py` with `runpy.run_path(..., run_name="__main__")` and `command inspect --strict` arguments. The fake command entry raised one saved `RuntimeError` object.
- Root forwarded `entry="command"` and `extra_args=["inspect", "--strict"]` exactly, propagated the same error object, and called `LifecycleRunner.unload_all()` exactly once after suite/API/plugin/select/run ordering.
- The controlled L0 doubles expose no QApplication, splash, Kernel, plugin-host, or Project World recovery/shutdown seam. No root ownership expansion or production correction was warranted.

## Evidence

- Focused: `5 passed in 0.26s`.
- Root/runtime bootstrap: `25 passed in 1.15s`.
- Adjacent offscreen: `117 passed in 1.70s`.
- Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core, GUI, and release guardrails: `OK`.
- Independent signature: `2 passed in 0.20s` via `D:\app\anaconda3\python.exe`; `.venv` lacks `cryptography`, and no dependency was installed.

## Next gate

E119 -- FrameCore Root Command Delegation Exit Lifecycle-Unload Audit.
