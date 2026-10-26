# Phase E127 -- Versioned Runtime Normal-Editor UI-Host Ownership Completion Audit

Date: 2026-07-31
Status: complete

## Objective

Audit normal versioned-runtime editor composition: QApplication reuse/construction, baseline application, Launcher invocation, Kernel/Host ownership, and failure/exit propagation. Prove FrameCore root remains L0-only while the versioned runtime and legacy UI-host adapter retain their existing responsibilities.

## Audit result

- Normal `runtime/main.py --editor --project workspace.pond` creates exactly one QApplication only when no instance exists, applies the baseline after runtime bootstrap, and gives Launcher the absolute project path. An existing QApplication is reused without construction.
- Launcher return codes and an independently raised `SystemExit` cross the versioned-runtime boundary unchanged; E125 retains the direct non-SystemExit-to-runtime-`SystemExit(1)` proof. Neither path grants FrameCore root L0 QApplication, Kernel, Host, Project World, or shutdown ownership.
- The real Launcher remains the Kernel/UI-host composition owner: it makes the runtime capability registry, constructs Kernel, sets the explicit project, loads layered plugins, shows the window, and only then enters the provided application event loop.
- A real offscreen Kernel/legacy UI-host launch loaded the production plugin layers, became visible, and produced a non-transparent captured frame. The test retains the process QApplication reference intentionally, so its QObject singleton is not destroyed before adjacent legacy-kernel tests; production ownership is unchanged.
- No production defect or production-code change was warranted. Offscreen proof covers visible rendering rather than pointer/keyboard interaction. A desktop current-context interactive session remains the fallback/unblock path for manual gesture parity; QPainter stays default and OpenGL/native is not default-ready.

## Required evidence

- Exercise normal `runtime/main.py --editor` and `--project` with controlled existing/no-existing application seams.
- Prove runtime creates QApplication at most once when absent and reuses it when present; Launcher remains the Kernel/UI-host composition owner.
- Verify launcher return, `SystemExit`, and non-`SystemExit` boundaries without transferring UI or Project World shutdown to root.
- Use actual offscreen rendering/interaction proof where available; otherwise record fallback, unblock path, and limitation.
- Add only evidence-driven minimal coverage/correction; finish verification and leave one next gate.

## Evidence

- Focused E127 suite: `5 passed in 0.83s` (`QT_QPA_PLATFORM=offscreen`).
- Root/runtime bootstrap slice: `43 passed in 1.67s`.
- Adjacent offscreen regression: `135 passed in 2.05s`.
- Real `main.py --smoke-editor`: `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`.
- Project-plugin/core/GUI/release guards: `OK`; independent Anaconda signature proof: `2 passed in 0.16s`. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

E128 -- Versioned Runtime Launcher Startup-Failure Splash-Cleanup Ownership Audit.

## Explicit non-goals

No UI-host migration, OpenGL/native default switch, `.pond` semantic change, command/Inspector/SR2D/manifest/Project World authority change without narrowly evidenced need. QPainter remains default; whole-refactor completion is not claimed.
