# E274 -- PondSerializer MemorySystem Hydration Adoption Route

## Goal
将 `.pond`/PondSerializer 的运行时记忆 hydration 写入收敛到 `MemorySystem.adopt_memory()`，消除最后一处 serializer 对 `memories` 列表的直接 append，同时提供 `.pond` 兼容性证据。

## Scope
- 仅修改 `builtin/systems/pond_serializer.py` 的 runtime `memories` hydration。
- 使用 `adopt_memory(memory, enforce_capacity=False)`，保持持久化集合完整载入。
- 添加 PondSerializer round-trip、字段顺序、strength/age、缺失/空 memories 与非法条目回归测试。

## Non-goals
- 不修改 organism serializer、继承、simulation learning、decay/reset、PS `memory_genes` 或 SR `sr_memory_genes`。
- 不修改 `.pond` schema、场景语义、Registry undo/redo 或 durable audit。
- 不修复 Conda/uv 混合环境，不重建 `.venv`，不运行 `uv sync`，不修改 `uv.lock`。

## Implementation
1. 审核 PondSerializer 的 serialize/deserialize 数据形状与错误降级。
2. 替换唯一 runtime `memories.append` 为 domain adoption API，并关闭运行时容量淘汰以保留 hydration 语义。
3. 覆盖有记忆、无记忆、非字典条目跳过、字段/顺序/strength/age 往返及 malformed entry 失败行为。
4. 运行 focused tests、audit guard、scoped py_compile、git diff --check 与 direct-write 搜索。
5. 更新主线状态和下一 fresh-session prompt。

## Evidence required
- PondSerializer 与既有 memory/inheritance/organism serializer focused tests 全部通过。
- `.pond` payload shape 未变，`unified_undo_redo_runtime=false`，audit guard 通过。
- scoped py_compile 与 `git diff --check` 通过。
- runtime 中不再存在 `memory_system.memories.append` 直接写入。

## Exactly one next gate
E275 -- inventory and consolidate remaining direct mutation surfaces beyond MemorySystem hydration
