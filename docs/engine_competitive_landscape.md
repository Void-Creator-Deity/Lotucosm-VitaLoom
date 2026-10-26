# 莲池织机与主流引擎原则对照

本文不是把莲池织机改成 Unity、Unreal 或 Godot，而是把成熟工具链的原则映射到莲池织机自己的架构。

## 现有定位

```text
FrameCore
  最底层启动框架，只发现和委托 lotucosm-vitaloom 大插件。

lotucosm-vitaloom
  莲池织机安装包/大插件，包含 Hub、产品版本表和当前版本 runtime。

versions/<version>/runtime
  具体织机实现：Lotucosm、VitaLoom、Player、builtin capability。

workspace/projects/*
  用户/示范项目世界。项目插件、资源、场景、lock 都属于当前项目。
```

## 原则映射

| 参考对象 | 可借鉴原则 | 莲池织机落点 |
|---|---|---|
| Unity Hub | Hub 管项目与 Editor 版本，项目锁定打开版本 | Hub 只负责创建/导入/打开项目和选择产品版本；Editor 内不跨项目切换 |
| Unity Asset Database | 资源变化、依赖刷新、导出闭包需要可复现 | `asset.scan`、`asset.dependencies`、`asset.validate`、`asset.export_closure` |
| Unity Package lock | 包解析结果必须锁定 | `project.lock.json` 锁定 suite/product/capability |
| Unreal Plugins | Engine 插件、Project 插件、模块描述分层 | FrameCore 安装插件、runtime builtin capability、项目 addons 分层 |
| Godot addons | 项目级扩展应跟随项目 | `workspace/projects/<project>/addons/` 和项目插件状态只影响当前项目 |
| VS Code Extension Manifest | 扩展应声明命令、入口、贡献点 | `package_index.json` 声明 `commands/resources/export_entries/ui_only_reason` |
| MCP Tools | Agent 工具必须可发现、可描述、schema 化 | `VitaLoom Command Registry` 是 UI/CLI/MCP/Agent 的共同 Interface |

## 当前强项

- 项目从物理结构上分清：启动框架、织机大插件、版本 runtime、项目世界。
- 项目插件语义明确：官方能力包、项目 addon、workspace extension source 都归当前项目管理。
- AI 原生路线清楚：AI 不模拟 UI，但必须用同一命令 Interface 得到同一项目结果。
- PVAEC/SR/PS 是差异化语义，不是照搬通用引擎。

## 当前短板

- 资源数据库仍轻量，没有 GUID、增量导入、热重载和大型项目索引。
- 渲染、动画、native/GPU 性能证据不足。
- 部分 UI 入口仍未完全命令化，尤其是 Inspector 字段修改和 SceneViewport 右键/拖拽创建。
- benchmark 刚建立，缺历史 baseline 和阈值趋势。

## 下一步顺序

1. 先让项目创作操作全部同构：UI 与 AI 都走命令层。
2. 再让资源闭包成为 Hub、导出和 AI 的共同事实来源。
3. 然后基于 benchmark 找热点，按 ADR-0006 做 native Adapter，而不是整体重写。

