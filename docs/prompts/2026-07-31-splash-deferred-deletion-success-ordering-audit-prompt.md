# Fresh-session handoff: E106 complete

E106 is complete. The former direct `QTimer.singleShot(0, splash.deleteLater)` callback leaked a `deleteLater()` exception after Launcher had already handed control to `app.exec()`. A deterministic scheduler double proved that gap through a genuine red test. The product fix is confined to `core/VitaLoom/ui/splash_screen.py`: `finish_splash(...)` schedules a private adapter-owned callback that catches callback-time `Exception` and logs `Failed to delete splash after editor startup handoff`.

E105 remains intact: `splash.finish(...)` and synchronous `QTimer.singleShot(...)` scheduling failures retain their exact primary exceptions, invoke Launcher cleanup once, and block `app.exec()`. E106 keeps Launcher out of Qt callback and splash lifecycle ownership. Current evidence: focused green `3 passed, 51 deselected`; interface `54 passed`; adjacent offscreen `97 passed`; editor smoke `plugins=13/20`; all four guardrails `OK`; signature `2 passed`. `.venv` lacks `cryptography`, so the signature check uses `D:\app\anaconda3\python.exe`; do not install dependencies merely for this.

## Current source of truth

- Adapter: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/ui/splash_screen.py`
- Launcher: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/editor_launcher.py`
- Focused interface proof: `tests/test_runtime_capability_registry_interface.py`
- Phase plan: `docs/superpowers/plans/2026-07-31-splash-deferred-deletion-success-ordering-audit.md`
- Status/context: `docs/mainline_status.md`, `CONTEXT.md`

## E107 task

Audit the successful deferred deletion path, not E106's failure observation again. Use a timer double that stores the callback and a successful `app.exec()` double. Prove: `splash.finish()` precedes one `singleShot(0, ...)`; no deletion occurs before `launch_editor()` reaches/returns from `app.exec()`; invoking the stored callback later calls `deleteLater()` exactly once and logs no E106 warning. Preserve the E105 immediate/synchronous failure and E106 callback-failure proofs.

If a defect is demonstrated, fix it only in the splash adapter. Do not grant Launcher callback, QApplication, or splash-lifecycle authority. Do not touch `.pond`, AI command registry, Inspector command binding, SR2D, manifests, plugin discovery, renderer defaults, recovery, project ownership, or Qt-free L0-L4 contracts. QPainter remains default; OpenGL/native acceleration is not default-ready.

Before switching topics, update the phase plan, `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and this fresh-session prompt as needed. Run focused evidence, the relevant interface/offscreen tests, root offscreen smoke, four guardrails, scoped hygiene, and the independent signature check. Record skips and exactly one next gate. Do not stage, commit, reset, restore, clean, or delete pre-existing work.