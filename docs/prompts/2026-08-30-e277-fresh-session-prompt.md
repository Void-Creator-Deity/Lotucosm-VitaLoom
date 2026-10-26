# VitaLoom E277 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E277 已完成。`EntityBase.restore_motion_state()` 现在是 runtime 三元运动状态恢复边界；`PondSerializer.deserialize_organism()` 已通过该 API 恢复 `.pond` 中的 position/velocity/acceleration。保持 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。

证据：E277 聚焦 persistence/PS/SR 链 **54 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。

下一唯一 gate：E278——审计并收敛非 memory 的 PS/SR 状态写入（优先 energy/health 或 component graph，先做 inventory 再选一个边界）。不要把 editor-host `cell_simulation_plugin` 直接迁入 runtime authority，也不要把 simulation/inheritance/persistence hydration commandize 成编辑器 undo/redo。
