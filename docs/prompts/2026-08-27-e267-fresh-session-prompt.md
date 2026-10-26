# E267 fresh-session prompt

E267（Inspector Qt-free CommandRegistry Authority Migration）已完成并闭环。

已交付：

- Inspector 不再拥有或引用私有 `CommandStack`；兼容类仍保留给其他消费者。
- 新增 `core/VitaLoom/inspector/transient_property.py`，支持对象、dict、位置轴和嵌套脚本属性，读取阶段不产生副作用。
- `CommandRegistry` 提供 transient target token；`inspector.set_property` 通过 Qt-free Registry 执行，并用 expected state 做 guarded undo/redo。payload/history 只含 token、路径、presence 和 JSON-safe 值，不含目标对象。
- stale、缺失 token、无效路径和写入错误都失败闭环，不产生部分 mutation。非项目 transient 目标不写 durable project audit。
- active `.pond` 的 entity/transform/script/connection 命令路径保持不变。

证据：E267 focused chain **28 passed**；语义命令/审计回归 **6 passed、6 subtests passed**；status guard、scoped `py_compile`、`git diff --check` 均通过。

环境按用户决定保持不变：使用项目 `.venv\python.exe`，不重建环境、不运行 `uv sync`、不重装依赖、不切换解释器、不修改 `uv.lock`。

下一步只做 E268：盘点 SceneViewport/其余 legacy mutation authority，选择下一个结构性迁移；不要把 `unified_undo_redo_runtime` 标为完成。
