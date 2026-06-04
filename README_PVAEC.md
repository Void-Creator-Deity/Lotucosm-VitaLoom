# PVAEC · 感知-验证自主演化循环（AI 数字生命模拟）

> **这不是编辑器本身。** PVAEC 是跑在 [莲池生命织机](README_VITALOOM.md) 上的 **AI 模拟与演化语义**；织机提供莲池、场景、播放与插件，PVAEC 提供「智能如何从生命经验中编织出来」的循环。

> **与具身智能的关系**：内稳态、内感受等机制**仅借鉴** EVAAA、Active Inference 等文献中的思路，用于 PVAEC 的 verify/remember 设计。**本项目不是具身智能产品，也不归属该研究方向。**

仓库总索引：[README.md](README.md)

---

## 项目是什么

**PVAEC**（Perception–Verification Autonomous Evolution Cycle）定义数字生命的学习法则：不靠静态数据集编程，而在生命周期内通过经验闭环涌现行为。

```text
感知 → 记忆 → 尝试 → 验证（利用新感知） → 再记忆 → …
```

与「莲池生命织机」的分工：

| 问题 | 谁回答 |
|------|--------|
| 宇宙、莲池、实体、`.pond` 怎么存？ | **织机引擎**（Lotucosm + VitaLoom） |
| 一帧里 perceive / think / act 怎么编排？ | **PVAEC**（本项目的算法与脚本契约） |
| 主世界细胞怎么游、怎么繁殖？ | **工程脚本**（如 `projects/pvaec-细胞演化/scripts/*_pvaec.py`） |

---

## 代码在哪里（勿与织机 UI 混淆）

| 模块 | 路径 | 职责 |
|------|------|------|
| 脚本契约 | `core/Lotucosm/pvaec_script.py` | `PvaecScript`：perceive → think → act |
| 帧循环 / 记忆 | `core/Lotucosm/pvaec_cycle.py`、`memory.py`、`perception.py` | PS 路径循环与记忆 |
| SR 心智 | `core/Lotucosm/sr_mind_profile.py`、`sr_central_brain_pvaec.py` | 场景运行时中枢字段 |
| 编排系统 | `builtin/systems/pvaec_orchestrator.py` | 莲池内 PVAEC 世代驱动 |
| 官方扩展包 | `vitalloom.pvaec.simulation`（见 [package_index.json](builtin/package_index.json)） | 包管理器中的 **PVAEC 模拟包** |
| **具体行为** | `projects/<工程>/scripts/*_pvaec.py` | 用户/示范关卡逻辑（可拷贝 [templates](projects/pvaec-细胞演化/templates/)） |

**不要**把 `builtin/components/sensors.py` 里的 PS `output_signal` 演示当成 SR 的 PVAEC 路径；SR 趋化走 `sr_channel_out` + 拓扑边，见 [docs/sr_extension_guide.md](docs/sr_extension_guide.md)。

---

## 无头实验（不打开织机）

在项目根：

```bash
python tools/run_ps_experiment.py
```

说明：[docs/experiment_guide.md](docs/experiment_guide.md)（配置 JSON、`metrics.csv`、世代编排）。

---

## 在织机里体验 PVAEC（主世界 SR）

1. 按 [README_VITALOOM.md](README_VITALOOM.md) 启动 `python main.py`
2. 打开工程 `projects/pvaec-细胞演化/`，加载 `scenes/main_scene.pond`
3. 工具栏 **▶ 运行** —— 画布上的细胞即 **PVAEC 脚本 + SR 引擎** 联合结果

玩法与场景字段：[projects/pvaec-细胞演化/README.md](projects/pvaec-细胞演化/README.md)  
扩展脚本：[docs/sr_extension_guide.md](docs/sr_extension_guide.md)

---

## 当前能力（PVAEC 侧）

- ✅ perceive / think / act 契约（`PvaecScript`）
- ✅ PS 无头实验与世代编排
- ✅ SR PVAEC 脚本批（sensor → actuator → organism 顺序，见 `scene_runtime_context.py`）
- ✅ 中枢 `mind` / `evo` 参数经 `.pond` 配置
- ✅ 膜 chemo 通道与信号边（引擎拓扑，行为在脚本）
- ✅ SR **圆体接触**：`sr.physics2d`（`SrPhysics2DWorld`）— 见 [docs/sr_physics2d.md](docs/sr_physics2d.md)

---

## 哲学（本项目的「为什么」）

我们摒弃「从静态数据学智能」的范式，转而模拟生命在自身时间线里**验证行动是否改善内稳态**。PVAEC 是这一范式的可执行定义；织机是承载它的世界与工具。

---

## 相关文档

- 引擎与包：[README_VITALOOM.md](README_VITALOOM.md)、[docs/package_architecture.md](docs/package_architecture.md)
- 细胞演化工程蓝图：[docs/pvaec_cell_evolution.md](docs/pvaec_cell_evolution.md)
- 排错：[docs/lotucosm_core_troubleshooting.md](docs/lotucosm_core_troubleshooting.md)
