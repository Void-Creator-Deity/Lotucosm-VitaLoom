# E276 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E277 -- Audit remaining direct mutation in PS/SR non-memory state and define the next domain boundary**

## 已完成上下文

- E270：MemoryEditor.import_memory() 通过 `memory.store` Registry 命令。
- E271：完成 runtime lifecycle mutation authority 盘点，明确不把 simulation/inheritance/persistence hydration 伪装成编辑器 undo/redo。
- E272：新增 `MemorySystem.adopt_memory()`，迁移 runtime-memory inheritance。
- E273/E274：organism 与 pond runtime-memory hydration 使用 adoption API，并有兼容性回归。
- E275：PS `Organism.memory_genes` 生产写入通过 `adopt_memory_gene()` / `replace_memory_genes()` 收敛。
- E276：SR `sr_memory_genes` 通过 bridge-owned `adopt_entity_memory_gene()` / `replace_entity_memory_genes()` 收敛；保留 SR2D public list seam、32 项容量、同情境更新与继承返回值。
- 最新 E276 证据：focused SR/PS chain **46 passed**；scoped SR py_compile passed；audit guard passed；`git diff --check` passed；SR 直接 append/replace 仅剩 bridge owner 内部；`unified_undo_redo_runtime=false`。

## E277 边界

1. 先阅读 `AGENTS.md`、E271–E276 plans/status/prompts，并对 PS/SR runtime 做非 memory state mutation inventory。
2. 分类位置、速度/加速度、能量/健康、组件图、导航/发育/社会状态、SR debug/trace 与 serializer/adapter 写入。
3. 只选一个有证据、边界清晰的下一 mutation authority；不能泛化重写所有生命周期，也不能破坏 `.pond`、SR2D 或 Qt-free contracts。
4. 先创建 E277 phase plan，再实现并提供对应行为/兼容性证据。
5. 继续使用项目 `.venv\python.exe`；不要修复 Conda/uv 混用，不运行 `uv sync`，不修改 `uv.lock`。

## 禁止事项

- 不把 runtime lifecycle 写入 editor undo/redo；`unified_undo_redo_runtime` 必须保持 `false`。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不迁移到 Unity、Godot、Unreal、Electron 等外壳。

## 输出要求

使用简体中文，说明 mutation inventory、唯一下一 gate、验证结果和边界。
