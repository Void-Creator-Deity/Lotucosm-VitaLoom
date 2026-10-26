# PVAEC · 感知-验证自主演化循环（AI 数字生命模拟）

> **这不是编辑器本身，也不是运行时地基。** PVAEC 是跑在 Lotucosm 莲池运行时之上的 **AI 模拟与演化语义**；[VitaLoom 织机](README_VITALOOM.md) 提供编辑与播放入口。分层见 [docs/architecture.md](../architecture.md)。

> **与具身智能的关系**：内稳态、内感受等机制**仅借鉴** EVAAA、Active Inference 等文献中的思路，用于 PVAEC 的 verify/remember 设计。**本项目不是具身智能产品，也不归属该研究方向。**

仓库总索引：[README.md](../../README.md)

---

## 项目是什么

**PVAEC**（Perception–Verification Autonomous Evolution Cycle）定义数字生命的学习法则：不靠静态数据集编程，而在生命周期内通过经验闭环涌现行为。

```text
感知 → 记忆 → 尝试 → 验证（利用新感知） → 再记忆 → …
```

与「莲池生命织机」的分工：

| 问题 | 谁回答 |
|------|--------|
| 宇宙、莲池、实体、`.pond` 怎么存、怎么 tick？ | **Lotucosm 莲池**（产品版本 `runtime/core/Lotucosm/`） |
| 怎么编辑场景、▶ 播放？ | **VitaLoom 织机**（产品版本 `runtime/core/VitaLoom/`） |
| 一帧里 perceive / think / act 怎么编排？ | **PVAEC**（算法与 `PvaecScript` 契约） |
| 主世界细胞怎么游、怎么繁殖？ | **工程脚本**（如 `workspace/projects/samples/pvaec-细胞演化/scripts/*_pvaec.py`） |

---

## 代码在哪里（勿与织机 UI 混淆）

| 模块 | 路径 | 职责 |
|------|------|------|
| 脚本契约 | `runtime/core/Lotucosm/pvaec_script.py` | `PvaecScript`：perceive → think → act |
| 帧循环 / 记忆 | `runtime/core/Lotucosm/pvaec_cycle.py`、`memory.py`、`perception.py` | PS 路径循环与记忆 |
| SR 心智 | `runtime/core/Lotucosm/sr_mind_profile.py`；中枢类见 `workspace/projects/samples/pvaec-细胞演化/scripts/central_brain_pvaec.py` | 场景运行时中枢字段 |
| 编排系统 | `runtime/builtin/systems/pvaec_orchestrator.py` | 莲池内 PVAEC 世代驱动 |
| 官方扩展包 | `vitalloom.pvaec.simulation`（见 [package_index.json](../../FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json)） | 插件管理器中的 **PVAEC 模拟包** |
| **具体行为** | `workspace/projects/<分组>/<工程>/scripts/*_pvaec.py` | 用户/示范关卡逻辑（可拷贝 [templates](../../workspace/projects/samples/pvaec-细胞演化/templates/)） |

**不要**把产品 runtime 内 `builtin/components/sensors.py` 的 PS `output_signal` 演示当成 SR 的 PVAEC 路径；SR 趋化走 `sr_channel_out` + 拓扑边，见 [docs/sr_extension_guide.md](../sr_extension_guide.md)。

---

## 莲池演化实验（推荐 · 织机内）

1. `python main.py` 启动织机
2. **视图 → 面板 → 莲池演化实验**（或 `Ctrl+Shift+P`）
3. 选择 `workspace/experiments/` 预设，调整 ticks / mutation_rate 等 → **运行实验**
4. 结果写入 `workspace/state/experiment_runs/`；**莲池生态** Dock 可查看 PS 进度摘要

打开 `workspace/projects/samples/pvaec-细胞演化` 时，工程 `project.json` 的 `ps_experiment_preset` 会自动加载默认预设。

## 终端 / CI（备选）

自动化与 CI 仍可使用：

```bash
python tools/run_ps_experiment.py
```

说明：[docs/experiment_guide.md](../experiment_guide.md)（配置 JSON、`metrics.csv`、世代编排）。

---

## 在织机里体验 PVAEC（主世界 SR）

1. 按 [README_VITALOOM.md](README_VITALOOM.md) 启动 `python main.py`
2. 打开工程 `workspace/projects/samples/pvaec-细胞演化/`，加载 `scenes/main_scene.pond`
3. 工具栏 **▶ 运行** —— 画布上的细胞即 **PVAEC 脚本 + SR 引擎** 联合结果

玩法与场景字段：[workspace/projects/samples/pvaec-细胞演化/README.md](../../workspace/projects/samples/pvaec-细胞演化/README.md)
扩展脚本：[docs/sr_extension_guide.md](../sr_extension_guide.md)

---

## 当前能力（PVAEC 侧）

- ✅ perceive / think / act 契约（`PvaecScript`）
- ✅ 织机内 PS 演化实验 Dock（`PsExperimentPlugin`）
- ✅ PS 世代编排（终端/CI 薄封装仍可用）
- ✅ SR PVAEC 脚本批（sensor → actuator → organism 顺序，见 `scene_runtime_context.py`）
- ✅ 中枢 `mind` / `evo` 参数经 `.pond` 配置
- ✅ 膜 chemo 通道与信号边（引擎拓扑，行为在脚本）
- ✅ SR **圆体接触**：`sr.physics2d`（`SrPhysics2DWorld`）— 见 [docs/sr_physics2d.md](../sr_physics2d.md)

---

## 哲学（本项目的「为什么」）

我们摒弃「从静态数据学智能」的范式，转而模拟生命在自身时间线里**验证行动是否改善内稳态**。PVAEC 是这一范式的可执行定义；织机是承载它的世界与工具。

---

## 相关文档

- 引擎与包：[README_VITALOOM.md](README_VITALOOM.md)、[docs/package_architecture.md](../package_architecture.md)
- 细胞演化工程蓝图：[docs/pvaec_cell_evolution.md](../pvaec_cell_evolution.md)
- **生命阶段与认知发育专项研究**：[docs/pvaec_developmental_research.md](../pvaec_developmental_research.md)
- **个体发育阶梯 ADR**：[docs/adr/0004-pvaec-developmental-ladder.md](../adr/0004-pvaec-developmental-ladder.md)
- **双轨可比性（verify / 生态指标）**：[docs/pvaec_comparability_research.md](../pvaec_comparability_research.md)
- **SR/PS 遗传字段对齐**：[docs/pvaec_inheritance_alignment.md](../pvaec_inheritance_alignment.md)
- 排错：[docs/lotucosm_core_troubleshooting.md](../lotucosm_core_troubleshooting.md)
