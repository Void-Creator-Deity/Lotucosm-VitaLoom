# builtin 模组

**L2 官方 builtin**：莲池组件/系统 + 织机编辑器插件（非 L0 莲池地基，非 PVAEC 产品本体）。  
架构分层：[docs/architecture.md](../docs/architecture.md) · PVAEC：[README_PVAEC.md](../README_PVAEC.md) · 织机：[README_VITALOOM.md](../README_VITALOOM.md)。  
逻辑扩展包索引：[docs/package_architecture.md](../docs/package_architecture.md)、[packages/README.md](packages/README.md)。  
SR 膜拓扑在 `core/Lotucosm/`；关卡脚本在 `projects/*/scripts/`；勿与 `builtin/components` 的 Pygame/PS 演示路径混谈。

排错与扩展见 [docs/lotucosm_core_troubleshooting.md](../docs/lotucosm_core_troubleshooting.md)、[docs/sr_extension_guide.md](../docs/sr_extension_guide.md)。

## 子目录

| 目录 | 职责 |
|------|------|
| `components/` | `ComponentBase` 子类：传感器、执行器、膜、工厂与类型目录 |
| `systems/` | 莲池演化、序列化、PVAEC 编排、物理/资源/环境子系统 |
| `entity_types/` | `Organism` 及简单/智能生命体、繁殖与组件获取 |
| `editor_extensions/` | 官方编辑器插件（Dock/视口/插件管理/工作流等） |
| `templates/` | 官方细胞行为模板（PS 随机游动示例） |
| （SR 扩展） | `workspace/projects/samples/pvaec-细胞演化/templates/` + [docs/sr_extension_guide.md](../docs/sr_extension_guide.md) |

## 排错索引

### 组件 (`components/`)

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| 组件 Inspector 无属性 / 拖入失败 | `component_library.get_component_class`、`ComponentFactory.create_component` | 类型名须在 `component_library` 注册 |
| 传感器无输出 | `TouchSensor.sense` / `LightSensor.sense`、`Environment` | PS：`get_nearby_entities` / `get_light_intensity` |
| 膜不吞噬食物 | `Membrane.auto_ingest`、`Environment.get_nearby_food` | 仅 PS 半径吞噬；物体须小于阈值 |
| SR 播放但期望 builtin 膜「直连食物」 | **非 builtin** → `sr_membrane_topology`、`nutrient_gradient_at` | SR 趋食经 chemo 边+脚本；`Membrane`/`TouchSensor` 不做 GPS 导航 |

### 莲池序列化 (`pond serialize`)

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| 反序列化后组件 `organism_id` 仍为 temp | `PondSerializer.deserialize_organism` 回填循环 | 须在 organism 反序列化后写入真实 ID |
| 加载 `.pond` 人口为空或缺字段 | `PondSerializer.deserialize_pond`、`Pond._apply_loaded_pond_state`（core） | 缺 `name/size/max_population` 等会抛错；加载后须 `org.pond = pond` |
| 保存后 JSON 无漂浮物/资源 | `serialize_pond` 的 `floating_components` / `resource_manager` 分支 | 无 `floating_system` 时走 `simple_floating_components` |
| 存档读写失败 | `PondSerializer.save_pond` / `load_pond` | 格式须与 `save_format`（json/pickle）一致 |

### 编辑器插件 (`plugins`)

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| 插件 Dock / 视口壳未出现 | `LegacyEditorPluginAdapter`、插件 `editor_contributions`、`LayoutManager` | 官方插件以 Host-copied `dock_surface` / `viewport_surface` 投影；具体 PyQt widget factory 仅由 Adapter 调用。历史社区 getter/factory 仅是受限兼容回退，且插件须在 `builtin/manifest` 启用 |
| 依赖 `on_editor_ready()` 的插件未完成初始化 | `IRuntimePlugin.on_load()`、`LegacyEditorPluginAdapter.after_plugin_load()` | 新插件直接实现 Qt-free `IRuntimePlugin`；Editor-ready 是贡献投影后的可选、best-effort Adapter 通知，不以 `IEditorPlugin` 类型为前提，也不可承载必需初始化 || 游戏视口不启动 / 仍是占位符 | `game_viewport_plugin.GameViewportPlugin.on_play` | 须真实 `GameViewport` 实例且含 `start_simulation` |
| 生态面板无数据 / 全零 | `ecology_dashboard_plugin`、`GameViewport` SR 快照 API | 仅 SR 播放时有统计 |
| 包/下载失败 | `package_services`、`downloader_plugin.DownloaderService` | 查 `workspace/state/system/download_cache` 与 sha256 |

### PS 演示 vs SR 播放 (`simulation vs SR`)

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| Pygame 演示窗无生物 / 不更新 | `systems/simulation.Simulation.update` | **PS 演示**；与编辑器 SR 播放无关 |
| 工具栏播放无反应 / 非 Pygame 窗 | `game_viewport_plugin` → `GameViewport.start_simulation` | **SR 主路径**；不实例化 `Simulation` |
| PVAEC 世代不替换种群 | `EvolutionRunner`、`PVAECOrchestrator.run_cycle` | PS 莲池 `evolution_generation_interval`；SR 世代在 GameViewport |
| 细胞行为与主世界不一致 | `workspace/projects/samples/pvaec-细胞演化/scripts/`、`sr_membrane_topology` | `templates/official_cell_behavior` 仅为 PS 示例 |

## 相关排错入口

- [Lotucosm 核心排错](../docs/lotucosm_core_troubleshooting.md)
- [主世界 SR 演示](../workspace/projects/samples/pvaec-细胞演化/README.md)
- [VitaLoom 框架](../core/VitaLoom/README.md)
