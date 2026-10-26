# Fresh-session handoff: E157 complete

E157 is complete. Direct no-splash regressions now cover both remaining mixed service combinations: explicit registry with omitted bus, and default registry with explicit bus. They prove validator/default-constructor order, exact caller identity where supplied, omitted event_bus keyword behavior, normal Kernel/layer/event-loop ordering, and no splash or cleanup activity. No production code change was required.

Proceed only with E158 -- Versioned Runtime Launcher Invalid-Service Pre-UI Failure Matrix Audit. Supply invalid explicit registry and event-bus candidates, prove validation fails before splash, Kernel, layers, plugins, cleanup, or app.exec(), and preserve exact error semantics plus all Qt-free FrameCore L0/runtime boundaries.