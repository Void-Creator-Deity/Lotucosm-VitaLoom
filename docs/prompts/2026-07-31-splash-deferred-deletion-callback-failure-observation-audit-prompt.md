# Fresh-session handoff: E105 complete

E105 is complete. `finish_splash(...)` occurs after `kernel.show()` and before `app.exec()`. Deterministic cases proved that both immediate `splash.finish(...)` errors and synchronous `QTimer.singleShot(...)` scheduling errors retain their exact primary exception, invoke E95 dismissal once, and prevent event-loop entry; cleanup failure logs without replacing the primary finish error.

No runtime correction was required: synchronous failures remain correctly owned by the existing outer Launcher startup boundary. Proof: focused `3 passed`; interface `53 passed`; adjacent offscreen `96 passed`; root smoke `plugins=13/20`; four guardrails and Anaconda signatures `2 passed`. `.venv` lacks `cryptography`; no dependency was installed. QPainter remains default; OpenGL/native is not default-ready; whole refactor is not complete.

One active gate: **E106 -- Splash Deferred-Deletion Callback Failure Observation Audit**. Audit callback-time `deleteLater()` failure after a successful timer schedule, retaining splash-adapter ownership and not giving Launcher Qt event-loop or splash lifetime authority.