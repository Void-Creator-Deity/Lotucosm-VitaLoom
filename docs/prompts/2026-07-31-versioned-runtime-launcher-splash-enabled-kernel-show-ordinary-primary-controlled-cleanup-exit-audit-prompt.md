# Fresh-session handoff: E149 complete

E149 is closed. With an owned splash, a primary RuntimeError from `kernel.show()` remains identical when `dismiss_splash(splash)` raises a secondary SystemExit. The normal splash pre-show order remains intact; owned cleanup is once-only and warning-only; finish/event loop are unreachable. Evidence: direct 1 passed, versioned-runtime composition 71 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E150: after successful owned-splash Kernel show, inject RuntimeError, SystemExit, and KeyboardInterrupt at `finish_splash`. Prove classified failures run one owned cleanup while KeyboardInterrupt remains unclassified, and neither path enters the event loop.