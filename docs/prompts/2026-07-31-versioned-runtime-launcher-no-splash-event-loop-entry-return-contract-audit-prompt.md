# Fresh-session handoff: E154 complete

E154 is closed. With use_splash=False, successful Kernel construction/layer load/show reaches app.exec() exactly once and preserves normal integer return plus RuntimeError/SystemExit(239)/KeyboardInterrupt semantics. No splash API, cleanup, or startup-cleanup warning is touched. Evidence: direct 4 passed, versioned-runtime composition 84 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene proof recorded.

The only next gate is E155: validate the successful explicit-service composition path. Pass valid L1 RuntimeCapabilityRegistry and RuntimeEventBus instances to Launcher, prove it validates and forwards those exact objects to Kernel rather than constructing/replacing either service, while retaining current splash and event-loop ownership boundaries.
