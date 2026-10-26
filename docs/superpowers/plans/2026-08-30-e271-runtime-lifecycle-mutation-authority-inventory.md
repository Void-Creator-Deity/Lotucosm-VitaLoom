# E271 -- Runtime Lifecycle Mutation Authority Inventory

## Goal
在 E270 之后建立完整、可验证的运行时记忆 mutation authority 盘点，区分编辑器命令缺口与有意保留的领域生命周期写入，并只选择一个下一步结构目标。

## Evidence inventory

| 路线 | 当前写入 | 调用上下文 | authority 分类 | 是否纳入 Registry undo/redo |
|---|---|---|---|---|
| `MemoryEditor.edit_memory` | `memory.edit` | 编辑器属性编辑 | editor mutation | 已纳入 |
| `MemoryEditor.import_memory` | `memory.store` | 编辑器显式导入 | editor mutation | 已纳入 |
| `PVAECCycle.update_memory` | `MemorySystem.store` | 每轮模拟验证后的学习 | simulation lifecycle | 不纳入；保持运行时顺序与容量策略 |
| `InheritanceSystem._inherit_runtime_memories` | `child.memory_system.memories.append(clone)` | 生物体繁殖/代际复制 | inheritance lifecycle | 不纳入；需要领域接纳 API，不能伪装成编辑器历史 |
| `InheritanceSystem._inherit_memory_genes` | `child.memory_genes.append(new_memory_gene)` | 代际 MemoryGene 复制 | inheritance lifecycle | 不纳入；与 SR `memory_genes` 语义分开 |
| `organism_serializer.deserialize_organism` | 新建 `MemorySystem` 后直接 append | 反序列化 hydration | persistence hydration | 不纳入；反序列化事务边界独立于 Registry |
| `pond_serializer.deserialize_organism` | 已有 `MemorySystem` 后直接 append | `.pond` hydration | persistence hydration | 不纳入；必须保持 `.pond` 语义 |
| `MemorySystem.decay_all_memories` | `MemoryGene.decay` | 运行时遗忘 | simulation lifecycle | 不纳入；不是用户编辑操作 |
| `MemorySystem.clear_memories` | list clear | 模拟 reset | lifecycle reset | 不纳入；应由 reset transaction 设计单独处理 |
| `sr_memory_gene_bridge.store_sr_memory_from_pvaec` | `sr_memory_genes` 原地更新/append/淘汰 | SR CentralBrain 学习 | SR simulation lifecycle | 不纳入；不是 PS `MemorySystem` 编辑器入口 |

## Findings

1. E270 已关闭当前 MemoryEditor 导入的 Registry bypass；搜索结果中没有发现其他 MemoryEditor/SceneViewport 对 `MemorySystem.memories` 的直接编辑入口。
2. `MemorySystem.store()` 仍有两个语义不同的调用者：E270 的显式编辑器导入，以及 `PVAECCycle.update_memory()` 的模拟学习。二者不能共享“编辑器 undo/redo”语义，否则会把每 tick 学习写入历史并破坏运行时性能/顺序。
3. 继承和 serializer 仍直接操作 `memories` 列表，但它们分别属于代际事务和持久化 hydration。当前主要结构问题是列表接纳/恢复协议重复，而不是缺少 Registry 命令。
4. PS `memory_genes`、SR `sr_memory_genes` 与 `MemorySystem.memories` 是三套并行状态；不能通过同一个命令或同一字段别名强行合并。
5. `MemoryStorage` 的 `load_memories`/`import_memories` 返回新对象列表，不直接写入 `MemorySystem`；它们是解析辅助，不是当前 mutation bypass。

## Selection

下一步只处理一个受限结构目标：为 `MemorySystem` 增加明确的运行时“接纳/恢复”领域 API，并先将 `InheritanceSystem._inherit_runtime_memories` 的直接列表 append 改为该 API。该目标不接入 CommandRegistry、不改变继承概率、不改变容量淘汰和 `.pond` 序列化格式；serializer 路线留在后续 gate。

## Non-goals

- 不把模拟学习、继承、hydration、decay、reset 记录为编辑器 undo/redo。
- 不合并 PS `memory_genes`、SR `sr_memory_genes` 与 PS `MemorySystem.memories`。
- 不修改 `.pond` schema、manifest、Qt host、WorldBridge/OpenGL/native SR2D 或 Conda/uv 环境。
- 不删除旧 `CommandStack` 兼容实现。

## Exactly one next gate

**E272 -- Introduce a domain-owned MemorySystem adoption API and route runtime-memory inheritance through it.**
