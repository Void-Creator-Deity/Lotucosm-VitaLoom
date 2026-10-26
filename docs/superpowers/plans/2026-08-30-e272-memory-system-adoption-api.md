# E272 -- MemorySystem Domain Adoption API for Runtime Inheritance

## Goal
收敛运行时 MemorySystem 的领域接纳边界，消除继承路径对 `memories` 列表的直接 append，同时不把生命周期 mutation 伪装成编辑器 CommandRegistry history。

## Scope
- 在 `core/Lotucosm/memory.py` 增加 `MemorySystem.adopt_memory(MemoryGene)` 领域 API。
- 让 `MemorySystem.store()` 复用该 API，保持原有构造、容量淘汰和排序语义。
- 将 `InheritanceSystem._inherit_runtime_memories()` 的直接列表写入改为 `adopt_memory()`。
- 添加类型拒绝、容量策略、对象所有权和继承行为回归测试。

## Non-goals
- 不接入 CommandRegistry、undo/redo 或 durable audit。
- 不改变继承概率、clone 强度衰减、mutation rate 或 `.pond` 语义。
- 不修改 serializer hydration、simulation learning、decay/reset、PS `memory_genes` 或 SR `sr_memory_genes`。
- 不修复 Conda/uv 混合环境，不重建 `.venv`，不运行 `uv sync`，不修改 `uv.lock`。

## Implementation
1. 定义 `adopt_memory()` 的输入类型、对象所有权和容量策略契约。
2. 让 `store()` 委托领域接纳 API，避免两个容量实现漂移。
3. 替换 runtime inheritance 的直接 append。
4. 用 focused tests 验证最弱淘汰、传入对象不隐式 copy、非法输入无 mutation，以及既有继承回归。
5. 运行 focused tests、audit guard、scoped py_compile、git diff --check，并更新文档。

## Evidence required
- 记忆/继承 focused tests 全部通过。
- audit status guard 通过，且 `unified_undo_redo_runtime=false`。
- scoped `.venv/python.exe -m py_compile` 通过。
- `git diff --check` 通过。
- 源码搜索确认继承路径不再直接写 `child.memory_system.memories.append(...)`。

## Exactly one next gate
E273 -- route one persistence hydration path through MemorySystem.adopt_memory without changing `.pond` semantics
