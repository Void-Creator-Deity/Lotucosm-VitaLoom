# PVAEC 遗传对齐：PS `InheritanceSystem` vs SR 膜繁殖

> **性质**：字段级差距调研，供 ADR-0001 Phase C 与 phylogeny 统一路线图使用。  
> **Ontogeny（S0–S4）** 见 [adr/0004-pvaec-developmental-ladder.md](adr/0004-pvaec-developmental-ladder.md)——与本文 **正交**。

---

## 1. 两条繁殖路径

```text
PS 批处理轨                          SR 播放轨
PVAECOrchestrator.run_cycle          GameViewport tick + EvoCentralBrainPvaec
  → SelectionSystem / reproduce        → _try_reproduce(ctx, ent)
  → InheritanceSystem.inherit()        → spawn_requests + membrane_spawn_spec
  → Organism 子代                      → 宿主 _process_organism_with_membrane_spawn
```

读模型已部分统一：`EcologySnapshot` / `collect_ecology_snapshots`（ADR-0001 C.0）。**遗传写入路径仍双轨**。

---

## 2. 总览对照表

| 维度 | PS · `InheritanceSystem.inherit` | SR · `EvoCentralBrainPvaec._try_reproduce` | 对齐状态 |
|---|---|---|---|
| 入口类 | `builtin/systems/inheritance.py` | `workspace/.../evo_central_brain_pvaec.py` | ❌ 双实现 |
| 子代类型 | `Organism` + 组件图 | SR 实体 + 膜拓扑 + 脚本 props | ❌ 模型不同 |
| 世代 | `generation = parent + 1` | `spawn_requests[-1]["generation"]` | ✅ 语义一致 |
| 能量/代谢 | `health`, `max_energy` 等拷贝 | 亲本 `*0.52 - birth_cost`；子 `initial_energy` | ⚠️ 公式不同 |
| 先天组件 | `_inherit_components` congenital 95% | 膜模板由场景 `sr_membrane_template` | ⚠️ 无组件 ID 对应 |
| 后天组件 | acquired 30% | 无 | ❌ SR 无 |
| MemoryGene | `_inherit_memory_genes` copy×率×mutate | `initial_memory_genes` + `sr_memory_genes`（Phase B） | ⚠️ 结构已对齐，EMA 仍并行 |
| MemorySystem 运行时记忆 | `_inherit_runtime_memories` | `initial_memory` 三键 EMA 衰减 | ⚠️ 结构不同 |
| 可演化标量 | `evolvable_traits` + Gaussian | `mind_dict_mutate(gene_keys=profile.gene_keys)` | ✅ Phase C |
| 膜 signal 边权 | 无 | `parent_signal_edges` / `edge_mutation_sigma` | ❌ PS 无 |
| MindProfile | 无直接对象 | 整表 `mind` dict + 子集突变 | ⚠️ SR 独有 |
| Ontogeny stage | `reset_ps_developmental_for_child` → S0 | ADR-0004：`initial_stage: 0` | ✅ PS/SR 均已强制 S0 |
| 变异 | `_apply_mutation` 组件级 | `mutation_sigma` on mind + 边权 | ⚠️ 粒度不同 |
| 配置来源 | `evolution_defaults` + 编排器 | `props.evo` + `EvolutionProfile` 合并 | ✅ Phase C |

---

## 3. PS 遗传字段明细

### 3.1 `InheritanceSystem.inherit(parent, position)`

| 步骤 | 字段 / 行为 | 默认参数 |
|---|---|---|
| 构造子代 | `organism_id`, `position`, `generation+1` | — |
| 生命属性 | `max_energy`, `max_health`, `health×0.9`, `mutation_rate`, `inheritance_rate`, `energy_consumption_rate` | 来自父代 |
| 组件 | `_inherit_components` | congenital 0.95 / acquired 0.30 |
| 代际记忆 | `_inherit_memory_genes` | 率 0.8 × `strength`；`copy()` + 可选 `mutate()` |
| 运行时记忆 | `_inherit_runtime_memories` | 同上；`strength×0.8` |
| 性状 dict | `_inherit_evolvable_traits` | Gaussian σ≈10% |
| 组件变异 | `_apply_mutation` | `mutation_rate` 0.01 |

### 3.2 `MemoryGene`（PS）

| 字段 | 含义 | SR 对应 |
|---|---|---|
| `situation` | 情境字符串 | 无 |
| `action_pattern` | 工具/控制 dict | 无 |
| `success_rate` | 0–1 | 无 |
| `strength` | 遗传概率权重 | 无 |
| `copy()` / `mutate()` | 代际 | SR：`mind_dict_mutate` 仅 3 键 |

---

## 4. SR 繁殖字段明细

### 4.1 `_try_reproduce` → `spawn_requests[-1]`

| 字段 | 来源 | PS 对应 |
|---|---|---|
| `hub_id` | 本地序号 | `organism_id` |
| `position` / `radius` | 亲本偏移 | `position` |
| `generation` | `parent+1` | ✅ |
| `energy` | `initial_energy` | 部分（非 inherit 公式） |
| `parent_hub_id` | 亲本 id | 无 |
| `parent_signal_edges` | chemo 膜边 | 无 |
| `edge_mutation_sigma` | `evo.mutation_sigma` | 无 |
| `scripts[].properties.mind` | `mind_dict_mutate(GENE_KEYS)` | 部分 ≈ `evolvable_traits` |
| `scripts[].properties.initial_memory` | EMA × `(1-mem_decay)` | ≈ runtime memory 衰减拷贝 |
| `scripts[].properties.developmental` | `{enabled, initial_stage:0}` | `Organism.developmental_*` + `developmental_profile` | ✅ ontogeny 双轨 |
| `scripts[].properties.social` | `{enabled}` S3+ 社会学习 | `Organism.social_learning_enabled` | ✅ 双轨 |
| `scripts[].properties.evo` | 复制亲本 evo 块 | 无直接对应 |

### 4.2 `GENE_KEYS`（SR 可演化子集）

```text
wander_amp | gain_high_stress | mem_alpha
```

PS `evolvable_traits` 为开放 dict，**无固定键表**。

---

## 5. 语义差距（产品叙事）

| 仓库叙事 | PS | SR | 风险 |
|---|---|---|---|
| 「继承算法」 | MemoryGene + 组件 + 率控变异 | mind 3 键 + 膜边 + EMA | 用户以为 SR ▶ 即完整遗传 |
| 「子代须重新验证」 | ADR-0004：`developmental_ladder_enabled` 时 S0 重启 | ADR-0004：spawn `initial_stage:0` | 默认关 ladder 时两轨仍「全能力出生」 |
| 「代际记忆」 | `memory_genes` + 编排器 | `initial_memory` 非 MemoryGene | 文档已警告（experiment_guide） |

---

## 6. 建议对齐路线（非本 ADR 承诺）

| 阶段 | 动作 | 产出 |
|---|---|---|
| **A** | EcologySnapshot 扩展 `generation`, `memory_gene_count`, **发育/verify 字段** | 见 [pvaec_comparability_research.md](pvaec_comparability_research.md) §3 |
| **A′** | PS verify 三分与 SR 对齐 | 同上 §2；`use_verify_triple` 配置 |
| **B** | SR spawn 可选序列化 `MemoryGene` → `initial_memory_genes` props；宿主注入 | ✅ `sr_memory_gene_bridge.py` + Evo 繁殖 |
| **C** | 统一 `EvolutionProfile` JSON（`mutation_rate`, `gene_keys`, `memory_*`） | ✅ `core/Lotucosm/evolution_profile.py` |
| **D** | ADR-0001 C.4 评审：单 Pond 驱动或 spawn→Organism 适配器 | 单 tick 遗传 |

---

## 7. 映射建议（字段级 target）

| PS 概念 | SR target（建议名） | 备注 |
|---|---|---|
| `memory_genes[]` | `spawn.properties.memory_genes` | JSON 序列化 MemoryGene |
| `evolvable_traits` | 扩展 `GENE_KEYS` 或共用 `evolution_profile.gene_keys` | 避免双表 |
| `congenital components` | `membrane_template` + `parent_signal_edges` | 拓扑等价，非 class 等价 |
| `mutation_rate` | `evo.mutation_sigma` + `edge_mutation_sigma` | 需换算文档 |
| `inheritance_rate` | `evo.mem_decay` 反函数？ | **勿**硬等同，仅文档说明 |

---

## 8. 相关代码路径

| 路径 | 职责 |
|---|---|
| `runtime/builtin/systems/inheritance.py` | PS 遗传 |
| `runtime/builtin/systems/pvaec_orchestrator.py` | PS 世代编排 |
| `runtime/core/Lotucosm/memory.py` | MemoryGene |
| `runtime/core/Lotucosm/sr_mind_gene.py` | SR mind 突变 |
| `workspace/.../evo_central_brain_pvaec.py` | SR 繁殖 |
| `runtime/core/Lotucosm/ps_developmental.py` | PS ontogeny |
| `runtime/core/Lotucosm/pvaec_cycle.py` | PS 六步 + developmental 钩子 |
| `runtime/core/Lotucosm/social_memory.py` | PS 社会学习（S3+ MemoryGene） |
| `runtime/core/Lotucosm/runtime/ecology_observation.py` | 观测接缝 |

---

## 9. 文档维护

- **版本**：v1.3（2026-06-12）— Phase A′ verify 对齐、可比性专项文档；PS ontogeny 已落地。
- **更新时机**：EcologySnapshot 发育字段、PS verify 三分落地后修订 §2–§6。
