# E291 Fresh Session Prompt

继续 VitaLoom E292 persistence hydration authority 审计。保持产品 runtime 边界 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`；使用现有 `.venv\python.exe`，不要重建环境、不要运行 `uv sync`、不要切换 Conda/uv、不要改 `uv.lock`。

E291 已完成：`GameViewport._SceneRuntimeEntity` 获得 motion/radius/energy/generation owner API；WorldBridge 对真实 SR entity 优先使用这些 API，legacy/simple doubles 才回退字段写入。Focused chain 为 36 passed。

下一步：分类审计 `builtin/systems/organism_serializer.py` 与 `builtin/systems/pond_serializer.py` 的构造、持久化恢复和 simulation mutation，避免把构造期/恢复期误当实时 bridge authority。为实际发现补最小端到端实现与测试；完成后更新 phase plan、`docs/mainline_status.md`，保持 exactly one next gate。不得声称 `unified_undo_redo_runtime=true`，不得破坏 `.pond`、CommandRegistry/Inspector、SR2D public seams 或 manifest。
