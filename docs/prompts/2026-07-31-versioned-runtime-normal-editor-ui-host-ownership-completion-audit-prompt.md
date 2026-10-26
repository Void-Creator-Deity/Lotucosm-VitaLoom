# Fresh-session handoff: E127 complete; E128 planned

E127 completed normal versioned editor composition auditing. Direct proofs cover QApplication create-once/reuse, baseline timing, absolute project forwarding, Launcher return and controlled-exit propagation, Launcher-to-Kernel/UI-host ownership, and a real offscreen visible pixel frame. Latest evidence is `5` focused, `43` root/runtime bootstrap, `135` adjacent offscreen plus green smoke/guards/signatures.

Start **E128 -- Versioned Runtime Launcher Startup-Failure Splash-Cleanup Ownership Audit**. Read its plan, then audit only `launch_editor(..., use_splash=True)` startup-failure cleanup: splash dismissal and secondary failures, Kernel/project/plugin startup failures, event-loop exclusion, primary-error propagation, and FrameCore L0 non-ownership. Preserve E124--E127 boundaries and close the loop with exactly one next gate.
