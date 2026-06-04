# 莲池实验指南（PS / PVAEC 双循环）

本文说明如何把项目里的 **感知-验证自主演化循环（PVAEC）** 与 **世代编排循环** 跑成可复现实验，并产出可分析数据。设计参考了内稳态/本质变量驱动的自主智能体研究（如 [EVAAA](https://github.com/cocoanlab/evaaa)）：用 **energy / health** 作为内在验证信号，而非外部手工奖励函数。

## 两条循环分别是什么

| 循环 | 代码入口 | 触发条件 | 作用 |
|------|----------|----------|------|
| **帧循环 · PVAEC 六步** | `PVAECCycle.run_cycle` ← `Organism.update` | `enable_pvaec_cycle_per_tick=true` 且已挂载 `MemorySystem` | 感知→记忆→行动→执行→验证→再记忆（单体内学习） |
| **世代循环 · 编排器** | `PVAECOrchestrator.run_cycle` ← `EvolutionRunner` | `Pond.time % evolution_generation_interval == 0` | 感知→变异→行动→适应度→选择/繁殖（替换整代种群） |

二者可单独或同时开启，便于做对照实验（见 `data/experiments/quick_evolution_only.json`）。

## 一键运行（推荐）

在项目根目录：

```bash
python tools/run_ps_experiment.py
```

默认读取 `data/experiments/pvaec_homeostasis_loop.json`，在 `data/experiment_runs/<名称>_<时间>/` 生成：

- `summary.json` — 配置、最终指标、全程快照
- `metrics.csv` — 按 `snapshot_interval` 采样的时间序列（可导入 Excel / pandas）

常用参数：

```bash
python tools/run_ps_experiment.py data/experiments/quick_evolution_only.json
python tools/run_ps_experiment.py --ticks 500 --seed 123 --name my_run
python tools/run_ps_experiment.py --no-export
```

## 配置文件字段

| 字段 | 含义 |
|------|------|
| `ticks` | 模拟帧数（每帧一次 `Pond.update`） |
| `evolution_generation_interval` | 多少帧触发一次世代替换；≤0 或关闭编排器则不演化 |
| `enable_pvaec_cycle_per_tick` | 是否在每帧跑单体内 PVAEC |
| `equip_sensor_actuator` | 是否装配 Sensor + Actuator（PS 运动闭环） |
| `equip_pvaec_engine` | 是否额外挂载 PVAECEngine 组件 |
| `selection_pressure` / `elitism_rate` / `mutation_rate` | 世代编排参数 |
| `seed` | 随机种子，便于复现 |

复制 JSON 改参数即可做参数扫描；无需改代码。

## 指标如何解读（产出价值）

`metrics.csv` 列含义：

- **population** — 存活个体数；世代后可能因选择波动
- **avg_energy / avg_health** — 内稳态水平（越高通常表示环境摄取与代谢越稳）
- **avg_fitness / max_fitness** — 选择系统综合适应度（能量、成功动作、后代、年龄惩罚）
- **avg_memory_count** — 单体内 PVAEC 写入的运行时记忆条数（学习是否在发生）
- **iteration** — 已完成的世代数

**可做的实验类型：**

1. 只开 PVAEC、关世代 → 观察 `avg_memory_count` 随 tick 上升
2. 只开世代、关 PVAEC → 对比 `max_fitness` 代际变化
3. 调 `mutation_rate` / `selection_pressure` → 种群多样性 vs 收敛速度
4. 固定 `seed` 重复跑 → 验证改动是否可复现

## 与编辑器 / SR 的关系

- **PS 实验**（本文）：`Pond` + `Organism`，无 GUI，适合批量与论文式指标。
- **SR 主世界**：`GameViewport` + `PvaecScript`，适合场景叙事与可视化；验收见 `tests/test_pvaec_cell_evolution_scripts_smoke.py`。

不要在 SR 脚本路径里期待 PS 的 `memory_genes` 世代遗传；代际记忆走 `InheritanceSystem` + 莲池编排器。

## 维护与回归

```bash
python -m pytest tests/test_ps_experiment_runner.py -q
python tools/run_routine_maintenance.py
```

## 延伸阅读

- [README_PVAEC.md](../README_PVAEC.md) — PVAEC 循环与 PS/SR 分工
- [sr_extension_guide.md](sr_extension_guide.md) — 扩展 SR 脚本
