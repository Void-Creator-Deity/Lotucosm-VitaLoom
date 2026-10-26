# VitaLoom E279 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E279 已完成。PS `Organism` 的 health/dead 写入已收敛到 `set_health()` / `set_dead()`；构造、死亡生命周期、PondSerializer hydration 和 SR→PS WorldBridge health 同步均通过 owner boundary（兼容 fallback 仅保留给非 Organism doubles）。保留 health clamp、dead bool 语义和 bridge 显示方向。

证据：E279 聚焦 PS/SR/persistence/bridge 链 **61 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。runtime 中 Organism health/dead 直接写入只剩 owner API 内部；SR display entity health 写入和实验 runner seed helper 属于边界外。

下一唯一 gate：E280——审计并收敛 Organism component graph（components/membrane）的 hydration 与 runtime mutation authority，保持公开 dict/list seams 和 `.pond`/legacy serializer 兼容。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
