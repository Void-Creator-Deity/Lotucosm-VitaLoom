# Fresh-session handoff: E163 complete

E163 is complete. Real explicit registry/event-bus services validate and preserve identity into `EditorKernel`; no-splash `set_startup_project()` RuntimeError and SystemExit(311) retain exact primary-error identity, stop plugin/event-loop work, and use the established one-call safe null cleanup `dismiss_splash(None)` without a cleanup warning when dismissal succeeds. Next: E164 tests whether ordinary and controlled failures from that null cleanup remain secondary without masking the primary project-binding error.
