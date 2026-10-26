# Fresh-session prompt: E66 legacy Editor shell restore timing and deferred plugin projection audit

Continue after E65. E65 audited the sole LayoutManager dock projection path and
fixed a real partial-layout gap: when Qt `window_state` is absent or invalid,
persisted JSON facts now restore visibility, floating/docked state, and a
validated dock area; successful `QMainWindow.restoreState()` still owns full Qt
topology and tab order. Evidence: dock regression `10 passed`, lifecycle suite
`56 passed`, full Qt `1673 passed, 34 skipped, 34 subtests`, smokes `13/20` and
`20/20`, all four guardrails and diff check; signature suite `2 passed` under
shared Python because the project `.venv` lacks `cryptography`.

Execute exactly E66: audit timing between EditorKernel startup, RuntimePluginHost
discovery, LegacyEditorPluginAdapter projection, and LayoutManager restore. Prove
whether a layout restored before all docks/viewports exist is completed
deterministically when late plugins project; make only a test-proven ordering or
idempotence repair. Preserve the one FrameCore L0, the one VitaLoom L1 runtime,
RuntimePluginHost authority, the one concrete Qt adapter/layout path, `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export, package
and public-import contracts, and current QPainter-default/OpenGL-not-default-ready
policy. Do not add another Host, registry, layout manager, renderer, UI framework,
widget DSL, or app shell. Close with evidence, status/CONTEXT/INDEX, a fresh
prompt, and exactly one next Gate.
