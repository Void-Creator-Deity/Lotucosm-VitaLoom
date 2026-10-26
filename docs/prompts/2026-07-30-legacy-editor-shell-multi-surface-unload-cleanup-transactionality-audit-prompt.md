# Fresh-session handoff: E69 completed, E70 next

E69 is complete. It repaired a real multi-surface dynamic-unload inconsistency
in the existing `RuntimePluginHost -> LegacyEditorPluginAdapter ->
LayoutManager` route. Declarative cleanup now removes a viewport before its
dock because `LayoutManager.remove_viewport()` is the only concrete
surface-cleanup path with explicit, retryable `False` failure semantics. A
failed viewport disposer therefore leaves the loaded Host plugin, Host-owned
command, dock, viewport, one Qt tab, and adapter ownership facts aligned; after
the disposer is repaired, retry removes all of them.

E69 evidence: direct real Qt/Host proof `1 passed, 12 deselected`; focused
lifecycle/cleanup suite `39 passed`; reload suite `70 passed`; four
architecture/release guardrails passed; changed-file `py_compile` passed;
`git diff --check` exited 0 (only pre-existing CRLF advisories); independent
signature proof `2 passed`. E69 deliberately did not rerun a new full Qt suite
or application smoke: E68 already contains the latest full offscreen Qt
(`1678 passed, 34 skipped, 34 subtests`) and regular/eager smoke (`13/20` and
`20/20`) proof, and E69 changed only cleanup ordering plus a fixture.

Execute exactly E70: **Runtime Plugin Host Post-Cleanup Deactivation Failure
Retryability Audit**. Trace `RuntimePluginHost._deactivate_plugin()` after
`adapter.before_plugin_unload()` succeeds. Audit and prove the behavior when
`plugin.on_unload()` or Host command release then fails: the adapter may already
have removed the viewport/dock while the Host remains active, and a retry may
not be able to reach the original post-cleanup failure. First write the E70
plan and fresh-session prompt, then add a focused real Qt/Host regression and
make only the smallest evidence-backed repair.

Preserve the singular authority route, FrameCore L0, VitaLoom L1, `.pond`,
Project World, Inspector binding, SR2D, SR/PS, Player/export,
packages/manifests/public imports, and QPainter-default/OpenGL-not-default-ready
policy. Do not add a second Host, command registry, event bus, renderer, layout
manager, widget DSL, UI framework, or app shell. Do not claim whole-refactor
completion or generic distributed Qt rollback. Close E70 with evidence, status
docs, and exactly one next Gate.