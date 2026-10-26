# VitaLoom E280 fresh-session prompt

继续 VitaLoom 重构主线，不要宣称整体完成。

当前门：E280 已完成。Organism 组件图与膜引用的生产恢复已收敛到 `replace_components()` / `set_membrane()`；保留公开 `components` dict identity、组件 parent links、组件 ID 唯一性、`.pond` 与 legacy serializer 兼容，以及 membrane organism_id 绑定。

证据：E280 聚焦 PS/SR/persistence 链 **62 passed**；AI command audit 通过且 `unified_undo_redo_runtime=false`；scoped `py_compile` 通过；`git diff --check` 通过。runtime 中 Organism 组件 dict 直接替换/写入只剩 owner API 内部，serializer 不再直接重建 dict。

下一唯一 gate：E281——审计 Organism/Entity 的生命周期标志与 age/generation/offspring 统计状态，明确哪些是 simulation lifecycle、哪些是 persistence hydration，继续收敛 owner boundary，但不要 commandize runtime lifecycle。

继续使用项目现有 `.venv\\python.exe`，不要运行 `uv sync`、重建环境、切换 Conda/uv、修改 `uv.lock`，也不要清理既有临时文件。
