# Fresh-session handoff: E164 complete

E164 is complete. When no-splash explicit-service `set_startup_project()` raises RuntimeError or SystemExit and the established `dismiss_splash(None)` cleanup also raises RuntimeError or SystemExit, the exact original project-binding error remains authoritative; cleanup is attempted once, logged as secondary, and cannot reach splash allocation, plugins, or the event loop. Next: E165 audits the distinct `KeyboardInterrupt` escape contract for the same no-splash project-binding boundary.
