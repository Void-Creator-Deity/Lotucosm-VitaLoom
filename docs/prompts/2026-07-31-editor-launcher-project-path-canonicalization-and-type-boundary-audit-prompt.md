# Fresh-session handoff: E99 complete

E99 is complete. `launch_editor(..., project_path=...)` now declares and enforces `str | os.PathLike[str] | None`: relative supported inputs are canonicalized to absolute strings before splash/Kernel lifecycle; `None` and `""` mean no explicit request; unsupported or bytes-returning forms raise direct `TypeError`; a `PathLike.__fspath__()` exception keeps its original identity. The Launcher remains environment-neutral and does not inspect/open projects, choose fallback, or own recovery.

Proof: red `3 failed`; focused `6 passed`; interface `30 passed`; adjacency `141 passed`; root smoke `plugins=13/20`; all four guardrails, Anaconda signatures, and scoped hygiene passed. QPainter remains default; OpenGL/native is not default-ready; whole refactor is not complete.

One active gate: **E100 -- Editor Launcher Repository-Root Plugin-Layer Boundary Audit**. Audit `repo_root`/`default_plugin_layers()` input and authority semantics without moving plugin discovery, bundle-path policy, Plugin Host lifecycle, or recovery into Launcher.