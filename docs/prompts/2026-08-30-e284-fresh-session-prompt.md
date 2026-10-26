# VitaLoom E284 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E284 已完成。组件持久化恢复已统一到 `Component.restore_persistent_state()`，Pond/FloatingSystem 漂浮列表 hydration 已统一到 owner API，并保持 list identity、组件公开 seam、`.pond` schema 和 simulation/editor 边界。

证据：E284 聚焦链 **30 passed**；新增原子恢复、专用字段恢复、浮动列表 identity 和非法条目回归；AI command audit 通过，`unified_undo_redo_runtime=false`；targeted `py_compile` 与 `git diff --check` 通过。

下一唯一 gate：E285——审计并收敛剩余 runtime WorldBridge 跨 lane 状态写入与兼容性边界，再进入 UI/OpenGL/native SR2D 的证据闭环。

继续使用项目现有 `.venv\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
