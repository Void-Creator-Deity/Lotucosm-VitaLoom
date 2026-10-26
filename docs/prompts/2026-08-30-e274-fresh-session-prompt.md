# E274 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E275 -- Inventory and consolidate remaining direct mutation surfaces beyond MemorySystem hydration**

## 已完成上下文

- E270：MemoryEditor.import_memory() 通过 `memory.store` Registry 命令。
- E271：完成运行时 lifecycle mutation authority 盘点，并明确不把 simulation/inheritance/persistence hydration 伪装成编辑器 undo/redo。
- E272：新增 `MemorySystem.adopt_memory()`，并迁移 runtime-memory inheritance。
- E273：`OrganismSerializer.deserialize_organism()` 通过 `adopt_memory(memory, enforce_capacity=False)` hydration。
- E274：`PondSerializer.deserialize_organism()` 通过同一 adoption API hydration；补充 `.pond` runtime memory round-trip、字段顺序、strength/age、空/缺失 memories、非字典跳过与 malformed entry 降级回归。
- 最新 E274 证据：focused chain **15 passed**；combined persistence/memory chain **40 passed**；audit guard passed；scoped py_compile passed；`git diff --check` passed；runtime 无 `memory_system.memories.append` direct write；`unified_undo_redo_runtime=false`。

## E275 边界

1. 先阅读 `AGENTS.md`、E271–E274 plans/status/prompts，以及 runtime 中剩余的直接 mutation surface。
2. 只做 inventory 与 consolidation 设计，选出一个有证据、边界清晰的下一 mutation authority 收敛目标；不要泛化改造所有生命周期。
3. 明确区分 simulation lifecycle、inheritance lifecycle、persistence hydration、decay/reset、PS `memory_genes`、SR `sr_memory_genes` 与 editor CommandRegistry history。
4. 为选定目标创建独立 phase plan；实现前先记录现状、调用方、对象所有权、容量/顺序/错误语义和不变量。
5. 继续使用项目 `.venv\python.exe`；不要修复 Conda/uv 混用，不运行 `uv sync`，不修改 `uv.lock`。

## 禁止事项

- 不改变 `.pond` schema 或 scene semantics。
- 不把 runtime lifecycle 写入 editor undo/redo；`unified_undo_redo_runtime` 必须保持 `false`。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不迁移到 Unity、Godot、Unreal、Electron 等外壳。

## 输出要求

使用简体中文，说明 inventory 证据、选定的唯一下一 gate、验证结果与边界。
