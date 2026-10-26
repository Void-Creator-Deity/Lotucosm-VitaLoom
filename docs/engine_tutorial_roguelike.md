# 织机教程 · 迷你 Roguelike

工程：`workspace/projects/samples/织机教程-迷你Roguelike`

## 定位

这是莲池织机的 **SR 2D 游戏教程工程**。它展示：

- `ScriptBase.sr_step(ctx, dt)` 游戏脚本；
- 键盘/鼠标输入；
- sprite manifest 与动画；
- 2D 接触物理；
- 关卡胜负 HUD 键。

它不是 PVAEC 工程，不要求 `vitalloom.pvaec.simulation`。

## 与 PVAEC 工程的边界

| 项目 | 能力包 | 运行语义 | 结束语义 |
|---|---|---|---|
| 织机教程 · 迷你 Roguelike | `core.platform` + `editor_essentials` + `lotuspond.runtime` + `engine.sr2d` | 游戏输入、战斗、出口 | 清场并到出口后通关暂停；HP 归零失败暂停 |
| PVAEC · 细胞演化 | 另加 `pvaec.simulation` | 连续演化、内稳态、膜/趋化 | 演示目标只提示，不自动打断演化 |

## 玩法闭环

1. 点击游戏画布获取输入焦点。
2. WASD / 方向键移动。
3. 鼠标瞄准，左键或 Space 攻击。
4. 清空 `enemy_*`。
5. 抵近 `exit_gate`。
6. `game_director.py` 设置 `sr_debug_hud["dungeon_clear"] = 1`。
7. `sr_play_goals.hud_victory_key = "dungeon_clear"` 触发 Victory，并暂停本局。

失败条件：

1. 敌人贴近玩家造成持续伤害。
2. `player_controller.py` 将 HP 降到 0。
3. 设置 `sr_debug_hud["player_dead"] = 1`。
4. `sr_play_goals.hud_defeat_key = "player_dead"` 触发 Game Over，并暂停本局。

## 关键场景字段

```json
{
  "sr_game_mode": true,
  "sr_play_goals": {
    "player_id": "player_rl",
    "hud_victory_key": "dungeon_clear",
    "hud_defeat_key": "player_dead",
    "pause_on_complete": true
  },
  "sr_pause_on_extinction": false
}
```

`pause_on_complete: true` 在这个工程里是有意的：教程游戏需要明确的通关结算，不应该只闪横幅继续空跑。

## 验收

```powershell
python -B -m pytest -q -p no:cacheprovider tests\test_engine_tutorial_roguelike_scene.py tests\test_sr_game_defaults.py tests\test_sr_game_scene.py tests\test_game_viewport_play_goals.py tests\test_sr_play_goals_hud_victory.py
```
