# Fresh-session handoff: E87 complete; E88 in progress

Repository root: <repository-root>

E87 is complete. The legacy PluginRuntimeOpsMixin now catches only thrown public reload_plugin(), unload_plugin(), and post-command sync_plugins_for_project() calls after capability resolution. Resolver/interface failures remain visible. Reload/unload stop before refresh; a Project World enable/disable persistence success remains successful when subsequent runtime sync is unavailable.

E87 evidence: red 4 failed, 1 passed in 0.29s; focused 5 passed in 0.17s; Runtime Ops/legacy adjacency 22 passed in 0.65s; Hot Reload adjacency 19 passed in 0.82s; source compilation and changed-file whitespace pass; fresh root offscreen smoke plugins=13/20; project-model/core/GUI/release guardrails pass; independent signatures 2 passed in 0.23s using D:\app\anaconda3\python.exe. E68 remains the broad proof: 1678 passed, 34 skipped, 34 subtests; regular/eager smoke 13/20 and 20/20.

The one active gate is E88 -- Project Manager Public Plugin Lifecycle Call-Failure Semantics Audit. Read docs/superpowers/plans/2026-07-30-project-manager-public-plugin-lifecycle-call-failure-semantics-audit.md and start at FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_manager.py. Audit public scan_project_addons() and sync_plugins_for_project() calls during project-open and project-close, including lifecycle reports/events and resolver/interface visibility. Do not introduce private state, an extra sync path, cache, fallback authority, or a second Host.

Use .venv\python.exe -B and QT_QPA_PLATFORM=offscreen plus PYTHONDONTWRITEBYTECODE=1 for Qt tests. Never use py_compile; source checks use compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec'). Signature proof uses D:\app\anaconda3\python.exe because .venv lacks cryptography. Do not install dependencies without approval.

Known environment fact: an isolated tests/test_editor_kernel_plugin_host_capability.py run is stuck without output. It is not a pass. Terminate only its currently re-verified repository test PID after explicit user approval; do not kill Python processes by image name. QPainter remains default; OpenGL/native is not default-ready. Preserve FrameCore -> lotucosm-vitaloom -> RuntimePluginHost -> LegacyEditorPluginAdapter -> LayoutManager, .pond, Project World, Inspector command binding, SR2D, SR/PS, Player/export, manifests, public imports, and MRO. Do not stage, commit, push, reset, restore, clean, or delete user work. Do not claim whole-refactor completion.
