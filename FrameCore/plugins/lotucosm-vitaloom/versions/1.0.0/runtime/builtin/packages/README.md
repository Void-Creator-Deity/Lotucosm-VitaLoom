# 官方扩展包 · 物理路径映射

逻辑包定义在 [`package_index.json`](../package_index.json)。  
当前实现采用**奥卡姆剃刀**：仍从单一 `builtin/` 目录加载，避免破坏 `import builtin.*`。

| 包 id | 状态 | 主要物理路径 | 说明 |
|-------|------|--------------|------|
| `vitalloom.core.platform` | required | `core/Lotucosm/`、`core/VitaLoom/`、`core/api/` | 莲池 + 织机内核 |
| `vitalloom.editor_essentials` | official | `builtin/editor_extensions/*`（UI 子集） | 见 index 中 `plugins` 列表 |
| `vitalloom.lotuspond.runtime` | official | `builtin/components/`、`builtin/entity_types/`、`builtin/systems/` | 莲池细胞与系统 |
| `vitalloom.pvaec.simulation` | official | `builtin/systems/pvaec_orchestrator.py`、`core/Lotucosm/pvaec_*.py` | PVAEC 编排 + 脚本基类 |
| `vitalloom.engine.sr2d` | official | `core/VitaLoom/viewports/game_viewport.py`、`sr_*.py`、`core/Lotucosm/sr_*.py` | 2D SR 播放 |
| `vitalloom.engine.3d` | planned | （无） | 仅占位，见 [package_architecture.md](../../docs/package_architecture.md) |
| `vitalloom.lotuspond.cell` | official | `cell_editor_plugin`、`cell_simulation_plugin` | PS 细胞内编辑 |

完整架构说明：[docs/package_architecture.md](../../docs/package_architecture.md)。
