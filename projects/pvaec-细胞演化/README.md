# PVAEC · 细胞演化（官方示范工程 v1.0.0）

本目录是 **PVAEC 演化模拟** 的官方示范工程，运行在 [莲池生命织机](../../README_VITALOOM.md) 上：单细胞隐喻、膜趋化、能量代谢与带突变的繁殖。

- **PVAEC 说明**：[README_PVAEC.md](../../README_PVAEC.md)
- **工程蓝图**：[docs/pvaec_cell_evolution.md](../../docs/pvaec_cell_evolution.md)
- **扩展脚本**：[docs/sr_extension_guide.md](../../docs/sr_extension_guide.md) · 模板见 `templates/`

## 场景

| 文件 | 说明 |
|------|------|
| `scenes/main_scene.pond` | 入门：存活 100s、种群峰值 ≥4 |
| `scenes/challenge_scene.pond` | 挑战：更高代谢、更少营养 |

`project.json` → `active_scene` 决定默认加载场景（v1 默认 **main_scene.pond**）。

## 演示目标与暂停行为

场景内 `sr_play_goals` 在 HUD 显示进度（存活时长、种群峰值）。**v1 默认 `pause_on_complete: false`**：达标后闪横幅一次，模拟**继续运行**（沙盒观看演化）。

若需要「通关即停」，在 `.pond` 中设 `"pause_on_complete": true`。灭绝暂停由 `sr_pause_on_extinction` 控制（v1 默认 `false`）。

## 脚本（SR）

核心：`evo_central_brain_pvaec`、`sensor_patrol_pvaec`、`actuator_pulse_pvaec`。  
契约测试：`tests/test_pvaec_cell_evolution_scripts_smoke.py`。

## 快速玩

1. `python main.py`（仓库根）
2. **文件 → 打开项目** → 选本目录 → 加载场景 → 工具栏 **▶ 运行**
