# Fresh-session handoff: E152 complete

E152 is closed. After a real owned-splash pre-finish sequence, a primary RuntimeError from `finish_splash` retains exact identity when `dismiss_splash(splash)` raises secondary `SystemExit(234)`. Cleanup is once-only and warning-only; the full pre-finish sequence occurs, the event loop is unreachable, and KeyboardInterrupt remains unclassified. Evidence: direct 1 passed, versioned-runtime composition 76 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene proof recorded.

The only next gate is E153: after successful splash finish, audit `app.exec()` as the UI-host event-loop boundary. Prove it is entered once and its normal return value is preserved; also prove RuntimeError/SystemExit/KeyboardInterrupt from the event loop retain natural semantics without retrospective startup cleanup or new Launcher/FrameCore lifecycle ownership.
