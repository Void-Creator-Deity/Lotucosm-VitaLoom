# 织机教程 · 迷你 Roguelike

这是莲池织机的 2D SR 游戏教程工程，不是 PVAEC 研究工程。它只需要 `sr2d` 与 `game_script` 能力，不应要求 `vitalloom.pvaec.simulation`。

## 打开

1. 运行 `python main.py`。
2. 在 Hub 打开 `workspace/projects/samples/织机教程-迷你Roguelike`。
3. 加载 `scenes/dungeon_01.pond`。
4. 点击画布获取输入焦点，然后按 ▶ 运行。

## 操作

- WASD / 方向键移动。
- 鼠标瞄准。
- 左键或 Space 攻击。
- 贴近敌人时也会自动尝试近战攻击。

## 目标

胜利：

1. 清空 `enemy_*`。
2. 靠近 `exit_gate`。
3. `game_director.py` 设置 `dungeon_clear=1`。
4. `sr_play_goals.hud_victory_key` 触发 Victory。
5. 本局暂停结算。

失败：

1. 敌人贴近玩家造成伤害。
2. HP 归零。
3. `player_controller.py` 设置 `player_dead=1`。
4. `sr_play_goals.hud_defeat_key` 触发 Game Over。
5. 本局暂停结算。

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

`pause_on_complete: true` 是本工程的设计：Roguelike 是关卡教程，需要明确通关结束。PVAEC 细胞演化工程相反，应连续演化。

## 脚本

| 文件 | 类名 | 挂载实体 |
|---|---|---|
| `player_controller.py` | `PlayerController` | `player_rl` |
| `enemy_chaser.py` | `EnemyChaser` | `enemy_*` |
| `game_director.py` | `GameDirector` | `level_01` |

更多说明见 [docs/engine_tutorial_roguelike.md](../../../docs/engine_tutorial_roguelike.md)。
