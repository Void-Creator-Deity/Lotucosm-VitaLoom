# Fresh-session prompt: E64 legacy Editor shell viewport-tab projection audit

Continue after E63. Commands remain singular in RuntimePluginHost; the Adapter
only projects QAction/menu/toolbar UI, and every QAction trigger now receives a
fresh JSON-safe payload. E63 evidence: focused `18 passed in 0.47s`; full Qt
`1670 passed, 34 skipped, 34 subtests passed in 198.85s`; standard/eager Editor
smokes `13/20` and `20/20`; four guardrails and independent signature `2 passed
in 0.27s` pass.

Execute exactly E64: audit central viewport/tab projection and fallback
registration/switch/removal/state behavior. Preserve the sole LegacyEditorPluginAdapter,
RuntimePluginHost, .pond, Inspector bindings, SR2D, SR/PS, Player/export, and
renderer policy. Do not add a Host, registry, renderer, UI framework, widget DSL,
or app shell. Close with focused and full evidence, docs, and exactly one next gate.
