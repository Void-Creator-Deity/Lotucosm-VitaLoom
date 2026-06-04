# SR `MindProfile` 字段说明

中枢脚本 [`CentralBrainPvaec`](../projects/pvaec-细胞演化/scripts/central_brain_pvaec.py) 使用 [`MindProfile`](../core/Lotucosm/sr_mind_profile.py)；场景 JSON 中通过 `scripts[].properties.mind` 扁平覆盖字段。缺省与历史硬编码一致，见 `MindProfile.default_main_world()`。

下列说明对应 [`sr_central_brain_channels.py`](../core/Lotucosm/sr_central_brain_channels.py) 中的用法。

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

## SR 膜通道与连接权重（运行时）

| 概念 | 说明 |
|------|------|
| `sr_channel_out` | 膜实体每 tick 输出的通道字典（如 `chemo`、`chemo_dir_x`） |
| `inbound_signals` | `SceneRuntimeTickContext` 入站聚合信号（目标为 actuator 等） |
| `connections[].weight` | 拓扑边突触强度，繁殖时可 `mutate_signal_edges` |
| `chemo_gain_scale` | 中枢在 `act` 写入 organism，调制膜受体化学通道增益 |

详见 [`sr_membrane_topology.py`](../core/Lotucosm/sr_membrane_topology.py) 与 [`game_viewport.py`](../core/VitaLoom/viewports/game_viewport.py) 膜同步逻辑。

## 排错交叉引用

| 现象 | 先查 |
|------|------|
| 运动总往画布中心 | `motion_acceleration` 中心牵引 + `gain_high/low_stress`（与 chemo 叠加，见 P2） |
| 趋化无效 | 膜通道与 `nutrient_gradient_at`，非 MindProfile 营养 GPS |
| 应激异常 | `stress_raw_and_norm` 与 `ambient_field` / `niche_pressure` |
| 全库索引 | [lotucosm_core_troubleshooting.md](lotucosm_core_troubleshooting.md) · [PVAEC 细胞演化 SR](../projects/pvaec-细胞演化/README.md) · [VitaLoom](../core/VitaLoom/README.md) · [builtin](../builtin/README.md) |
