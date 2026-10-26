# Fresh-session prompt: E62 legacy Editor shell command-and-state boundary discovery

Continue VitaLoom after E61. E60 mapped the old PyQt6/QPainter/OpenGL Editor
host boundary; E61 removed the residual eager `QWidget` import from the optional
SR OpenGL canvas wrapper. A fresh interpreter now imports viewport selection
and the optional canvas shim without loading PyQt. Actual QOpenGLWidget probing
and canvas construction remain lazy Adapter-local behavior.

Latest evidence: fresh selection/import proof `8 passed in 0.47s`; expanded
viewport rendering/capture/parity/interaction/OpenGL/QPainter/benchmark proof
`60 passed, 2 skipped in 26.87s`; full project-local Qt regression `1663 passed,
34 skipped, 34 subtests passed in 211.84s`; standard/eager Editor smokes `13/20`
and `20/20`; all four guardrails pass; independent signature-only `2 passed in
0.67s`. A real Windows current-context probe has pixels, no fallback, and
released context. QPainter remains the default because the OpenGL worker
texture-blit route has no native geometry acceleration and showed only `0.0182x`
measured speedup in the recorded benchmark. Do not call OpenGL default-ready.

Execute exactly one next gate: E62 Legacy Editor Shell Command-and-State
Boundary Discovery. Audit the bounded EditorKernel/LayoutManager command/state
seam and select one smallest portable-fact extraction only if it preserves the
single current LegacyEditorPluginAdapter as Qt projection authority. Do not
introduce a replacement UI Host, renderer, UI framework, app shell, second
registry/command authority, or peer engine root. Preserve .pond, Project World,
Inspector command binding, SR2D, SR/PS, Player/export, manifests, and signatures.
