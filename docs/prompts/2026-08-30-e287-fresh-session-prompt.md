# VitaLoom E287 Fresh Session Prompt

继续 VitaLoom 主线重构，不要宣布整体完成。

工作目录：`<repository-root>`

上一 gate：E286 已完成 WorldBridge size/radius authority。E287 已收敛 `core.Lotucosm` 的 Qt-free boundary，并完成 editor/Inspector/Viewport 聚焦验证。

当前唯一下一 gate：E288，真实 OpenGL current-context 证据。检查 `tests/test_opengl_canvas_smoke.py`、`tests/test_viewport_pixel_parity.py`、`tests/test_viewport_interaction_continuity.py`、`tests/test_benchmark_engine_viewport_variants.py` 及对应 Host Adapter。必须有真实像素、交互、parity、benchmark；QPainter 仍为默认，除非证据满足切换政策。

约束：
- 继续使用 `.venv\python.exe`；不要重建环境、不要 `uv sync`、不要改 `uv.lock`。
- 不 stage/commit/reset/restore/clean，不删除既有临时目录。
- 保持 runtime 边界：`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`。
- 不把 simulation lifecycle 伪装成 CommandRegistry undo/redo；保持 `unified_undo_redo_runtime=false`。
- 不修改 `.pond` 语义、AI CommandRegistry、Inspector binding、SR2D public seams。
