# VitaLoom E285 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E285 已完成。SR→PS WorldBridge 运动状态已优先通过 `EntityBase.restore_motion_state()` 原子恢复；simple doubles 保留兼容回退，PS→SR 仍是显示投影边界。

证据：WorldBridge focused chain **21 passed**；targeted `py_compile`、`git diff --check` 通过；AI command audit 通过且 `unified_undo_redo_runtime=false`。

下一唯一 gate：E286——审计 WorldBridge 剩余 dead/size/radius 与组件投影的跨 lane 写入和兼容性边界。

继续使用项目现有 `.venv\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
