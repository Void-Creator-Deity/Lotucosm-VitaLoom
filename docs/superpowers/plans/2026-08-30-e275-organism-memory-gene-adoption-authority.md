# E275 -- Organism Memory-Gene Adoption Authority

## Goal

将 PS `Organism.memory_genes` 的生产写入统一收敛到 organism-owned adoption API，消除 runtime 生产代码对该列表的散落 append/replace，同时保持代际遗传、社会学习、simulation seed 与 `.pond`/organism JSON hydration 语义不变。

## Inventory evidence

当前 runtime 中 `memory_genes` 有以下写入者：

- `InheritanceSystem._inherit_memory_genes()`：继承生命周期，创建 copy/mutate 后写入子代。
- `social_memory.observe_peer_action()` 与 `inherit_social_memory_genes()`：PS 社会学习/继承生命周期，写入同一 PS 列表。
- `simulation.create_test_organism()`：PS simulation seed。
- `PondSerializer.deserialize_organism()` 与 `OrganismSerializer.deserialize_organism()`：持久化 hydration；必须保留 payload 顺序、字段转换和 malformed-entry 降级。

SR `sr_memory_genes` 是另一实体模型，继续由 `sr_memory_gene_bridge` 管理，本阶段不与 PS 列表合并。

## Implementation

1. 在 `builtin.entity_types.organism.Organism` 增加 `adopt_memory_gene()` 与 `replace_memory_genes()`。
2. API 在 mutation 前验证 `MemoryGene` 类型；`replace_memory_genes()` 先 materialize/验证全部输入再替换，避免半更新。
3. 将上述 PS runtime writers 路由到 API；保留 public `memory_genes` list 读取兼容性。
4. 不改变 inheritance probability/mutation、social filtering、simulation seed、serializer payload shape、顺序、字段默认值或错误降级。
5. 为 API、各写入生命周期及 hydration 增加 focused regressions。

## Non-goals

- 不把 simulation/inheritance/social learning/persistence hydration 写入 CommandRegistry undo/redo。
- 不修改 SR `sr_memory_genes` bridge、`.pond` schema、Scene semantics、MemorySystem runtime cache 或 Conda/uv 环境。
- 不删除 public `memory_genes` list seam；本阶段只收敛生产写入权威。

## Evidence required

- focused PS memory-gene/serializer/inheritance/social tests pass。
- source search shows no production `memory_genes.append` or serializer `memory_genes = []` outside the Organism owner API (tests may construct fixtures directly).
- audit status remains passed with `unified_undo_redo_runtime=false`.
- scoped py_compile and `git diff --check` pass.

## Exactly one next gate

E276 -- audit remaining SR `sr_memory_genes` mutation ownership and decide whether its bridge needs an equivalent entity-owned boundary.
