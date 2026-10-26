# E275 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E276 -- Audit remaining SR `sr_memory_genes` mutation ownership and decide whether its bridge needs an equivalent entity-owned boundary**

## 已完成上下文

- E270：MemoryEditor.import_memory() 通过 `memory.store` Registry 命令。
- E271：完成 runtime lifecycle mutation authority 盘点，明确不把 simulation/inheritance/persistence hydration 伪装成编辑器 undo/redo。
- E272：新增 `MemorySystem.adopt_memory()`，迁移 runtime-memory inheritance。
- E273：OrganismSerializer runtime-memory hydration 使用 `adopt_memory(..., enforce_capacity=False)`。
- E274：PondSerializer runtime-memory hydration 使用同一 adoption API，并有 `.pond` 兼容性回归。
- E275：新增 `Organism.adopt_memory_gene()` 与原子 `replace_memory_genes()`；PS inheritance、social memory、simulation seed、PondSerializer hydration 已通过 organism-owned API 写入。PS 与 SR memory 模型仍分离。
- 最新 E275 证据：focused PS chain **41 passed**；audit guard passed；待最终收口的 scoped py_compile 与 `git diff --check` 结果必须在本 gate内补齐；生产代码中 PS `memory_genes.append` 仅剩 owner API 内部。

## E276 边界

1. 先阅读 `AGENTS.md`、E271–E275 plans/status/prompts，以及 `core/Lotucosm/sr_memory_gene_bridge.py`、`social_memory.py` 和 SR 相关测试。
2. 建立 SR `sr_memory_genes` 的完整 mutation inventory：props hydration、remember/update、inheritance、capacity、清理/替换与所有权。
3. 只选一个有证据的下一收敛目标；不要把 PS `memory_genes`、SR `sr_memory_genes` 和 MemorySystem 合并。
4. 保持 SR2D adapter public seams、spawn props、记忆容量限制和现有 graceful degradation；不把 SR lifecycle 写入 CommandRegistry undo/redo。
5. 继续使用项目 `.venv\python.exe`；不要修复 Conda/uv 混用，不运行 `uv sync`，不修改 `uv.lock`。

## 禁止事项

- 不改变 `.pond` schema 或 scene semantics。
- 不把 runtime lifecycle 写入 editor undo/redo；`unified_undo_redo_runtime` 必须保持 `false`。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不迁移到 Unity、Godot、Unreal、Electron 等外壳。

## 输出要求

使用简体中文，说明 SR inventory 证据、唯一下一 gate、验证结果和边界。
