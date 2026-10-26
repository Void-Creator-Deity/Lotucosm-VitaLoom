# VitaLoom E286 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E286 已完成。`EntityBase.set_radius()` 已成为 size/radius 的 runtime owner API；WorldBridge 创建和显示投影优先走该 API，simple doubles 保留兼容回退；组件 projection 仍明确为 read-only。

证据：完整 WorldBridge 测试集 **351 passed、5 subtests passed**；E286 focused chain **22 passed**；`py_compile`、`git diff --check` 通过；AI command audit 通过且 `unified_undo_redo_runtime=false`。

下一唯一 gate：E287——审计 editor/UI host 边界，并准备真实 OpenGL/native SR2D 证据 gate。

继续使用项目现有 `.venv\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
