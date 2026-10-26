# E276 -- SR Memory-Gene Authority Boundary

## Goal

收敛 SR `sr_memory_genes` 的生产写入，保留 bridge 作为 SR2D 兼容边界，避免 `social_memory.py` 与 props/PVAEC 路径直接操作实体列表。

## Inventory

- `ensure_entity_memory_genes()`：当前负责 lazy-create 并返回可变 list。
- `load_sr_memory_genes_from_props()`：当前通过切片赋值 hydration，容量上限 `MAX_SR_MEMORY_GENES=32`。
- `store_sr_memory_from_pvaec()`：当前在 bridge 内更新同情境 gene，或 append 后按 strength 淘汰。
- `social_memory.observe_peer_action_sr()`：通过 ensure 后直接 append。
- `inherit_sr_memory_genes()`：构造并返回独立 child list，由 SR reproduction caller 接管。
- `social_memory.inherit_social_sr_memory_genes()`：构造并返回独立 list，不直接写实体。

## Implementation

1. 在 `sr_memory_gene_bridge` 增加 `adopt_entity_memory_gene()` 和 `replace_entity_memory_genes()`。
2. API 验证 `MemoryGene` 类型；replace 在验证完整集合后一次性替换，并保留 32 项容量裁剪语义。
3. 将 props hydration、PVAEC store 新增 gene、SR social observation 路由到 bridge owner API。
4. 保持 `ensure_entity_memory_genes()` 只作为兼容读取/lazy-init seam；不改变公开实体 `sr_memory_genes` list。
5. 保持已有 update、strength 淘汰、顺序、spawn props 以及 inheritance 返回值语义。

## Non-goals

- 不合并 PS `memory_genes`、SR `sr_memory_genes`、`MemorySystem`。
- 不将 SR lifecycle 写入 CommandRegistry undo/redo。
- 不改变 SR2D adapter public seams、spawn schema、容量常量或 Conda/uv 环境。

## Evidence required

- SR bridge/social tests and focused regression pass.
- Production source has direct SR list append/replace only inside bridge owner functions.
- audit, py_compile, diff check pass.

## Exactly one next gate

E277 -- audit remaining direct mutation in PS/SR non-memory state and define the next domain boundary.
