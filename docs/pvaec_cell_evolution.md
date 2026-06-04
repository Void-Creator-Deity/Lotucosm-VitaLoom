# PVAEC · 细胞演化工程蓝图

本文说明 Lotucosm **感知-验证自主演化循环（PVAEC）** 在 SR 中的落地，以及工程 **PVAEC · 细胞演化**（`projects/pvaec-细胞演化`）的路线与玩法。

> **定位**：莲池生命织机是场景/运行时编辑器；PVAEC 是挂载其上的演化模拟语义。**本项目不是具身智能（Embodied AI）产品或研究方向**——内稳态、内感受等设计仅**借鉴**外部文献思路，不表示归属该领域。

## 1. 借鉴的外部研究（参考用，非本项目归类）

| 方向 | 核心思想 | 在本项目中的用法（借鉴） |
|------|----------|--------------------------|
| [EVAAA](https://github.com/cocoanlab/evaaa) | food/water 等**本质变量**驱动行为 | SR：`energy` / `stress` → `intero_*`；`homeostatic_success` |
| Active Inference | 行动最小化对未来偏好的惊奇 | PVAEC **verify** / **remember** 的分数设计 |
| Allostatic switching | 高负荷→休息；低负荷→觅食 | `stress_norm` 调制脚本增益（可选） |

## 2. PVAEC 六步 ↔ SR 脚本

见 `core/Lotucosm/pvaec_script.py` 与 `projects/pvaec-细胞演化/scripts/*_pvaec.py`。

## 3. 怎么玩

1. 打开 `projects/pvaec-细胞演化`，加载 `main_scene.pond`，**▶ 运行**。
2. 复盘：`logs/sr_sessions/session_*.md`。
3. PS 对照：`python tools/run_ps_experiment.py`。

## 4. 路线图

- Phase A：内感受 + verify/remember（已落地）
- Phase B：`sr_play_goals` 与膜学习边权
- Phase C：PS/SR 统一 Pond 驱动（defer）
- **SR 接触物理**（2026-05）：[`sr_physics2d`](../core/Lotucosm/sr_physics2d/) 官方 2D 引擎 — 见 [sr_physics2d.md](sr_physics2d.md)

## 5. 参考

- [README_PVAEC.md](../README_PVAEC.md)
- [sr_extension_guide.md](sr_extension_guide.md)
