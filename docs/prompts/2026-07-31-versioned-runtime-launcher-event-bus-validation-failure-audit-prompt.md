# Fresh-session handoff: E136 complete; E137 planned

Caller-supplied event-bus validation is now proven cleanup-free before splash ownership. The next sequential Launcher seam has an acquired splash: plugin-layer resolution.

Start **E137 -- Versioned Runtime Launcher Plugin-Layer Resolution Failure Cleanup Audit**. Read `docs/superpowers/plans/2026-07-31-versioned-runtime-launcher-plugin-layer-resolution-failure-cleanup-audit.md`; inject ordinary/SystemExit failure at `default_plugin_layers(normalized_repo_root)`, prove exact once-only splash cleanup and no plugin load/show/event loop, keep `KeyboardInterrupt` explicit, and leave exactly one next gate.