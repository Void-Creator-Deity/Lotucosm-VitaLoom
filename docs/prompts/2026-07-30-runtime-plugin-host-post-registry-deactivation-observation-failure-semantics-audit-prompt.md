# Fresh-session handoff: E71 completed, E72 next

E71 is complete. If `after_plugin_deactivated()` raises after singular Host registry removal, the caller receives an `unload_signal` failure but the plugin remains definitively removed: command ownership, `loaded_plugins`, and E70 progress remain empty. A retry cannot replay the observer or resurrect lifecycle ownership.

Evidence: direct Host proof plus shutdown failure-matrix coverage; focused lifecycle/cleanup `47 passed in 0.93s`; reload `71 passed in 0.99s`; `py_compile`, four guardrails, diff check, and signature proof `2 passed in 0.17s`. No new full Qt/smoke run was needed; E68 remains latest full Qt (`1678 passed, 34 skipped, 34 subtests`) and regular/eager smoke (`13/20`/`20/20`) proof.

Execute exactly E72: **Runtime Plugin Host Deactivation Metadata Snapshot Consistency Audit**. Audit the live `plugin.get_plugin_info()` fallback before staged deactivation, especially after E70 progress exists. Prove whether mutable or failing metadata changes retry behavior; create an immutable Host-fact boundary only if a real regression requires it. Preserve singular authority and do not add a second Host, registry, event bus, renderer, layout manager, widget DSL, UI framework, or app shell. Close with evidence and exactly one next Gate.
