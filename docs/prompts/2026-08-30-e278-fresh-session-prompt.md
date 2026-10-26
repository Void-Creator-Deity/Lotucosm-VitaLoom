# VitaLoom E278 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E278 已完成。PS `Organism` 的生产 energy 写入已收敛到 `set_energy()`；代谢、繁殖、组件捕获、死亡归零和 gain/consume 均通过 owner API。保留 simulation/inheritance lifecycle，不写入 editor CommandRegistry history。

证据：E278 聚焦链 **62 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。生产 runtime 中 organism energy 直接赋值/增减只剩 owner API 内部；Food 独立资源能量、实验 runner seed helper 和 WorldBridge 兼容桥接不属于本 gate。

下一唯一 gate：E279——审计并收敛 PS/SR 的 health/dead 状态写入，先区分 organism owner、serializer hydration、WorldBridge compatibility bridge，再实现一个不改变现有生命周期语义的边界。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
