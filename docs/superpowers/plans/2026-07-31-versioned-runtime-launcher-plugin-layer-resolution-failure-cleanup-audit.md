# Phase E137 -- Versioned Runtime Launcher Plugin-Layer Resolution Failure Cleanup Audit

Date: 2026-07-31
Status: complete

## Previous gate

E136 closed the final no-resource service-validation seam. Layer resolution occurs after Launcher owns a shown splash and has constructed Kernel.

## Audit result

- Direct regressions inject ordinary RuntimeError and `SystemExit(181)` at the real `default_plugin_layers(normalized_repo_root)` seam. Both retain the exact primary object/code, dismiss the Launcher-held splash exactly once, and never call plugin loading, Kernel show, splash finish, or `app.exec()`.
- `KeyboardInterrupt` is explicitly outside the controlled `except (Exception, SystemExit)` cleanup policy: it preserves identity and does not dismiss the splash. This is intentional existing ownership, not a production defect.
- No production correction was warranted. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Evidence

- New direct regression: `tests/test_versioned_runtime_launcher_plugin_layer_resolution_failure.py` (3 cases).
- Focused E128--E137/interface slice: `122 passed in 3.81s` with `QT_QPA_PLATFORM=offscreen`.
- Complete `test_versioned_runtime*.py` composition slice: `53 passed in 4.49s` with `QT_QPA_PLATFORM=offscreen`.
- Real `main.py --smoke-editor`: `plugins=13/20`; project-plugin/core/GUI/release guards `OK`; independent Anaconda signature `2 passed in 0.28s`. `.venv` lacks `cryptography`; no dependency was installed.

## Next gate

Exactly one next gate: **E138 -- Versioned Runtime Launcher Kernel-Show Failure Cleanup Audit**. Audit ordinary, controlled-exit, and KeyboardInterrupt behavior from `kernel.show()` while Launcher owns a splash.