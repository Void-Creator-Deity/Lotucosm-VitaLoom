# Lotucosm · 莲池运行时（织机引擎 · 运行时一半）

本目录是 **莲池生命织机** 的**宇宙/莲池/实体/组件/系统**实现，**不是** PVAEC 产品本身的全部。

- 织机编辑器壳层：[`core/VitaLoom/README.md`](../VitaLoom/README.md)
- PVAEC AI 模拟语义：[`README_PVAEC.md`](../../README_PVAEC.md)
- 仓库总索引：[`README.md`](../../README.md)

## 职责边界

| 在本目录 | 不在本目录（或仅契约） |
|----------|------------------------|
| `cosmos`、`pond`、`entity`、`component`、`system` | PyQt 窗口、Dock、菜单 |
| `.pond` 场景运行时：`scene_runtime_context` | 主世界关卡文案 |
| SR 膜拓扑：`sr_membrane_topology`、`sr_link_physics` | PVAEC 具体巡逻/繁殖脚本（在 `projects/*/scripts`） |
| `pvaec_script.py` 基类 | `pvaec_orchestrator` 在 `builtin/systems/` |

## 常用入口

| 文件 | 用途 |
|------|------|
| `cosmos.py` | 宇宙单例、创建莲池 |
| `pond.py` | 莲池世界 |
| `pvaec_script.py` | SR 脚本 perceive/think/act 契约 |
| `scene_runtime_context.py` | GameViewport 每帧 tick 上下文 |
| `sr_membrane_topology.py` | chemo 边聚合、膜附着 |

排错：[docs/lotucosm_core_troubleshooting.md](../../docs/lotucosm_core_troubleshooting.md)
