# Phase E117 -- FrameCore Root Lifecycle-Unload Failure Precedence Audit

Date: 2026-07-31
Status: complete

## Previous gate

E116 executed root `main.py` as `__main__` while a controlled delegated editor product entry raised a saved `RuntimeError`. The exact exception object propagated unchanged, and root's `finally` invoked Frame lifecycle unload exactly once after the established suite/API/plugin/select/run sequence. Root did not obtain Qt or editor-runtime recovery/shutdown authority.

## Objective

Audit the remaining root-finally failure seam: a Frame lifecycle-unload exception after delegated product entry succeeds or fails. Establish explicit exception precedence and chaining while preserving exactly one unload attempt and keeping root as a Qt-free L0 delegation boundary.

## Required evidence

1. Execute root `main.py` as `__main__` with controlled Frame API and LifecycleRunner doubles where `unload_all()` raises a saved exception.
2. Prove the cleanup exception identity and, when product entry also fails, the primary delegation exception remains available through Python exception chaining rather than being silently lost.
3. Prove the expected suite/API/plugin/select/run/unload ordering and exactly one unload attempt.
4. Prove root does not create QApplication or invoke splash/Kernel/plugin-host/Project World recovery or shutdown actions.
5. Preserve E94--E116 startup, splash, event-loop, exit-code, lifecycle, and manifest version-selection contracts.
6. Do not alter Qt-free L0--L4 engine-plugin contracts, `.pond`, AI commands, Inspector binding, SR2D, manifests, plugin discovery, Project World/recovery ownership, or renderer defaults.
7. Run focused proof, relevant bootstrap/offscreen adjacency, smoke, four guardrails, scoped hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

The PyQt6/QPainter editor remains a legacy UI-host adapter; QPainter remains default and OpenGL/native acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- The real root `__main__` path was executed with a fake LifecycleRunner whose `unload_all()` raised a saved `RuntimeError`.
- After a successful editor delegation, that exact cleanup exception was surfaced with no exception context. When a saved delegated editor `RuntimeError` also occurred, the cleanup error remained the surfaced object and the delegated error was retained as its exact `__context__`.
- Both cases observed one suite/API/plugin/select/run/unload sequence and exactly one unload attempt. The controlled L0 doubles expose no QApplication, splash, Kernel, plugin-host, or Project World recovery/shutdown seam.
- This is transparent Python `try/finally` precedence, not a reason to add L0 recovery or alter production ownership. No production correction was warranted.

## Evidence

- Focused: `4 passed in 0.25s`.
- Root/runtime bootstrap: `24 passed in 0.96s`.
- Adjacent offscreen: `116 passed in 1.61s`.
- Editor smoke: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin, core, GUI, and release guardrails: `OK`.
- Independent signature: `2 passed in 0.23s` via `D:\app\anaconda3\python.exe`; `.venv` lacks `cryptography`, and no dependency was installed.

## Next gate

E118 -- FrameCore Root Command Delegation Failure Lifecycle-Unload Audit.
