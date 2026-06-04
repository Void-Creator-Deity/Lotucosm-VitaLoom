# Lotucosm · VitaLoom · PVAEC（单仓，两个项目）

本仓库同时承载**两个产品**，请勿混读为同一个 README：

| 项目 | 是什么 | 主 README |
|------|--------|-----------|
| **PVAEC** | 感知-验证自主演化循环 · **AI 数字生命模拟**（算法、世代、无头实验） | **[README_PVAEC.md](README_PVAEC.md)** |
| **莲池生命织机**（VitaLoom + Lotucosm） | **引擎与编辑器**：莲池运行时 + 织机 IDE，供 PVAEC 与其它 `.pond` 工程挂载 | **[README_VITALOOM.md](README_VITALOOM.md)** |

关系（第一性表述）：

```text
莲池生命织机（引擎）  →  提供宇宙/莲池、.pond、播放 tick、插件化编辑器
        ↑ 运行在之上
PVAEC（AI 模拟）      →  提供 perceive→think→act 闭环与演化实验语义
        ↑ 具体关卡与脚本
projects/*（用户工程） →  如 `pvaec-细胞演化`（PVAEC 示范）与 `织机教程-迷你Roguelike`（引擎教学）
```

---

## 30 秒：我该读哪份、跑哪条命令？

| 你想… | 读 | 跑 |
|--------|-----|-----|
| 理解 PVAEC 循环、做无头演化实验 | [README_PVAEC.md](README_PVAEC.md) | `python tools/run_ps_experiment.py` |
| 打开织机、编辑场景、▶ 玩示范工程 | [README_VITALOOM.md](README_VITALOOM.md) · [START_HERE.md](START_HERE.md) | `python main.py` |
| 扩展独特细胞脚本 / 场景边权 | [docs/sr_extension_guide.md](docs/sr_extension_guide.md) | 改 `projects/pvaec-细胞演化/` 后停止再运行 |
| 包结构（核心包 vs PVAEC 扩展包） | [docs/package_architecture.md](docs/package_architecture.md) | — |

---

## 仓库目录（谁归哪个项目）

| 路径 | 归属 |
|------|------|
| `core/Lotucosm/` | **织机·莲池运行时**（引擎） |
| `core/VitaLoom/` | **织机·编辑器**（引擎） |
| `core/Lotucosm/pvaec_*.py`、`builtin/systems/pvaec_orchestrator.py` | **PVAEC 模拟**（跑在引擎上的官方扩展） |
| `builtin/components`、`builtin/entity_types` | 引擎·莲池官方组件 |
| `builtin/editor_extensions/` | 引擎·织机官方插件 |
| `projects/pvaec-细胞演化/scripts/*_pvaec.py` | **PVAEC 内容**（某一工程里的行为实现） |
| `projects/织机教程-迷你Roguelike/` | **引擎教学**（ScriptBase Roguelike，见 [docs/engine_tutorial_roguelike.md](docs/engine_tutorial_roguelike.md)） |
| `plugins/` | 织机·社区编辑器扩展（可选） |

---

## 其它文档

- 文档地图：[docs/INDEX.md](docs/INDEX.md)
- **相对 GitHub 旧版的完整变更说明**：[CHANGELOG.md](CHANGELOG.md)
- 深度使用指南：[USER_GUIDE.md](USER_GUIDE.md)
- 插件开发：[PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md)

## 技术栈与许可

Python 3.12+ · PyQt6 · JSON · MIT License — 详见 [LICENSE](LICENSE) 与各子 README。
