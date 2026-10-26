# Phase E5 完成后的接手提示（2026-07-18）

## 用户确认的不可变架构

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and downstream plugin-host framework
      -> versions/<version>/runtime (versioned runtime boundary, not another numbered layer)
          -> L2 vitalloom.* capability/domain packages
          -> L3 engine extension plugins/adapters
          -> L4 project addons scoped to one Project World
```

- FrameCore 只发现 L1 引擎大插件；不得直接加载 `vitalloom.*`。
- `lotucosm-vitaloom` 本身继续作为下层 plugin Host。
- Project World 是 L4 addon 作用域，不是并列根框架。
- PyQt6/QPainter/OpenGL 是当前或遗留 UI-host Adapter，不是根架构、领域 authority 或生命周期规则。
- 不破坏 `.pond`、AI command registry、Inspector binding、SR2D、package/project manifests。

## E5 已完成且稳定

新增 Qt-free 深层 Module：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/
  core/VitaLoom/project/plugin_host_lifecycle.py
```

其 Interface 现在负责：

- downstream extension catalog normalization；
- scope priority 与同级 source collision diagnostics；
- dependency closure、missing dependency 与 cycle fail-closed；
- dependency-first activation；
- reverse-dependency deactivation；
- protected plugin retention；
- JSON-safe deterministic lifecycle plan/report；
- L4 `<project>/addons/<addon>/plugin.json` authority discovery；
- project/addon/manifest/entry containment、traversal、symlink 与 runtime version validation。

L4 addon manifest schema：

```json
{
  "schema_version": 1,
  "id": "ExamplePlugin",
  "version": "1.0.0",
  "entry": "example_plugin.py",
  "runtime": {
    "plugin_id": "lotucosm-vitaloom",
    "version": ">=1.0.0,<2.0.0"
  },
  "dependencies": ["OtherPlugin"]
}
```

`PluginLoader` 已收敛为具体 Editor/PyQt Host Adapter：

- 通过 Qt-free plan 激活/停用，不再用字典顺序或循环依赖 fallback 执行项目生命周期；
- 新 Project World 的 manifest 和入口 metadata 全部验证成功后，才清理旧 embedded catalog；
- discovery/metadata 失败保留旧 catalog 和 active state；
- callback failure 产生 partial/failed report；独立插件仍 failure-isolated，依赖失败插件的后继会跳过；
- `last_project_addon_discovery_report` 与 `last_lifecycle_report` 保存可检查证据。

`ProjectManager` 已明确事件语义：

- `project_opened` 仍只表示项目/场景上下文已选择；
- settled lifecycle 才发布 `project_plugins_synced`，payload 携带 report；
- blocked/failed lifecycle 发布 `project_plugin_lifecycle_failed`；
- project close 会清理 L4 embedded catalog 并回到无项目激活目标。

文档层级已统一：`CONTEXT.md`、`docs/architecture.md`、`docs/suite_architecture.md`、ADR-0003、插件命令契约与插件开发指南不再把 Product Version Runtime 错列为 L2，也不再把 capability、extension 和 Project World 混为同层。

## 验证证据

聚合回归：**55 passed, 3 skipped in 3.17s**。

三个真实环境 skip：

1. 缺少真实 PyQt6 Adapter 环境；
2. package interlock directory-symlink 测试在当前 Windows 会话无创建权限；
3. L4 addon directory-symlink 测试在当前 Windows 会话无创建权限。

没有 fake/stub Qt 或伪造 symlink 行为。

Guardrails：

```text
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
syntax AST OK
```

## 仍未完成/不得误报

- 没有 operator-facing lifecycle inspect/list/recovery command；
- 没有第三方 callback side-effect 的通用事务回滚；
- watcher/hot reload 尚未迁移到同一 lifecycle authority；
- workspace extension 安装/解析仍属于 package/project command 主线，不应被冷启动自动启用；
- 当前环境无法做真实 PyQt project-open interaction smoke；
- 不得声称 PyQt 已移除、OpenGL default-ready、native acceleration 完成或整个项目“彻底完成”。

## 唯一下一 Gate

**Phase E6 — Downstream Extension Operator Inspection and Failed-Lifecycle Recovery Authority。**

开始 E6 前先写 `docs/superpowers/plans/` 计划。目标是通过共享 command registry 提供 Qt-free operator inspection/list/resolve seam，读取 E5 discovery/lifecycle reports，并对 blocked/failed/partial 状态定义显式、确认绑定、fail-closed 的恢复动作。不能把恢复逻辑塞进 PyQt panel，不能自动 force-unload/force-import，也不能改变 L0/L1、L2/L3/L4 层级。
