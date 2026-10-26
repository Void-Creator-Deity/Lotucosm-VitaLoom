# E208 Fresh-Session Prompt -- WorldBridge Script and Command-Binding Ownership Decision Gate

E208 is complete with an explicit rejection. `.pond`/legacy scene script descriptors may be JSON-shaped, but an attached `EntityBase` script is a live object: attachment invokes `on_attach()` and entity updates invoke `update()`. PS components also retain live sensing, signaling, ingestion, force, and connection behavior. WorldBridge has no script/component execution route; the existing component projection is JSON-safe read-only diagnostics only, not live mapping. Focused coverage passed `11 passed in 0.95s`; the prior fresh runtime baseline remains `2062 passed, 34 skipped, 50 subtests passed in 225.92s`.

The one next gate is E209: audit hierarchy ownership. Do not copy `parent`/`children`, root registration, or traversal semantics unless lane authority, lifecycle, persistence, and update/render behavior are explicitly proven.
