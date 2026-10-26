# Fresh-session handoff: E107 complete

E107 is complete. A deterministic timer double now proves the corrected splash adapter schedules one zero-delay callback after `splash.finish(...)`, does not delete before successful `app.exec()` handoff, and deletes once with no E106 warning when the callback succeeds. No E107 production change was needed; E106's adapter-owned wrapper remains the only product correction.

Current proof: focused E105/E106/E107 `3 passed, 52 deselected`; interface `55 passed`; adjacent offscreen `98 passed`; root editor smoke `plugins=13/20`; all four guardrails `OK`; independent signature `2 passed`. `.venv` still lacks `cryptography`, so use `D:\app\anaconda3\python.exe` for `tests/test_package_signature_warn_only.py`; do not install dependencies. QPainter remains default and OpenGL/native is not default-ready.

## Current source of truth

- Splash adapter: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/ui/splash_screen.py`
- Launcher: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/editor_launcher.py`
- Focused proofs: `tests/test_runtime_capability_registry_interface.py`
- Phase plan: `docs/superpowers/plans/2026-07-31-splash-deferred-deletion-real-qt-event-loop-parity-audit.md`

## E108 task

Run a real offscreen Qt parity audit for `finish_splash(...)`. Use a real `QApplication` and actual `QTimer.singleShot(0, ...)` delivery, while keeping the splash double minimally Qt-compatible if needed. Prove a successful callback executes and deletes exactly once without a warning; prove a callback-time `deleteLater()` error is logged and does not escape Qt event processing. Do not retest only the deterministic double and do not move any callback/lifecycle responsibility into Launcher.

Preserve E102--E107 semantics and all architecture constraints: Qt-free L0--L4 engine-plugin contracts, `.pond`, AI command registry, Inspector command binding, SR2D, manifests, plugin discovery, project/recovery ownership, and renderer defaults. Before switching topics, update plan/status/context/index/prompt, run focused evidence plus interface/offscreen/smoke/guardrail/signature checks, perform scoped hygiene, record skips, and leave exactly one next gate. Never stage, commit, reset, restore, clean, or delete pre-existing work.