# Fresh-session handoff: E153 complete

E153 is closed. With a completed owned-splash handoff, `app.exec()` is called exactly once; normal integer return is unchanged, and RuntimeError/SystemExit(237)/KeyboardInterrupt preserve exact natural semantics. No late startup cleanup or warning occurs. Evidence: direct 4 passed, versioned-runtime composition 80 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E154: repeat the event-loop entry/return/exception contract with `use_splash=False`. Prove the successful no-splash Kernel path enters the loop exactly once and that splash APIs plus cleanup remain absent for normal, RuntimeError, SystemExit, and KeyboardInterrupt loop outcomes.
