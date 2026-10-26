# Phase E119 -- FrameCore Root Command Delegation Exit Lifecycle-Unload Audit

Date: 2026-07-31
Status: complete

## Previous gate

E118 executed root `main.py` as `__main__` through the real `command` selector with controlled arguments. A saved non-SystemExit command-entry error passed through unchanged, the command arguments were forwarded exactly, and root lifecycle unloaded once without acquiring product runtime authority.

## Objective

Audit the normal delegated command exit path. Prove a versioned product command's controlled `SystemExit` code passes exactly through root `main.py` while root's finally unloads Frame lifecycle once and retains Qt-free L0 ownership.

## Required evidence

1. Execute root `main.py` as `__main__` with `command` arguments and a fake Frame API whose command entry raises a saved `SystemExit` code.
2. Prove exact code propagation, exact command argument forwarding, one lifecycle unload, and suite/API/plugin/select/run ordering.
3. Prove root does not create QApplication or invoke splash/Kernel/plugin-host/Project World recovery or shutdown actions.
4. Preserve E94--E118 startup, splash, event-loop, exit-code, lifecycle, and manifest version-selection contracts.
5. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
6. Run focused proof, relevant bootstrap/offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- Executed root `main.py` through `runpy.run_path(..., run_name="__main__")` with `command inspect --strict`; the fake command entry raised `SystemExit(73)`.
- Root preserved the exact exit code, forwarded `entry="command"` and `extra_args=["inspect", "--strict"]`, and called `LifecycleRunner.unload_all()` exactly once after suite/API/plugin/select/run ordering.
- The L0 doubles expose no QApplication, splash, Kernel, plugin-host, or Project World recovery/shutdown seam. No production correction was warranted.

## Evidence

- Focused: `6 passed in 0.31s`.
- Root/runtime bootstrap: `26 passed in 1.24s`.
- Adjacent offscreen: `118 passed in 2.25s`.
- Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core, GUI, and release guardrails: `OK`.
- Independent signature: `2 passed in 0.25s` via `D:\app\anaconda3\python.exe`; `.venv` lacks `cryptography`, and no dependency was installed.

## Next gate

E120 -- FrameCore Root Version Query Lifecycle-Unload Audit.
