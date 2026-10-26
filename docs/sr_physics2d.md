# SR 2D 物理引擎（`vitalloom.engine.sr2d` · `sr.physics2d`）

官方 **2D 场景物理** 入口：`core/Lotucosm/sr_physics2d/`。  
与 PS 莲池 `builtin/systems/physics_engine.py`（细胞内演示）**不是同一套**。

## 通用：两个工程共用同一插件

| 工程 | 自动模式 | 接触类型 |
|------|----------|----------|
| **`workspace/projects/samples/pvaec-细胞演化`** | `Physics2DMode.PVAEC` | organism 互撞、营养/场域锚圆盘、膜弹簧 |
| **`workspace/projects/samples/织机教程-迷你Roguelike`** | `Physics2DMode.GAME` | 边墙 AABB、程序化柱圆盘、game_actor 互斥 |

二者都通过 **`GameViewportPlugin`** 加载同一 `GameViewport`；加载 `.pond` 时读 `sr_physics2d` 配置并创建 **`SrPhysics2DWorld`**。  
`sr_game_mode: true` → 游戏轨；否则 → PVAEC 轨。**无需装两个物理插件。**

最小包栈（两工程相同）：`core` + `editor_essentials` + `lotuspond.runtime` + **`engine.sr2d`**。

## 能力一览

| 能力 | 模块 | 说明 |
|------|------|------|
| **积分** | `integrator.py` | 阻尼、限速、位置更新、边界反弹 |
| **PVAEC 接触** | `pvaec_contacts.py` | organism 圆-圆 + 冲量 |
| **游戏接触** | `game_contacts.py` | 边墙条 + `proc_wall_*` 圆柱 + 玩家/史莱姆互撞 |
| **软连接** | `sr_link_physics.py` | 膜 Kelvin-Voigt 弹簧（仅 PVAEC） |
| **单步编排** | `world.py` | `SrPhysics2DWorld.step` / `step_for_viewport` |

## API

```python
from core.Lotucosm.sr_physics2d import SrPhysics2DConfig, SrPhysics2DWorld, Physics2DMode

world = SrPhysics2DWorld(SrPhysics2DConfig.from_scene_data(scene_data))
world.step(entities, dt, width, height, mode=Physics2DMode.PVAEC, springs=spring_links)
world.step(entities, dt, width, height, mode=Physics2DMode.GAME)

# GameViewport 内部：
world.step_for_viewport(host, entities, dt, width, height)
```

## Adapter Boundary

`SrPhysics2DWorld.step()` remains the public runtime entry point. Internally it delegates to `SrPhysics2DAdapter`.

- `PythonSrPhysics2DAdapter` is the reference implementation and default fallback.
- Future Rust/C++ adapters must pass `tests/test_sr_physics2d_world.py` and `tests/test_sr_physics2d_adapter_contract.py` before being enabled.
- `.pond` files, `GameViewport`, and AI command flows must not call a native module directly.
- Benchmark evidence lives in `tools/benchmark_engine.py --case sr2d`.

## 场景配置（可选，两工程通用）

根级或 `pond_config` 内：

```json
"sr_physics2d": {
  "linear_damping": 0.98,
  "boundary_bounce": 0.85,
  "restitution": 0.34,
  "friction": 0.18,
  "contact_iterations": 4,
  "game_contact_iterations": 3,
  "game_mover_padding": 8.0,
  "max_speed": 420.0
}
```

- **PVAEC** 常用：`restitution`、`contact_iterations`  
- **教程** 常用：`game_contact_iterations`、`game_mover_padding`、`max_speed`（玩家 165 移速量级）

## 运行时顺序

1. 脚本批 +（PVAEC）执行器耦合  
2. **胞外交换**（`sr_fluid_coupling`：uptake/secretion；**漂移默认关**，趋化仍走 sensor→chemo→actuator）  
3. **`SrPhysics2DWorld.step`**：弹簧（PVAEC）→ 积分 → 接触  
4. **内外流体视觉**（`sr_fluid_flow` 粒子 + 膜形变；可选 `sr_field_grid` 扩散）  
5. 能量 / HUD / 会话结局  

### `pond_config.sr_fluid_coupling`（PVAEC）

```json
"sr_fluid_coupling": {
  "enabled": false,
  "drift_gain": 0.14,
  "max_drift_accel": 38.0,
  "uptake_rate": 1.2,
  "secretion_gain": 0.35,
  "chemo_suppress": 0.82
}
```

主世界演示默认 **`enabled: false`**：细胞靠膜趋化游向营养，避免场梯度与执行器耦合「抢方向盘」。需要实验性场牵引时再显式打开。

### `pond_config.sr_field_grid`（可选扩散场）

```json
"sr_field_grid": {
  "enabled": false,
  "cell_size": 48.0,
  "diffusion": 0.22,
  "decay": 0.04
}
```

## 内外流体（PVAEC 视觉 + 运动层）

`core/Lotucosm/sr_fluid_flow.py` — **仅 PVAEC 轨**（织机教程 `game_mode` 不启用）：

| 驱动源 | 效果 |
|--------|------|
| 营养势 + 环境场梯度 | 胞外水流、膜外压 |
| 游动尾流 / 纤毛 emission | 邻近胞外扰动 |
| 核→执行器 chemo | 胞内能量流 |
| 受体 chemo | 跨膜入流 |
| 细胞 velocity | 前进侧膜隆起 |

有流场时质膜 sin 装饰降为约 22%，形变主要由内外压差决定。

## 参考

- [sr_link_physics.md](sr_link_physics.md) — 连接与弹簧  
- [LearnOpenGL · Collision resolution](https://learnopengl.com/In-Practice/2D-Game/Collisions/Collision-resolution)
