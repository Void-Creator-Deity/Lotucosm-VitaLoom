# PVAEC 双轨可比性研究：Verify · 生态指标 · 统一世界

> **性质**：PS ontogeny 最小移植完成后的差距调研与实现基线。  
> **依据**：`pvaec_developmental_research.md` §11、§22；`pvaec_inheritance_alignment.md` §6 Phase A/D；`runtime_unification_roadmap.md` Phase C.4。  
> **状态**：PS verify 三分、EcologySnapshot 可比字段、WorldBridge 试点已落地；是否默认启用统一 Pond 仍以 ADR-0005 为准。

**关联实现（截至 2026-06-12）**

| 能力 | SR | PS |
|---|---|---|
| Ontogeny S0–S4 | `PvaecScript` + `sr_developmental_ladder` ✅ | `ps_developmental` + `PVAECCycle` ✅ |
| Verify 三分 | `pvaec_verify_triple` ✅ | `ps_verify.validate_action_triple` ✅（`use_verify_triple` 或 ladder 开启） |
| MemoryGene 遗传 | `initial_memory_genes` ✅ | `InheritanceSystem` ✅ |
| EcologySnapshot | `avg_memory_gene_count` / `avg_developmental_stage` ✅ | `avg_memory_count` / `avg_memory_gene_count` / `avg_developmental_stage` ✅ |
| 子代 S0 重启 | spawn `initial_stage:0` ✅ | `reset_ps_developmental_for_child` ✅ |

---

## 1. 研究问题

PS 批实验与 SR 场景播放**刻意不合并 tick**（ADR-0001），但维护者与用户仍需要回答：

1. **同一叙事下**，两轨的「验证成功」「发育阶段」「代际记忆」是否**语义可比**？  
2. **若不合并 tick**，能否通过统一读模型（EcologySnapshot + 实验导出）做**离线对比**？  
3. **若合并 tick**（Phase C.4），最小接缝是什么、风险边界在哪？

---

## 2. Verify 信号差距（Q8）

### 2.1 当前实现对照

| 分量 | SR（`PvaecScript.verify`） | PS（`PVAECCycle.validate_action`） |
|---|---|---|
| **Homeo** | `homeostatic_success(intero_before, intero_after)` | energy/health 差分 + 归一化项（非 intero dict） |
| **Reaff** | `reafference_consistency(velocity, motor)` | **无** |
| **Exaff** | `exafference_predictability(obs, motor, dt)` | **无** |
| **合并** | `pvaec_verify_triple` 50/25/25 | 单标量 [0,1] |
| **进阶门控** | verify ≥ 0.55 计 success（S1→S2） | 同一阈值，但 success 定义不同 ⚠️ |

**后果**：PS 在 S1→S2 的「≥5 次 verify success」与 SR **计数条件同名、异义**——批实验与 ▶ 播放的 stage 曲线**不可直接对比**。

### 2.2 PS 接入三分 verify 的可行路径

PS 已在 `enrich_ps_perception` 注入 `intero_*`；`old_perception` / `new_perception` 在 `run_cycle` 内可用。建议 **Spec v0.1**（非实现）：

```text
validate_action_ps_triple(organism, old_perception, new_perception, action, result, dt=1.0)
  homeo  ← homeostatic_success(interoception_from_environment(old), interoception_from_environment(new))
  reaff  ← reafference_consistency(pre_vel, post_vel, motor_ax, motor_ay, dt)
           motor 从 action 首组件 command/params 或 result 反推
  exaff  ← ps_exafference_predictability(old, new, action, component_ids)
           映射：component sense 标量变化 vs explore/actuator 预期
  return pvaec_verify_triple(homeo, reaff, exaff)
```

**PS 特有问题**

| 问题 | 建议 |
|---|---|
| 无 SR 式 `sensor_pull` 键 | exaff 改用 **首组件 sense 标量** + `intero_energy_norm` 变化 |
| 无统一 velocity | 从 `organism.position` 差分或 actuator `result` 中的 displacement |
| S0–S1 仅 explore | reaff 在 explore 时仍可用（速度变化 vs 随机 explore 预期） |
| 向后兼容 | `PsExperimentConfig.use_verify_triple: bool = False` 默认关 |

**验收假设**：同一 seed、`developmental_ladder_enabled=true` 下，PS 与 SR 的 **S0→S1 中位 tick** 偏差 ≤ 30%（文档约定阈值，非硬 CI）。

### 2.3 研究结论（Q8）

- **应做**：PS 复用 `sr_interoception` 的 homeo + triple 合并；exaff 需 **PS 专用键映射表**（见 §2.2）。  
- **不应做**：把 SR 的 `EXAFFERENCE_OBS_KEYS` 硬套到 component dict 上。  
- **优先级**：P1（阻塞 ontogeny 跨轨可比性）。

---

## 3. EcologySnapshot 可比性（Phase A 续）

### 3.1 已有字段

`EcologySnapshot.extras` 已承载轨特异指标：

| 键 | SR | PS | 语义对齐 |
|---|---|---|---|
| `avg_memory_gene_count` | ✅ GameViewport | ✅ `_collect_metrics` | MemoryGene 条数 |
| `avg_social_memory_count` | ✅ GameViewport | ✅ `_collect_metrics` | 社会 MemoryGene 条数 |
| `avg_memory_count` | ❌ | ✅ PsExperimentService | PS MemorySystem 条数 |
| `wander_amp_variance` | ✅ | ❌ | SR mind 多样性代理 |
| `avg_developmental_stage` | ✅ | ✅ | ontogeny 曲线对比 |
| `pct_at_stage_s4` | ✅ | ✅ | 成熟个体比例 |
| `avg_verify_success` | ⚠️ HUD 可选 | ✅ metrics | verify 质量 |
| `unified_bridge_enabled` | ✅ unified 模式 | ❌ | Bridge 试点元数据 |
| `bridged_organism_count` | ✅ | ❌ | 已桥接 SR hub 数 |

### 3.2 建议扩展（读模型 only）

在 **不合并 tick** 前提下，双轨各写采集器，经 `ecology_observation.py` 统一：

| 新 extras 键 | SR 来源 | PS 来源 | 用途 |
|---|---|---|---|
| `avg_developmental_stage` | `sr_debug_hud.developmental_stage` 均值 | `organism.developmental_stage` 均值 | ontogeny 曲线对比 |
| `pct_at_stage_s4` | stage==4 占比 | 同上 | 成熟个体比例 |
| `avg_verify_success_ema` | HUD `verify_success` EMA | 实验 metrics 滑动均值 | verify 质量 |
| `avg_memory_gene_count` | 已有 | 从 `organism.memory_genes` 聚合 | phylogeny 记忆 |
| `avg_social_memory_count` | `sr_social_memories` | `social_memories(organism)` | 社会学习可比 |
| `ladder_enabled` | props.developmental | config / organism 标志 | 实验元数据 |

**PS Runner 同步**：`_collect_metrics` 增加 `avg_developmental_stage`、`avg_memory_gene_count`（与 SR 键名对齐），写入 `metrics.csv` 与 `get_ecology_snapshot`。

### 3.3 不可强对齐项（文档声明）

| 指标 | 原因 |
|---|---|
| `avg_fitness` | PS `SelectionSystem._calculate_fitness` vs SR 无统一 fitness |
| `generation` vs `iteration` | SR 实体 generation vs PS 编排器 iteration — 语义接近但非同一计数器 |
| `sim_time` | SR 场景秒 vs PS 离散 tick |

**研究建议**：可比报告使用 **归一化 tick 轴**（`tick / ticks_total`）+ 上表 extras，而非强行等同 `sim_time`。

---

## 4. Phase C.4 统一 Pond 可行性（Phase D）

### 4.1 问题重述

两套实体（SR `_SceneRuntimeEntity` + 膜脚本 vs PS `Organism` + 组件图）导致：

- 繁殖写入路径不同（spawn vs `InheritanceSystem`）  
- verify / ontogeny 钩子挂载点不同  
- 用户无法在同一世界内回答「这条遗传链在统一法则下是否成立」

### 4.2 三种接缝方案（评审用）

| 方案 | 描述 | 优点 | 风险 |
|---|---|---|---|
| **A · Display-only Bridge** | SR 仍真源；PS Runner 只读 SR 快照做 metrics | 改动最小 | 非真正统一 tick；遗传仍双轨 |
| **B · Organism Adapter** | SR spawn → `WorldBridge.sr_entity_to_organism` 注入 Pond | 单 Pond 真源；PS 编排器可复用 | 膜拓扑 ↔ 组件图 **无损映射未证明** |
| **C · Script-only SR** | 废弃 PS Organism，SR 实体 + PVAECCycle 适配器 | 长期模型唯一 | 破坏现有 PS 实验与 builtin 测试 |

**研究倾向**：短期 **A + EcologySnapshot**（已部分存在）；中期试点 **B** 限 `pvaec-细胞演化` 单工程；**C** 不采纳除非 ADR 修订。

### 4.3 WorldBridge 最小接口（草案）

```python
# core/Lotucosm/runtime/world_bridge.py（试点已落地；膜↔组件映射仍待评审）

def sr_entity_to_organism(entity, pond, profile=None, equip_pvaec=False) -> Organism: ...
def sync_sr_entity_to_organism(entity, organism) -> None: ...
def sync_organism_to_sr_display(organism, entity) -> None: ...
def ensure_bridged_organisms(sr_entities, pond, ...) -> int: ...
def bridge_spawned_organism(entity, pond, spawn_request, ...) -> Organism: ...
def unified_pond_step(pond, sr_entities, delta_time=1.0) -> None: ...
def resolve_runtime_mode(project_config) -> str: ...  # dual | unified_pond
```

**GameViewport**：`_refresh_unified_pond_mode`、`_ensure_unified_bridge_for_scene`、`_run_unified_pond_bridge_tick`、繁殖 `bridge_spawned_organism`（见 ADR-0005 §2）。

**依赖清单**

1. C.1 `EvolutionProfile` + `developmental_profile` ✅  
2. C.2 PS replay overlay ✅ 骨架  
3. C.3 SimulationCoordinator ✅  
4. Ontogeny + verify 语义对齐 ✅  
5. MemoryGene 双轨结构对齐 ✅ Phase B  
6. WorldBridge 桩 + GameViewport 试点 ✅（膜映射待评审）  
7. `avg_social_memory_count` 双轨 metrics ✅

### 4.4 验收阈值（ADR-0005 已采用）

| 检查项 | 阈值 |
|---|---|
| 同 seed unified vs dual，50 tick 后 population | 相对误差 ≤ 15% |
| avg_developmental_stage @ 30% ticks | 相对误差 ≤ 25% |
| 繁殖事件数 / 100 tick | 绝对差 ≤ 1（小种群） |

实现注意：`tools/run_dual_comparability.py` 只比较真实采样点。默认 smoke 配置 `snapshot_interval=10`，因此默认 checkpoint 使用 `20,50`；若手动指定未采样 tick，报告会标记 `checkpoint_sample` 失败，而不会用 final 指标冒充 checkpoint。

---

## 5. 社会学习与 verify 的交叉（Q4 × Q8）

§20 社会学习尚未实现；与 verify 的关系：

| 机制 | verify 角色 | ontogeny 阶段 |
|---|---|---|
| 基因继承 | 子代 S0 起重新 homeo/reaff/exaff | S0 起 |
| 社会观察 | **不替代** verify；仅 `generate_action` 偏置 | 建议 S3+ |
| 文化传递 | 跨代 MemoryGene tag | S4 / phylogeny L4+ |

**原则**：社会信号降低 explore 熵，但 **stage 进阶仍须本体验证计数**——与 ADR-0004「遗传偏置 ≠ 全知」一致。

---

## 6. 建议优先级（研究 → 工程）

| 优先级 | 项 | 产出 |
|---|---|---|
| **P1** | PS verify 三分 + PS exaff 键表 | ✅ `ps_verify.py`；`test_ps_verify_triple.py` |
| **P1** | EcologySnapshot / metrics 发育字段 | ✅ `_collect_metrics` + GameViewport + `ecology_observation` |
| **P2** | `gene_keys` 写入 `sr_mind_profile_fields.md` | ✅ |
| **P2** | SocialMemoryModule 最小实现 | ✅ `social_memory.py` + smoke test |
| **P3** | Phase C.4 ADR + GameViewport 试点 | ✅ `adr/0005` + `world_bridge.py` + tests |
| **P3** | critical period 可逆性（Q7） | ✅ `plasticity_window` / `plasticity_penalty` |

---

## 6.5 战争后进化试点（2026-06-12）

示范工程：`workspace/projects/samples/pvaec-战争后进化`

| 轨 | 灾难叙事 | 指标 |
|---|---|---|
| SR | `sr_war_recovery` 三幕 + 可选 `W` 手动战争 | `war_phase`、`population_at_war_end`、`war_population_min`（EcologySnapshot extras） |
| PS | `disaster_window` in `post_war_recovery.json` | 同上字段写入 metrics / `dual_comparability_matrix` case `post_war_recovery` |

无头对照：`python tools/run_dual_comparability.py --matrix workspace/experiments/dual_comparability_matrix.json`

---

## 7. 开放问题（新增）

| ID | 问题 | 路径 |
|---|---|---|
| Q8 | PS verify 是否与 SR 共用 `pvaec_verify_triple`？ | ✅ 已实现；exaff 用 component sense 键表 |
| Q9 | EcologySnapshot 是否升格为一等字段（非 extras）？ | 待 UI 消费稳定后 ADR |
| Q10 | unified_pond 默认 `dual` 还是 opt-in？ | **opt-in**；与 roadmap 一致 |
| Q11 | PS `memory_genes` vs `memory_system` 哪个进 EcologySnapshot？ | **两者都报**；文档区分 phylogeny vs runtime |

---

## 8. 文档维护

- **版本**：v1.2（2026-06-12）— unified_pond GameViewport 试点、社会记忆 metrics、Bridge 繁殖接缝。  
- **上一阶段**：[pvaec_developmental_research.md](pvaec_developmental_research.md) v1.2、[pvaec_inheritance_alignment.md](pvaec_inheritance_alignment.md) v1.2。  
- **更新时机**：膜↔组件映射评审、unified vs dual 对照实验报告。
