# Fresh-session handoff: E150 complete

E150 is closed. With an owned splash, successful Kernel construction, plugin loading, and Kernel show, a RuntimeError/SystemExit at `finish_splash` preserves the primary error through one owned cleanup; KeyboardInterrupt remains intentionally outside cleanup. No case enters the event loop. Evidence: direct 3 passed, versioned-runtime composition 74 passed, editor smoke plugins=13/20, four guards OK, Anaconda signature 2 passed, scoped compile and hygiene passed.

The only next gate is E151: at the same finish seam, make the primary Kernel startup error controlled SystemExit and force owned splash cleanup to raise a distinct SystemExit. Prove the primary exit stays authoritative and KeyboardInterrupt remains unclassified.