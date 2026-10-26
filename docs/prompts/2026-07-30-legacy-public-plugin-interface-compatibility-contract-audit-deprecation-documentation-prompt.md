# Fresh-session prompt: E60 legacy Editor host rendering boundary audit

Continue VitaLoom after E59. E58 retained the public legacy UI compatibility
surface and E59 quarantined all four legacy UI interface names to
`core/VitaLoom/kernel/plugin_interfaces.py`. Direct `IRuntimePlugin` plus
Host-copied `editor_contributions` remains the authority, while
`LegacyEditorPluginAdapter` remains the only concrete PyQt payload bridge.

Latest evidence: targeted quarantine guard `3 passed in 0.18s`; project-local
`.venv\python.exe` full non-signature Qt regression `1662 passed, 34 skipped,
34 subtests passed in 165.59s`; all four guardrails pass. Standard/eager Editor
smokes passed in E58 (`13/20`, `20/20`). Package-signature coverage remains
independently `2 passed in 0.27s` in the shared interpreter; `.venv` lacks
`cryptography` for that single collection.

Execute exactly one next gate: E60 Legacy Editor Host Rendering Boundary
Discovery and Migration-Readiness Audit. Map PyQt6/QPainter/OpenGL host seams,
classify Qt-free versus host-coupled responsibilities, and produce an
evidence-backed incremental migration plan. Do not introduce or claim a new UI
Host, renderer, UI framework, app shell, native acceleration, OpenGL
default-readiness, or whole-engine completion without concrete build/import,
pixel-parity, interaction, and benchmark proof.