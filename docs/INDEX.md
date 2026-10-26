# Documentation Index

当前文档只保留活跃架构、工程契约、用户指南、研究说明、最终重构状态和历史材料分类入口。

## 项目状态

| 文档 | 用途 |
|---|---|
| [Release Notes 2026-10-26](release_notes_2026-10-26.md) | 最近一次源码同步、修复范围、验证和已知边界 |
| [Refactor Completion Record](refactor_completion_record.md) | 引擎化重构最终摘要、验证和边界 |
| [Refactor Progress](refactor_progress.md) | 固定 100 分交付面 |
| [Refactor Iteration Log](refactor_iteration_log.md) | 唯一总迭代记录和根目录审计结论 |
| [Mainline Status](mainline_status.md) | 完整长周期迭代日志 |
| [Repository Layout](repository_layout.md) | 根目录、文档、测试和生成物规则 |

历史资料目录：

- [Historical Prompts](prompts/)
- [Historical Plans and Specs](superpowers/)
- [Historical Archive](archive/)

## 架构与契约

| 文档 | 用途 |
|---|---|
| [Suite Architecture](suite_architecture.md) | 套件整体分层 |
| [Architecture Overview](architecture.md) | 当前架构总览 |
| [Runtime Entry Points](runtime_entry_points.md) | 入口和宿主调用路径 |
| [Package Architecture](package_architecture.md) | 包结构与能力包边界 |
| [Project Manifest](project_manifest.md) | Project World manifest |
| [Compatibility and Versions](compatibility_and_versions.md) | 兼容性和版本语义 |
| [Root Asset Provenance Policy](asset_provenance_policy.md) | 资产来源与信任边界 |
| [Plugin Command Contract](plugin_command_contract.md) | 插件命令契约 |
| [AI Native Command Layer](ai_native_command_layer.md) | AI/CLI/MCP/UI 命令层 |

### ADR

- [ADR 0001 - Dual Runtime Unification Seam](adr/0001-dual-runtime-unification-seam.md)
- [ADR 0002 - First Principles and Layering](adr/0002-first-principles-and-layering.md)
- [ADR 0003 - Suite Plugin Architecture](adr/0003-suite-plugin-architecture.md)
- [ADR 0004 - PVAEC Developmental Ladder](adr/0004-pvaec-developmental-ladder.md)
- [ADR 0005 - Unified Pond Bridge](adr/0005-unified-pond-bridge.md)
- [ADR 0006 - Native Acceleration Seams](adr/0006-native-acceleration-seams.md)
- [ADR 0007 - Unified Semantic Command History](adr/0007-unified-semantic-command-history.md)

## 用户与开发者指南

| 文档 | 用途 |
|---|---|
| [Quick Start](guides/README_QUICK_START.md) | 快速启动 |
| [VitaLoom Guide](guides/README_VITALOOM.md) | 产品与 runtime 入门 |
| [PVAEC Guide](guides/README_PVAEC.md) | PVAEC 使用说明 |
| [User Guide](guides/USER_GUIDE.md) | 用户操作 |
| [Plugin Development Guide](guides/PLUGIN_DEVELOPMENT_GUIDE.md) | 插件开发 |
| [Legacy Plugin Compatibility](guides/LEGACY_PLUGIN_INTERFACE_COMPATIBILITY.md) | 旧接口兼容 |
| [SR Extension Guide](sr_extension_guide.md) | SR 扩展 |
| [SR Physics 2D](sr_physics2d.md) | SR2D 物理 |
| [SR Link Physics](sr_link_physics.md) | 连接物理 |
| [Experiment Guide](experiment_guide.md) | 实验运行 |
| [Engine Roguelike Tutorial](engine_tutorial_roguelike.md) | 教程 |
| [Core Troubleshooting](lotucosm_core_troubleshooting.md) | 故障排查 |

## 研究、比较与领域说明

| 文档 | 用途 |
|---|---|
| [PVAEC Cell Evolution](pvaec_cell_evolution.md) | 细胞演化 |
| [PVAEC War Recovery](pvaec_war_recovery.md) | 战后恢复 |
| [PVAEC Developmental Research](pvaec_developmental_research.md) | 发育研究 |
| [PVAEC Comparability Research](pvaec_comparability_research.md) | 可比性研究 |
| [PVAEC Inheritance Alignment](pvaec_inheritance_alignment.md) | 继承路线对齐 |
| [SR Mind Profile Fields](sr_mind_profile_fields.md) | Mind profile 字段 |
| [Engine Gap Against Mihoyo](engine_gap_against_mihoyo.md) | 能力差距分析 |
| [Engine Competitive Landscape](engine_competitive_landscape.md) | 竞品背景 |
| [Runtime Unification Roadmap](runtime_unification_roadmap.md) | 历史路线参考 |

## 维护规则

- 当前权威文档放在 `docs/` 的明确分类中。
- 阶段 prompt/plan 不再进入活跃文档树。
- 完整重构历史保留在 `mainline_status.md`、`prompts/`、`superpowers/` 和 `archive/`。
- 测试中间载荷不进入 Git；只在归档 manifest 中追溯。
