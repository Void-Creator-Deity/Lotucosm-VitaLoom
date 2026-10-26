# 莲池织机引擎能力差距审查

> 目的：用米哈游等游戏引擎岗位能力标尺校准项目短板，不把莲池织机伪装成商业级 C++ 引擎。现有架构仍以 [suite_architecture.md](suite_architecture.md) 为准：FrameCore 是启动框架，`lotucosm-vitaloom` 是莲池织机大插件，AI 命令层属于产品 runtime。

## 参考来源

用户提供的米哈游招聘页是动态页，抓取正文不稳定，因此本文只把它作为岗位入口；能力归纳结合公开游戏引擎岗位共性和主流引擎官方资料：

- Unity [Asset Database refresh](https://docs.unity3d.com/Manual/AssetDatabaseRefreshing.html)
- Unity [Package lock files](https://docs.unity3d.com/Manual/upm-conflicts-auto.html)
- Unreal [Plugins](https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine)
- Godot [Editor plugins](https://docs.godotengine.org/en/stable/tutorials/plugins/editor/index.html)
- VS Code [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest)
- MCP [Tools](https://modelcontextprotocol.io/docs/concepts/tools)

这些资料只取原则，不照抄目录结构。

## 岗位标尺

| 方向 | 商业引擎常见要求 | 莲池织机当前状态 |
|---|---|---|
| 引擎模块 | 渲染、动画、物理、资源管线、工具链、扩展机制 | 有 SR 2D、PVAEC/PS、插件工具链；渲染/动画/资源管线深度仍不足 |
| 性能工程 | CPU、内存、IO、GPU、启动时间、稳定性、平台适配 | 有 Windows smoke 与轻量 benchmark；缺长期趋势、GPU、移动端和多线程证据 |
| 复杂系统 | 至少在一个引擎子系统上有深度证据 | PVAEC/SR/PS 语义较深；资源、渲染、动画仍浅 |
| Native 能力 | C++/Rust/C、OS、数学、图形学、调试 | 当前主体是 Python；已用 ADR-0006 记录 native seam，但没有 native Adapter |
| AI/自动化 | AIGC、Agent、工具自动化、可审计工作流 | AI 原生命令层是差异化方向，CLI/MCP 与 UI 同构正在补齐 |

## 已有证据

- 物理架构：`FrameCore/` + `FrameCore/plugins/lotucosm-vitaloom/` + 产品版本 runtime + `workspace/projects/`。
- 项目契约：`project.json`、`project.lock.json`、项目级插件状态、workspace extension source。
- 运行语义：SR/PS 双入口、PVAEC、场景 `.pond`、实体/脚本契约。
- AI 同构命令：`project.*`、`scene.*`、`entity.*`、`transform.set`、`script.set_property`、`prefab.place`、`asset.*`、`plugin.*`、`export.player.prepare`。
- 资源证据：`asset.dependencies`、`asset.validate`、`asset.export_closure` 输出依赖、缺失资源、文件 hash、启用插件闭包。
- 性能证据：`tools/benchmark_engine.py` 输出 JSON，覆盖 command list/dispatch、resource scan、export closure、PS tick、Hub smoke、Editor smoke。

## 正在补强

| 优先级 | 项 | 完成标准 |
|---|---|---|
| P1 | Inspector 同构 | 字段修改走 `entity.set_property`、`transform.set`、`script.set_property`，进入统一审计/undo |
| P1 | SceneViewport 创建/放置同构 | 右键创建、拖拽 asset、放置 prefab 走 `entity.create`、`asset.apply_to_scene`、`prefab.place` |
| P1 | MCP server 包装 | `list_commands`、`describe_command`、`run_command`、`get_project_state`、`get_scene_snapshot` 不新增业务逻辑 |
| P2 | 资源闭包深化 | Player export、Hub 风险摘要、AI 命令复用同一 `asset.export_closure` |
| P2 | benchmark 趋势 | 可选 baseline 和阈值检查，CI 只报警不阻断 |
| P2 | 插件贡献契约 | package catalog 声明 `commands/resources/export_entries/ui_only_reason`，门禁检查 |
| P3 | native seam 原型 | 对 SR 物理、渲染批处理、PS batch 建第二个 Adapter |

## 明显缺口

- 渲染深水区：材质、批处理、GPU 管线、后处理、可视化调试还不具备商业引擎证据。
- 动画系统：状态机、时间轴、骨骼/关键帧/混合树仍缺。
- 移动端与跨平台：Android/iOS/主机平台没有系统构建和性能数据。
- 多线程与 GPU：没有稳定调度、Profiler、GPU benchmark 和 native memory 证据。
- 资源数据库：第一阶段只有相对路径 + hash + 闭包，没有 GUID 数据库、增量导入和热重载深度。
- 长期稳定性：缺崩溃率、启动趋势、运行时压力测试和大型项目样本。

## 为什么 AI 同构不是限制 AI

AI 不适合模拟拖拽，但必须产生和人类 UI 一样的项目结果。命令层给 AI 的是语义工具，而不是限制：

```text
人类：在 Inspector 改 Transform
AI：run transform.set
结果：同一份 .pond、同一套事件、同一条审计记录

人类：在插件管理器启用 PVAEC
AI：run plugin.enable
结果：同一份 project.json / package_state / project.lock.json
```

这样避免“人用组件和场景，AI 绕过组件写运行时代码”的割裂。

## 当前验收命令

```bash
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B tools/check_asset_provenance.py
python -B tools/check_project_plugin_model.py
python -B -m pytest -q -p no:cacheprovider
python -B tools/benchmark_engine.py --case all --repeats 1
```

