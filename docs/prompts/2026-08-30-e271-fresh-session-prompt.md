# E271 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E272 -- Introduce a domain-owned MemorySystem adoption API and route runtime-memory inheritance through it**

## 已完成上下文

- E270：MemoryEditor.import_memory() 已通过 `memory.store` Registry 命令，支持 guarded collection snapshot、容量淘汰后的精确 undo/redo 和失败回滚。
- E271：完成运行时记忆 mutation authority 盘点，区分编辑器 mutation 与 simulation/inheritance/hydration/decay/reset/SR lifecycle。
- E271 结论：不要把运行时生命周期 mutation 伪装成 CommandRegistry editor history；下一步只收敛 `MemorySystem` 的领域接纳协议，并先替换继承路径的直接列表 append。
- 当前证据：E270 focused chain **49 passed, 6 subtests passed**；audit guard passed；`unified_undo_redo_runtime=false`。

## E272 边界

1. 阅读 `AGENTS.md`、E271 plan、`core/Lotucosm/memory.py`、`builtin/systems/inheritance.py` 与现有记忆测试。
2. 设计小而明确的 `MemorySystem` domain-owned adoption API（例如接纳已有 `MemoryGene`，保留容量淘汰语义，并明确对象所有权/复制策略）。
3. 将 `InheritanceSystem._inherit_runtime_memories` 的直接 `child.memory_system.memories.append(clone)` 改为该 API。
4. 保持继承概率、clone 强度衰减、容量淘汰、列表/对象语义和异常行为可验证；不接入 CommandRegistry。
5. 添加 focused regression tests，运行相关测试、audit guard、scoped py_compile、`git diff --check`，更新主线状态和下一个 prompt。

## 禁止事项

- 不把 simulation learning、inheritance、serializer hydration、decay/reset 或 SR `sr_memory_genes` 纳入 editor undo/redo。
- 不修改 `.pond` schema、AI command registry、Inspector、SR2D adapter、manifest 或 Qt-free engine contracts。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不修复 Conda/uv 混合环境；继续使用项目 `.venv\\python.exe`，不运行 `uv sync`，不修改 `uv.lock`。
- `unified_undo_redo_runtime` 必须保持 `false`。

## 输出要求

使用简体中文，说明实现、证据、未完成边界和唯一下一 gate。
