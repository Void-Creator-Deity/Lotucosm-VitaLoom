# Fresh-session handoff: E151 complete

E151 is closed. After a real owned-splash pre-finish sequence, primary `SystemExit(231)` from `finish_splash` remains authoritative when `dismiss_splash(splash)` raises secondary `SystemExit(232)`. Cleanup is once-only and warning-only; the event loop is unreachable and KeyboardInterrupt remains unclassified. Evidence: direct 1 passed, versioned-runtime composition 75 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E152: retain the owned-splash finish seam but inject a primary RuntimeError plus secondary cleanup SystemExit. Prove the ordinary primary object cannot be masked by a classified controlled cleanup exit.