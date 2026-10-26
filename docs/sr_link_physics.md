# SR 连接物理：硬骨架 · 软信号 · 独立扩散

## 动机

原先 `connections` 与 `sr_signal_connections` 在运行时效果上偏「数据管线」：膜蛋白 rigid 跟随 hub，趋化边单独一张表，视觉上容易像预设 sin 循环。  
借鉴粗粒化细胞模型里常见的 **skeleton–membrane decoupling**（如 MEDYAN 膜–骨架、Kelvin-Voigt 粘弹性键），把连接语义拆成三层：

| 类型 | 力学 | 信号 | 典型用途 |
|------|------|------|----------|
| **hard** | 刚性附着（骨架） | 不单独传 chemo | organism ↔ sensor/actuator |
| **soft** | 可选弹簧（KV 阻尼） | 仅传 channel/weight | sensor → actuator；或软锚定膜蛋白 |
| **independent** | 无拓扑边 | 场扩散 / 不传 | 孤立受体、靠 `nutrient_gradient` |

## `.pond` 字段

```json
{
  "start": "ai_organism_01",
  "end": "sensor_mem_01",
  "link_kind": "hard"
}
```

```json
{
  "start": "sensor_mem_01",
  "end": "actuator_cilium_01",
  "link_kind": "soft",
  "channel": "chemo",
  "weight": 1.15
}
```

软锚定（膜蛋白可相对 hub 弹动）：

```json
{
  "start": "ai_organism_01",
  "end": "sensor_mem_01",
  "link_kind": "soft",
  "stiffness": 85,
  "damping": 11,
  "rest_length": 60
}
```

| 字段 | 说明 |
|------|------|
| `link_kind` | `hard` / `soft` / `independent`；缺省时 organism↔膜组件→hard，sensor↔actuator→soft |
| `channel`, `weight` | 软连接上的信号（chemo 等） |
| `stiffness`, `damping`, `rest_length` | 软弹簧；默认 k=85, c=11，rest=初始距离 |
| `mechanical: false` | soft 边只做信号、不建弹簧 |
| `transmission` | `wired`（默认）或 `diffusion`（独立节点靠场） |

## 运行时顺序

1. `_sync_membrane_positions` — 仅 **hard** 子实体 rigid 跟随 hub  
2. PVAEC 脚本批（sensor / actuator / organism）  
3. `_apply_actuator_coupling`  
4. **`SrPhysics2DWorld.step`** — 弹簧 → 积分 → 圆体/墙接触（见 [sr_physics2d.md](sr_physics2d.md)）

## 渲染

- **hard**：胞内淡色刚性辐条（骨架）  
- **soft 弹簧**：绿色锯齿弹簧曲线；有弹簧时质膜 sin wobble 减弱，形状更多由锚点物理位置决定  
- **soft 信号**：仍走胞内趋化弧 + 光点（读当帧 chemo）  

## 向后兼容

- 未写 `link_kind` 的旧场景：推断规则与上表一致，行为与改前相同  
- 主世界 `main_scene.pond`：结构边显式 `hard`，`sr_signal_connections` 显式 `soft`  

## 模块

- [`core/Lotucosm/sr_link_physics.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_link_physics.py) — 分类、弹簧、步进
- [`core/Lotucosm/sr_membrane_topology.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_membrane_topology.py) — `build_membrane_attachments` 仅消费 hard
- [`core/VitaLoom/viewports/game_viewport.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py) — tick 接入
- [`core/VitaLoom/viewports/sr_visual_renderer.py`](../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_visual_renderer.py) — 骨架/弹簧绘制

## 参考概念（非逐行复现）

- Kelvin-Voigt viscoelastic bonds：弹簧 + 阻尼，适合膜波动与骨架耦合的时间尺度  
- Reaction–diffusion + membrane clustering：软连接传信息、硬连接定几何  
- 独立节点：无显式边时沿用 SR 营养场 / `nutrient_gradient_at` 扩散输入  
