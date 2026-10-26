# E273 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E274 -- Route the separate pond serializer hydration path through the domain adoption API with `.pond` compatibility proof**

## 已完成上下文

- E270：MemoryEditor.import_memory() 通过 `memory.store` Registry 命令。
- E271：完成运行时 lifecycle mutation authority 盘点。
- E272：新增 `MemorySystem.adopt_memory()`，并迁移 runtime-memory inheritance。
- E273：`OrganismSerializer.deserialize_organism()` 已通过 `adopt_memory(memory, enforce_capacity=False)` hydration；保留字段、顺序、strength/age 和超容量持久化载入语义。
- 最新 E273 证据：focused chain **36 passed**；audit guard passed；scoped py_compile passed；`git diff --check` passed；`unified_undo_redo_runtime=false`。

## E274 边界

1. 阅读 `AGENTS.md`、E271/E272/E273 plans、`pond_serializer.py`、`PondSerializer` 相关 tests 和 `.pond` 文档。
2. 只迁移 pond serializer 的 runtime `memories` hydration direct append，使用 `MemorySystem.adopt_memory(..., enforce_capacity=False)` 保持 persisted collection 完整载入。
3. 必须验证 `.pond` serialize/deserialize 字段、顺序、strength/age、空/缺失 memories、非法条目降级与现有错误处理不变。
4. 不修改 organism serializer、继承、simulation learning、PS/SR parallel memory models 或 CommandRegistry history。
5. 运行 focused tests、audit guard、scoped py_compile、`git diff --check`，更新主线状态和下一 fresh-session prompt。

## 禁止事项

- 不改变 `.pond` schema 或 scene semantics。
- 不把 hydration 写入 editor undo/redo；`unified_undo_redo_runtime` 必须保持 `false`。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不修复 Conda/uv 混合环境；继续使用项目 `.venv\\python.exe`，不运行 `uv sync`，不修改 `uv.lock`。

## 输出要求

使用简体中文，说明实现、证据、边界和唯一下一 gate。
