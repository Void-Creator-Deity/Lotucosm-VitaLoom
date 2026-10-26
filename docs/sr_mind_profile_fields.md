# SR `MindProfile` 字段说明

中枢脚本 [`CentralBrainPvaec`](../workspace/projects/samples/pvaec-细胞演化/scripts/central_brain_pvaec.py) 使用 [`MindProfile`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_mind_profile.py)；场景 JSON 中通过 `scripts[].properties.mind` 扁平覆盖字段。缺省与历史硬编码一致，见 `MindProfile.default_main_world()`。

下列说明对应 [`sr_central_brain_channels.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_central_brain_channels.py) 中的用法。

| 字段 | 作用 |
|------|------|
| `actuator_damping` | 应激 raw 中削弱 `actuator_pull` |
| `stress_tanh_scale` | `tanh(stress_raw * scale)` 得到归一化应激 |
| `stress_norm_threshold` | 高于则用 `gain_high_stress`，否则 `gain_low_stress` |
| `gain_high_stress` / `gain_low_stress` | 指向场心加速度增益（高/低应激） |
| `max_speed` | `act` 中速度钳制 |
| `mem_alpha` | EMA 记忆更新系数（stress/field/speed） |
| `wave_field_div` / `wave_tanh_scale` | 环境场幅值 → `wave_risk` 的尺度 |
| `wave_risk_coeff` | 应激 raw 中 `wave_risk` 权重 |
| `org_pull_coeff` | 应激 raw 中同伴 organism 拉力惩罚 |
| `niche_stress_coeff` | 应激 raw 中 `niche_pressure` |
| `load_deriv_penalty` | 应激 raw 中 `world_load_derivative`（正项惩罚） |
| `field_flee_div` | 场强归一化除数；记忆 `field_ema` 与逃离权重 |
| `field_flee_gain` | 沿梯度逃离基础增益 |
| `mem_flee_boost` | 用 `stress_ema` 放大逃离 |
| `niche_flee_boost` | 用 `niche_pressure` 放大逃离 |
| `wander_amp` | 切向漫游强度（乘 `speed_ema`） |
| `intrinsic_speed_div` | 速度 EMA 归一化除数 |
| `emission_arousal` / `emission_memory` / `emission_floor` | `act` 中 `emission_strength` 组合 |

Phase 3/4：同一扁平 dict 可序列化进存档或与 PS 组件字段对齐；基因组件可映射上述字段子集。

## 可演化基因键（`gene_keys` / `sr_mind_gene`）

SR 繁殖与 `EvolutionProfile` 通过 [`sr_mind_gene.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_mind_gene.py) 对 **mind dict 子集** 做高斯突变。默认键与边界如下（可被 `project.json` → `evolution_defaults.gene_keys` 覆盖）：

| 键 | 默认 bounds | 中枢用途 |
|---|---|---|
| `wander_amp` | 4.0 – 88.0 | 切向漫游（`motion_acceleration`） |
| `gain_high_stress` | 6.0 – 128.0 | 高应激指向场心增益 |
| `mem_alpha` | 0.04 – 0.88 | stress/field/speed EMA |

**扩展键**（需在 `gene_keys` 中显式列出；bounds 见 `bounds_for_gene_key`）：

| 键 | bounds（内置） | 说明 |
|---|---|---|
| `gain_low_stress` | 2.0 – 80.0 | 低应激增益 |
| `max_speed` | 40.0 – 600.0 | 速度钳制 |
| `field_flee_gain` | 4.0 – 60.0 | 场逃离 |
| `niche_stress_coeff` | 0.01 – 0.5 | 生态位应激权重 |

**工程配置示例**（`project.json`）：

```json
"evolution_defaults": {
  "mutation_sigma": 0.38,
  "gene_keys": ["wander_amp", "gain_high_stress", "mem_alpha", "field_flee_gain"]
}
```

**数据流**：`EvolutionProfile.gene_keys` → `evo_central_brain_pvaec` spawn → `mind_dict_mutate(..., gene_keys=profile.gene_keys)`。未列入 `gene_keys` 的 MindProfile 字段仍可通过场景 `properties.mind` 静态覆盖，但**不参与代际突变**。

**PS 对应**：开放 dict `evolvable_traits`；对齐见 [pvaec_inheritance_alignment.md](pvaec_inheritance_alignment.md) §7。

## SR 膜通道与连接权重（运行时）

| 概念 | 说明 |
|------|------|
| `sr_channel_out` | 膜实体每 tick 输出的通道字典（如 `chemo`、`chemo_dir_x`） |
| `inbound_signals` | `SceneRuntimeTickContext` 入站聚合信号（目标为 actuator 等） |
| `connections[].weight` | 拓扑边突触强度，繁殖时可 `mutate_signal_edges` |
| `chemo_gain_scale` | 中枢在 `act` 写入 organism，调制膜受体化学通道增益 |

详见 [`sr_membrane_topology.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_membrane_topology.py) 与 [`game_viewport.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py) 膜同步逻辑。

## 排错交叉引用

| 现象 | 先查 |
|------|------|
| 运动总往画布中心 | `motion_acceleration` 中心牵引 + `gain_high/low_stress`（与 chemo 叠加，见 P2） |
| 趋化无效 | 膜通道与 `nutrient_gradient_at`，非 MindProfile 营养 GPS |
| 应激异常 | `stress_raw_and_norm` 与 `ambient_field` / `niche_pressure` |
| 全库索引 | [lotucosm_core_troubleshooting.md](lotucosm_core_troubleshooting.md) · [PVAEC 细胞演化 SR](../workspace/projects/samples/pvaec-细胞演化/README.md) · [VitaLoom](guides/README_VITALOOM.md) · [builtin](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/README.md) |
