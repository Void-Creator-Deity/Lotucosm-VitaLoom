# E273 -- OrganismSerializer MemorySystem Hydration Adoption Route

## Goal
将 legacy organism JSON hydration 的运行时记忆写入改为调用 `MemorySystem.adopt_memory()`，消除该 serializer 对内部 `memories` 列表的直接 append，同时保持原有 payload 字段、顺序、strength/age 和错误降级语义。

## Scope
- 仅修改 `builtin/systems/organism_serializer.py` 的 `memories` hydration 路线。
- 扩展 `MemorySystem.adopt_memory()` 以支持显式关闭容量约束，供 persistence hydration 保留历史“完整载入”语义。
- 增加 organism serializer round-trip、超容量 hydration 和非法条目降级回归测试。

## Non-goals
- 不修改 `pond_serializer.py`，不改变 `.pond` schema。
- 不修改继承、simulation learning、decay/reset、PS/SR parallel memory models。
- 不接入 CommandRegistry、editor undo/redo 或 durable audit。
- 不修复 Conda/uv 混合环境，不运行 `uv sync`，不修改 `uv.lock`。

## Implementation
1. 为 `adopt_memory()` 增加明确的 `enforce_capacity` 关键字参数，默认保持 E272 行为。
2. organism serializer hydration 使用 `adopt_memory(memory, enforce_capacity=False)`，避免大于 `max_memories` 的历史 payload 被静默淘汰。
3. 保持非字典条目跳过、缺字段异常捕获和已有错误返回行为。
4. 添加 focused tests 验证字段/顺序/strength/age、超过容量不丢数据、非法条目行为和源码无直接 append。
5. 运行相关测试、audit guard、scoped py_compile、git diff --check，并更新文档与下一 prompt。

## Evidence required
- serializer 与此前 MemorySystem/继承 focused tests 全部通过。
- `unified_undo_redo_runtime=false` 且 audit guard 通过。
- scoped py_compile 与 `git diff --check` 通过。
- 搜索确认 organism serializer 不再直接写 `memory_system.memories.append`。

## Exactly one next gate
E274 -- route the separate pond serializer hydration path through the domain adoption API with `.pond` compatibility proof
