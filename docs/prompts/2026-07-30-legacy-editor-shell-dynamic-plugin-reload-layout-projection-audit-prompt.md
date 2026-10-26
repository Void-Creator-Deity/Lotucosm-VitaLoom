# Fresh-session prompt: E67 dynamic plugin reload layout projection audit

Continue after E66. E66 established that initial layered discovery is
synchronous through Host lifecycle completion, then the sole delayed callback
runs `restore_layout`, default-layout fallback if needed, and Project World open
in that order. New direct timing proof plus capability/layout regressions passed
`16`; full Qt passed `1675 passed, 34 skipped, 34 subtests`; guardrails/diff and
shared-Python signature `2 passed` are green. No runtime implementation was
needed because another restore authority would duplicate LayoutManager.

Execute exactly E67: audit dynamic plugin activation/unload/reload after startup
through RuntimePluginHost, LegacyEditorPluginAdapter, and LayoutManager. Prove
same-title dock and viewport replacement, stale-widget cleanup, and the correct
interaction with persisted layout facts; make only a test-proven repair. Preserve
FrameCore L0, the VitaLoom L1 runtime boundary, RuntimePluginHost authority, the
single Qt adapter/layout projection route, `.pond`, Project World, Inspector
command binding, SR2D, SR/PS, Player/export, packages/public imports, and the
QPainter-default/OpenGL-not-default-ready policy. Do not add another Host,
registry, layout manager, renderer, UI framework, widget DSL, or app shell.
Close with evidence, docs, and exactly one next Gate.
