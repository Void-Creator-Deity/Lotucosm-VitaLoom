# Fresh-session handoff: E109 complete

E109 is complete. A deterministic `app.exec()` double raised only after splash show/messages, Kernel construction/load/show, `splash.finish(kernel)`, and successful zero-delay scheduling. The exact entry `RuntimeError` stayed primary. Because the splash handoff was already complete, Launcher did not call E95 `dismiss_splash()` or duplicate `hide()`/`deleteLater()`; the saved adapter callback could later delete once without warning. No E109 production change was needed.

Evidence: focused `1 passed, 57 deselected`; interface `58 passed`; adjacent offscreen `101 passed`; editor smoke `suite=lotucosm.vitaloom.suite`, `product=lotucosm-vitaloom@1.0.0`, `plugins=13/20`; four guardrails `OK`; independent Anaconda signature `2 passed`. `.venv` lacks `cryptography`; do not install it for this work.

Next gate is E110: use a real offscreen `QApplication`, real zero-delay Qt timer delivery, and a controlled raising application adapter to confirm E109's completed-splash ownership boundary. Preserve primary-error identity, prevent duplicate Launcher cleanup, and keep deferred callback-time behavior adapter-owned. Correct only a demonstrated defect.

Preserve E102--E109 semantics and all architecture constraints: Qt-free L0--L4 engine-plugin contracts, `.pond`, AI command registry, Inspector command binding, SR2D, manifests, plugin discovery, project/recovery ownership, and renderer defaults. Before switching topics, update plan/status/context/index/prompt, run focused evidence plus interface/offscreen/smoke/guardrail/signature checks, perform scoped hygiene, record skips, and leave exactly one next gate. Never stage, commit, reset, restore, clean, or delete pre-existing work.
