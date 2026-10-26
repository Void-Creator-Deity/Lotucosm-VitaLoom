# ADR-0004：PVAEC 个体发育阶梯（Developmental Ladder）

> 物理架构：runtime 路径见 [ADR-0003](0003-suite-plugin-architecture.md)（`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/`）。

- **状态**：已接受
- **日期**：2026-06-12
- **决策者**：PVAEC 语义 / 架构维护者
- **依据**：[pvaec_developmental_research.md](../pvaec_developmental_research.md) §9、§21

## 背景

项目愿景要求生命体按 **ontogeny** 顺序认识世界（① 自我 → ② 交互验证 → ③ 生态位 → ④ 世界规律），而非出生即 `CentralBrainPvaec.perceive()` 全知。

研究文档 v1.1 已给出 S0–S4 解锁表与 API 草案；本 ADR 将其固化为 **runtime 契约**，与 phylogeny（`InheritanceSystem` / SR 繁殖）分离。

## 决策

### 1. 两条轴不可混写

| 轴 | 含义 | 实现位置 |
|---|---|---|
| **Ontogeny** | 个体出生后感知/行为/记忆逐步解锁 | SR：`PvaecScript.developmental_*`、`sr_developmental_ladder.py`；PS：`ps_developmental.py` + `PVAECCycle.run_cycle` |
| **Phylogeny** | 代际组件、基因、MemoryGene 传递 | PS：`InheritanceSystem`；SR：`evo_central_brain_pvaec` spawn（见 [pvaec_inheritance_alignment.md](../pvaec_inheritance_alignment.md)） |

**不变量**：子代 phylogeny 继承偏置（mind gene、膜边权、MemoryGene）后，**ontogeny 仍从 S0 起步**——遗传的是倾向，不是全知地图。

### 2. 发育阶段 S0–S4

| Stage | 名称 | 解锁感知（CentralBrain 键） | 最低 stage tick | 进阶条件（满足且 tick 达标） |
|---|---|---|---|---|
| S0 | Neonate | `simulation_time`, `bounds`, `world_*`, `memory_*` | 0 | 出生默认 |
| S1 | Proprio | + `intrinsic_speed` | 30 | ≥3 次 explore act（\|Δv\|>ε） |
| S2 | Interactive | + `sensor_pull`, `actuator_pull`, `ambient_*` | 100 | ≥5 次 verify success ≥ 0.55 |
| S3 | Ecological | + `nearest_*`, `peer_organism_pull`, `niche_pressure` | 300 | ≥1 次 remember 写入 |
| S4 | World | + `world_load`, `world_load_derivative` | 500 | 首次繁殖 **或** `len(peers)` 中 organism ≥ 2 |

被 mask 的键在 `filter_observation` 中置为中性值（0 / None），避免 `think` KeyError。

### 3. Runtime API（`PvaecScript`）

```python
developmental_ladder_enabled: bool = False   # 基类默认关，兼容旧脚本
developmental_stage: int = 0                 # 0..4

def perception_mask(self) -> frozenset[str]
def filter_observation(self, observation) -> dict
def apply_developmental_profile(self, profile: Mapping | None) -> None
def on_stage_advance(self, new_stage: int) -> None
```

- **`pvaec_step`**：在 `perceive` 之后、`think` 之前调用 `filter_observation`；在 `remember` 之后调用 `_maybe_advance_developmental_stage`。
- **实现模块**：`core/Lotucosm/sr_developmental_ladder.py`（阶段键表与进阶阈值常量）。

### 4. 示范工程默认

| 脚本 | `developmental_ladder_enabled` | 说明 |
|---|---|---|
| `PvaecScript` 子类（通用） | `False` | 不破坏膜 patrol 等脚本 |
| `CentralBrainPvaec` | `True` | PVAEC 细胞演化中枢 demo |
| `EvoCentralBrainPvaec` 子代 spawn | `initial_stage: 0` | 强制 ontogeny 重启 |

可通过 `scripts[].properties.developmental` 关闭或设 `initial_stage`：

```json
"developmental": {
  "enabled": true,
  "initial_stage": 0
}
```

### 5. 工程配置（`project.json`）

新增可选字段 `developmental_profile`（工程级默认，场景 props 可覆盖）：

```json
"developmental_profile": {
  "enabled": true,
  "initial_stage": 0
}
```

与 `evolution_defaults` 并列：`evolution_defaults` 管 PS phylogeny；`developmental_profile` 管 **SR/PS ontogeny** 默认（PS 经 `PsExperimentConfig.developmental_*` 与 `Organism.developmental_*` 生效）。

### 6. PS 轨（最小移植，2026-06）

| 模块 | 职责 |
|---|---|
| `ps_developmental.py` | 感知 enrich/filter、retrieve/generate 门控、stage 进阶、子代 S0 重置 |
| `PVAECCycle.run_cycle` | 六步循环内挂载 developmental 钩子 |
| `Organism` | `developmental_ladder_enabled` / `developmental_stage`（默认关） |
| `InheritanceSystem.inherit` | 子代 `reset_ps_developmental_for_child`（继承 ladder 开关，stage 归零） |
| `PsExperimentRunner` | 按 `PsExperimentConfig` 初始化种群 ladder |

PS 感知形态为 `{component_id: sense_result}` + `intero_*` / `_pvaec_tick`；S0 仅 intero，S1 +meta，S2 单组件，S3 全组件，S4 全感知。进阶阈值复用 `sr_developmental_ladder.can_advance_stage`。

### 7. 明确不在本 ADR 范围

- Reafference 拆分 verify（Q1）→ 后续 ADR 或 runtime 小版本
- `NavigationBody` / `SocialMemoryModule` → P1/P2 实现
- SR 与 PS 遗传字段统一 → [pvaec_inheritance_alignment.md](../pvaec_inheritance_alignment.md) + ADR-0001 Phase C

## 后果

### 正面

- 「认识顺序」可在 SR demo 中观测（HUD / `developmental_stage`）。
- 研究 §21 与代码一一对应，可写测试 `test_developmental_ladder.py`。
- phylogeny 与 ontogeny 语义分离，符合仓库「继承算法 + 个体验证」叙事。

### 负面

- `CentralBrainPvaec` 早期 stage 应激/运动变弱（设计如此）；挑战场景需更长 warm-up。
- 直接调用 `perceive()` 的测试须显式 `developmental_ladder_enabled = False` 或设高 stage。

## 备选方案（已否决）

| 方案 | 否决原因 |
|---|---|
| 仅在示范脚本 if/else 门控 | 无法复用、与 core 契约脱节 |
| 默认全员开启 ladder | 破坏未迁移脚本与 patrol 单元测试 |
| 子代继承父代 stage | 违背「子代须从 S0 重新验证」 |

## 参考

- [pvaec_developmental_research.md](../pvaec_developmental_research.md)
- [pvaec_inheritance_alignment.md](../pvaec_inheritance_alignment.md)
- [0001-dual-runtime-unification-seam.md](0001-dual-runtime-unification-seam.md)
- [guides/README_PVAEC.md](../guides/README_PVAEC.md)
