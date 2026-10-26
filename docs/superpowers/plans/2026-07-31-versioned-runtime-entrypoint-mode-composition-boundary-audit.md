# Phase E126 -- Versioned Runtime Entrypoint-Mode Composition Boundary Audit

Date: 2026-07-31
Status: complete

## Objective

Audit versioned runtime `command`, `--version`, and `--smoke-editor` precedence and contracts across the FrameCore manifest boundary.

## Audit result

- Real manifest `command` dispatch reaches `runtime/main.py` with only user command arguments after the manifest token and preserves controlled `SystemExit(73)` without runtime bootstrap or Qt/editor composition.
- Internal `--version` wins over `--editor`, validates runtime metadata, returns normally, and creates no QApplication, Launcher, Kernel, Host, or Project World resource.
- Internal `--smoke-editor` wins over ordinary editor composition even when the manifest/root supplied `--editor` and project arguments. The full real smoke still proves temporary-state restoration, idle Project World Host cleanup, plugin observation, and `13/20` active/catalog result.
- No production defect or production-code change was warranted; isolated tests replace only UI/smoke seams to prove precedence.

## Evidence

- Focused E126 suite: `3 passed in 0.20s`.
- Root/runtime bootstrap: `38 passed in 1.17s` (`QT_QPA_PLATFORM=offscreen`).
- Adjacent offscreen: `130 passed in 1.76s`.
- `main.py --smoke-editor` passed (`lotucosm.vitaloom.suite`, `lotucosm-vitaloom@1.0.0`, `plugins=13/20`).
- Project-plugin/core/GUI/release guards: `OK`; independent Anaconda signature proof: `2 passed in 0.24s`. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

E127 -- Versioned Runtime Normal-Editor UI-Host Ownership Completion Audit.
