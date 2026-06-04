# 织机教程 · 迷你 Roguelike

**莲池生命织机**（引擎）教学工程。**不是** PVAEC 研究包；推荐 **不装** `vitalloom.pvaec.simulation`。

| 对比 | 本工程 | [PVAEC · 细胞演化](../pvaec-细胞演化/) |
|------|--------|--------------------------------------|
| 产品 | 莲池织机 · 2D 游戏 SR | PVAEC AI 模拟研究 |
| 脚本 | `ScriptBase.sr_step(ctx)` | `PvaecScript` 六步 |
| 实体 | `game_actor` / `game_prop` + `sr_game_mode` | `organism` / 膜 / chemo |
| 生命 | HUD 的 `hp` / `player_dead` | `energy` / 种群灭绝 |
| 包 | `lotuspond` + `engine.sr2d` | 另加 `pvaec.simulation` |

**物理**：与 PVAEC 细胞演化示范共用官方 **`sr.physics2d`**（`SrPhysics2DWorld`，本工程自动 `GAME` 模式）。见 [docs/sr_physics2d.md](../../docs/sr_physics2d.md)。

## 操作

1. `python main.py` → 打开本工程 → `scenes/dungeon_01.pond` → **▶**
2. **点击游戏画布**获得焦点
3. **WASD** 移动 · **鼠标** 瞄准 · **左键 / Space** 挥砍（贴近史莱姆也会自动攻击）
4. 清史莱姆 + 靠 **出口** → Victory 横幅（**模拟继续**）；HP 归零 → Game Over 暂停

## 架构说明

- **`player_rl`**：`PlayerController` — 移动、瞄准、战斗
- **`level_01`**：`GameDirector` — 程序化障碍（`proc_seed`）、胜负 HUD
- 边墙在 `.pond` 固定摆放；中部障碍由 `GameDirector` 首帧 `spawn_requests` 生成

## 课节

1. `.pond` + `sr_visual` + `pond_config.player_id`
2. `player_controller.py` — `ctx.input`、`damage_requests`、`fx_requests`
3. `assets/manifest.json` — 贴图与 walk 动画
4. `game_director.py` — `spawn_requests`、通关条件
5. `sr_play_goals` — 胜利/失败键，游戏模式不 `pause_on_complete`

## 脚本

| 文件 | 类名 | 挂载实体 |
|------|------|----------|
| `player_controller.py` | `PlayerController` | `player_rl` |
| `enemy_chaser.py` | `EnemyChaser` | `enemy_*` |
| `game_director.py` | `GameDirector` | `level_01` |

更多：[docs/engine_tutorial_roguelike.md](../../docs/engine_tutorial_roguelike.md)
