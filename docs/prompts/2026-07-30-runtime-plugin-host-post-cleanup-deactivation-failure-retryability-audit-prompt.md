# Fresh-session handoff: E70 completed, E71 next

E70 is complete. `RuntimePluginHost` now retains private, per-active-plugin
completed-stage facts during deactivation. After Adapter cleanup succeeds, a
failure in `plugin.on_unload()` no longer causes retry to replay cleanup against
an already-removed Qt projection; after `on_unload()` succeeds, a command-owner
release failure likewise resumes at exact command release. The Host clears this
private progress only when `loaded_plugins` removal succeeds. Singular
ownership remains:

```text
FrameCore -> lotucosm-vitaloom -> RuntimePluginHost
          -> LegacyEditorPluginAdapter -> LayoutManager
```

E70 evidence: real Qt/Host post-cleanup retry regression; Host command-release
retry regression; focused lifecycle/cleanup `46 passed in 1.28s`; reload
regression `71 passed in 1.23s`; changed-file `py_compile`; all four
architecture/release guardrails; `git diff --check` exited 0 (only existing
CRLF advisories); independent signature proof `2 passed in 0.30s`. E70 did not
rerun the full offscreen Qt suite or application smoke: E68 remains the latest
full Qt (`1678 passed, 34 skipped, 34 subtests`) and regular/eager smoke
(`13/20` and `20/20`) proof. QPainter remains default; OpenGL is not
default-ready. Whole-refactor completion is not claimed.

Execute exactly E71: **Runtime Plugin Host Post-Registry Deactivation
Observation Failure Semantics Audit**. Trace the one remaining deactivation
seam after `loaded_plugins` removal:

```text
loaded-plugin removal -> adapter.after_plugin_deactivated()
```

Establish the observable reporting, shutdown/reload-plan convergence, and
retry behavior when that observer raises after the plugin has been definitively
removed. First write the E71 plan and fresh-session prompt, then add the
smallest evidence-backed regression and repair only if a real inconsistency is
proved. Preserve FrameCore L0, VitaLoom L1, `.pond`, Project World, Inspector
binding, SR2D, SR/PS, Player/export, package/manifests/public imports, and the
QPainter-default/OpenGL-not-default-ready policy. Do not add a second Host,
command registry, event bus, renderer, layout manager, widget DSL, UI
framework, or app shell. Close E71 with evidence, status docs, and exactly one
next Gate.
