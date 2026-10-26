# Fresh-session handoff: E139 complete; E140 planned

E139 closed the plugin-load controlled-exit ownership path. Start E140: make ordinary splash cleanup fail after `kernel.load_plugins_layered()` raises `SystemExit`, prove the primary exit remains unchanged and cleanup is warning-only, keep KeyboardInterrupt policy explicit, then leave exactly one next gate.
