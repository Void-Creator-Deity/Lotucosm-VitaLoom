# VitaLoom E281 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E281 已完成。EntityBase 的 age 推进/恢复已通过 `set_age()` / `advance_age()`；Organism 的 generation 与 offspring_count 写入已通过 owner API；两个 serializer 的 age hydration、Organism update age 推进和 reproduction 计数已迁移。保持 memory age、editor viewport doubles、UI tool active 状态分离。

证据：E281 聚焦 PS/SR/persistence/lifecycle 链 **66 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。

下一唯一 gate：E282——审计 Organism 内部 property/state 初始化与 persistence payload 覆盖，优先统一 max_energy/energy 与 max_health/health 的构造及 hydration 原子性，避免再次扩大到 editor CommandRegistry。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
