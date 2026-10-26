# Fresh-session handoff: E140 complete; E141 planned

E140 closed controlled-exit cleanup precedence at plugin load. Start E141: make both `kernel.load_plugins_layered()` and Launcher-owned `dismiss_splash()` raise distinct ordinary errors, prove the exact plugin-load error remains primary and cleanup is warning-only, then leave exactly one next gate.
