# Fresh-session prompt: E63 legacy Editor shell command projection boundary discovery

Continue VitaLoom after E62. E62 audited `EditorKernel`/`LayoutManager` and
implemented only `EditorLayoutState`, a frozen Qt-free JSON-safe value object
for persisted `window_state`, geometry, dock state, and viewport state.
`LayoutManager` remains the concrete Qt capture, file-I/O, and state-apply
authority. Runtime plugin lifecycle and command ownership remain singular in
`RuntimePluginHost`; `LegacyEditorPluginAdapter` remains the sole concrete Qt
payload projection route.

Latest evidence: portable-layout and LayoutManager proof `12 passed in 0.67s`;
expanded state/Adapter/contribution proof `22 passed in 0.95s`; full project
local Qt regression `1669 passed, 34 skipped, 34 subtests passed in 198.22s`;
standard/eager Editor smokes `13/20` and `20/20`; all four guardrails pass;
independent signature-only `2 passed in 0.22s`. QPainter remains the default:
the OpenGL worker texture-blit route still lacks native geometry acceleration
and its recorded speedup is only `0.0182x`. Do not claim OpenGL default-ready.

Execute exactly one next gate: E63 Legacy Editor Shell Command Projection
Boundary Discovery. Trace Host-copied editor contributions through
`LegacyEditorPluginAdapter` into `LayoutManager` `QAction`/menu/toolbar
projection, trigger binding, and unload cleanup. Audit authority first; choose
at most one smallest portable fact or regression only when it preserves the
single `RuntimePluginHost` command authority and the sole Qt Adapter. Do not
introduce a replacement Editor Host, another command registry, event bus,
renderer, UI framework, widget DSL, application shell, or peer engine root.
Preserve `.pond`, Project World, Inspector binding, SR2D, SR/PS, Player/export,
package/signature behavior, public imports, and entity/component MRO.

Before closing E63: update its plan, docs/mainline_status.md, CONTEXT.md, docs
INDEX, and a fresh-session prompt; run focused lifecycle proof, full local Qt
non-signature regression, standard/eager smokes, four guardrails, `git diff
--check`, and the independent signature collection. Record skips/blockers with
fallback and unblock path, and name exactly one next gate.
