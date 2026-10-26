# Fresh-session handoff: E137 complete; E138 planned

E137 proved plugin-layer resolution failure cleanup after Launcher owns splash. Start **E138 -- Versioned Runtime Launcher Kernel-Show Failure Cleanup Audit**; read the E138 plan, inject failure at `kernel.show()`, prove owned-splash cleanup and blocked finish/event loop, keep KeyboardInterrupt explicit, and leave one next gate.