# PVAEC · 细胞演化工程蓝图

工程：`workspace/projects/samples/pvaec-细胞演化`

## 定位

PVAEC 是挂在莲池织机运行时之上的 **感知-验证-行动-记忆-演化语义**。
莲池织机负责场景、播放、插件和工具；PVAEC 工程负责具体细胞脚本、膜拓扑、趋化、繁殖与演化演示。

它不是普通 2D 游戏工程，也不是 FrameCore 底层框架。

## 当前设计意图

PVAEC SR 工程应当表现为 **连续演化演示**：

- 达成 `sr_play_goals` 后只显示 Victory/目标达成提示，不自动暂停；
- 种群灭绝后只显示/记录状态，不强制自动暂停；
- 会话日志仍在手动停止、显式停止或测试 smoke 结束时保存；
- 真正的批处理实验由 PS 路径负责，见 `tools/run_ps_experiment.py` 与 `workspace/experiments/*.json`。

这和 Roguelike 教程不同：Roguelike 是游戏关卡，通关/失败应该暂停结算。

## 场景规则

`main_scene.pond`：

- 入门演示；
- `survive_seconds = 100`；
- `peak_population = 4`；
- `pause_on_complete = false`；
- `sr_pause_on_extinction = false`。

`challenge_scene.pond`：

- 更高代谢、更少营养；
- `survive_seconds >= 150`；
- `peak_population >= 6`；
- `pause_on_complete = false`；
- `sr_pause_on_extinction = false`。

## PVAEC 六步与 SR 脚本

示范脚本位于：

```text
workspace/projects/samples/pvaec-细胞演化/scripts/
```

核心分工：

- `evo_central_brain_pvaec.py`：中枢、趋化、能量、繁殖；
- `sensor_patrol_pvaec.py`：膜受体/化学感受；
- `actuator_pulse_pvaec.py`：纤毛/执行器；
- `well_pulse_pvaec.py`：场域锚；
- `ambient_marker_drift.py`：环境标记漂移；
- `satellite_roamer_pvaec.py`：附属游动体。

## 能力包

PVAEC 工程需要：

```text
vitalloom.core.platform
vitalloom.editor_essentials
vitalloom.lotuspond.runtime
vitalloom.pvaec.simulation
vitalloom.engine.sr2d
```

这些由工程 `project.json` 和 `project.lock.json` 锁定。教程工程不应要求 `vitalloom.pvaec.simulation`。

## 验收

```powershell
python -B -m pytest -q -p no:cacheprovider tests\test_pvaec_cell_evolution_scenes.py tests\test_pvaec_cell_evolution_scripts_smoke.py tests\test_central_brain_pvaec.py tests\test_evo_survival_balance.py
```

关键不变量：

- PVAEC 场景 `pause_on_complete` 必须为 `false`；
- PVAEC 场景 `sr_pause_on_extinction` 必须为 `false`；
- Roguelike 的 `pause_on_complete` 可以为 `true`，因为它是关卡结算，不是演化演示。
