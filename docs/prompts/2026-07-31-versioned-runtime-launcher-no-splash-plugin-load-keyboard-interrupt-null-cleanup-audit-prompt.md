# Fresh-session handoff: E143 complete; E144 planned

E143 closed the no-splash plugin-load KeyboardInterrupt path: it propagates unchanged with no null cleanup, splash work, show, or event loop. Start E144: reach `kernel.show()` after successful plugin load with splash disabled and audit RuntimeError/SystemExit/KeyboardInterrupt behavior, then leave exactly one next gate.
