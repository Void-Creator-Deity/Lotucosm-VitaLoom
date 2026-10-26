# Fresh-session prompt: E65 legacy Editor shell dock-layout projection audit

Continue after E64. E64 fixed falsey-empty-QTabWidget behavior: EditorKernel now
installs the actual tab container and LayoutManager registers/switches/removes
and restores ordered tabs consistently. Latest proof: tab regression `8 passed`,
viewport lifecycle `51 passed`, full Qt `1671 passed, 34 skipped, 34 subtests`,
Editor smokes `13/20` and `20/20`, guardrails/diff/signature `2 passed`.

Execute exactly E65: audit dock registration, tabification, visibility/floating
geometry persistence, restore, and unload parity. Preserve the sole Qt Adapter
and LayoutManager, RuntimePluginHost authority, .pond, Project World, Inspector,
SR2D, SR/PS, Player/export, public imports, and rendering policy. Do not add a
new Host, command registry, renderer, UI framework, widget DSL, or app shell.
Close with evidence, docs, a fresh prompt, and exactly one next gate.
