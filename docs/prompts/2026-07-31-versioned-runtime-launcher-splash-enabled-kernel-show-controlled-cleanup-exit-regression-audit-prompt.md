# Fresh-session handoff: E148 complete

E148 is closed. With an owned splash, primary Kernel-show `SystemExit(221)` survives a secondary cleanup `SystemExit(222)` by identity/code. Splash show and all pre-show messages remain ordered; cleanup is once-only and warning-only; finish/event loop are unreachable. Evidence: direct 1 passed, versioned-runtime composition 70 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E149: retain the owned-splash setup but inject a primary RuntimeError at Kernel show plus a secondary cleanup SystemExit. Prove the ordinary primary error object cannot be masked by a classified controlled cleanup exit, without changing the KeyboardInterrupt boundary.