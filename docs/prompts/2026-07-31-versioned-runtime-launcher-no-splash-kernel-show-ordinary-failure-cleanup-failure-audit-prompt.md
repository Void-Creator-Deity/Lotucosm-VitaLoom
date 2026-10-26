# Fresh-session handoff: E146 complete

E146 is closed. With `use_splash=False`, a primary RuntimeError raised by `kernel.show()` stays identical even if `dismiss_splash(None)` raises a distinct ordinary RuntimeError. Cleanup is once-only and warning-only; splash presentation and the event loop remain unreachable. Evidence: direct 1 passed, versioned-runtime composition 68 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E147: make both the no-splash Kernel-show primary error and the injected null-cleanup failure controlled SystemExit instances. Audit whether a secondary controlled exit can mask the primary, while retaining the explicit KeyboardInterrupt boundary and no BaseException catch.