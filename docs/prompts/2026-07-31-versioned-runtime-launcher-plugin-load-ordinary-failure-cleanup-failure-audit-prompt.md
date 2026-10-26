# Fresh-session handoff: E141 complete; E142 planned

E141 closed ordinary primary-error precedence when plugin load and splash cleanup both fail. Start E142: set `use_splash=False`, inject ordinary and controlled plugin-load failures, verify the existing null cleanup handoff is UI-no-op and cannot affect primary error, then leave exactly one next gate.
