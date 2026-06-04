# 织机引擎教学 · 迷你 Roguelike

工程：[projects/织机教程-迷你Roguelike](../projects/织机教程-迷你Roguelike/)

## 产品边界

| | 织机教程 | PVAEC · 细胞演化 |
|---|----------|------------------|
| 官方包 | `vitalloom.core.platform` + `editor_essentials` + `lotuspond.runtime` + `engine.sr2d` | 另加 `pvaec.simulation` |
| 用途 | 学做游戏（输入、贴图、ScriptBase） | 学 AI 演化 / 膜拓扑 |
| 通关 | HUD 横幅，**模拟继续**（`pause_on_complete: false`） | 演示目标达成可 **自动暂停** |

`vitalloom.pvaec.simulation` 是**官方研究扩展**，不是做普通 2D 游戏的必装项。

## 学习路径

### 课节 1 · 输入与瞄准

- 画布捕获键盘 + 鼠标 → `SceneRuntimeTickContext.input`
- `ctx.input.keys_down`（WASD / 方向键 / Space）
- `ctx.input.mouse_scene_xy`、`mouse_left_clicked` — 鼠标瞄准 + 左键挥砍
- 参考：[player_controller.py](../projects/织机教程-迷你Roguelike/scripts/player_controller.py)

### 课节 2 · 实体视觉

```json
"sr_visual": { "sprite": "player", "anim": "player_walk", "flip_x": false, "alpha": 1.0 }
```

- [assets/manifest.json](../projects/织机教程-迷你Roguelike/assets/manifest.json) 定义 `sprites` / `animations`
- 脚本改 `get_visual().anim` / `flip_x`，或 `self.set_sprite(...)`

### 课节 3 · 战斗反馈

- `ctx.damage_requests` — 宿主扣血，HP 归零后移除
- `ctx.fx_requests` — 飘字 / 挥砍弧（`sr_game_effects.py`）
- 扇形判定：`core/Lotucosm/sr_game_combat.py`

### 课节 4 · 关卡与路引

- `pond_config.proc_seed` / `proc_obstacles` — 开局程序化障碍（同 seed 布局一致）
- [game_director.py](../projects/织机教程-迷你Roguelike/scripts/game_director.py) 挂 `level_01` 实体，`spawn_requests` 刷墙
- `sr_play_goals.hud_victory_key` + `hud_defeat_key`（`player_dead`）

### 课节 4b · 2D 物理（与 PVAEC 共用）

官方 **`sr.physics2d`**（`SrPhysics2DWorld`）同时服务本教程与 PVAEC 主世界，**无需另装插件**：

| 工程 | 自动模式 | 接触 |
|------|----------|------|
| 织机教程（`sr_game_mode: true`） | `GAME` | 边墙 AABB、`proc_wall_*` 柱、玩家/史莱姆互撞 |
| PVAEC 主世界 | `PVAEC` | 细胞圆-圆、营养/场域锚、膜弹簧 |

在 `pond_config.sr_physics2d` 调参（教程常用 `game_contact_iterations`、`max_speed`）：

```json
"sr_physics2d": {
  "restitution": 0.38,
  "game_contact_iterations": 4,
  "game_mover_padding": 6.0,
  "max_speed": 280.0
}
```

详见 [docs/sr_physics2d.md](sr_physics2d.md)。

### 课节 5 · 通关语义

- 清史莱姆 + 抵近出口 → `dungeon_clear=1` → **Victory 横幅，不暂停**
- HP 归零 → `player_dead=1` → **Game Over 并暂停**

## 验收

- 点击画布 → WASD + 鼠标瞄准 → 左键/Space 挥砍（扇形朝鼠标）
- 清怪 + 出口 → Victory 横幅，▶ 仍在跑；HP 归零才停
- `pytest tests/test_engine_tutorial_* tests/test_sr_game_* tests/test_sr_input_state.py -q`

## 明确不做（scope）

五层换关、遗物三选一、后端存档、Tilemap 编辑器 — 见 Rift Delve 策划案「明确不做」；教程保持单层 ScriptBase 教学。
