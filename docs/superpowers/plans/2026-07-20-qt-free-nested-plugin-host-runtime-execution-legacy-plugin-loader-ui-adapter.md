# Phase E20 — Qt-free Nested Plugin Host Runtime Execution Authority and Legacy PluginLoader UI Contribution Adapter

- **日期：** 2026-07-20
- **状态：** completed
- **前置 Gate：** E19 已完成 Qt-free `IRuntimePlugin` lifecycle Interface 与 legacy `IEditorPlugin` 兼容层；focused `6 passed`，排除 signature 文件的完整套件 `1226 passed, 25 skipped, 34 subtests passed`，四项架构门禁通过
- **唯一目标：** 将 downstream nested plugin Host 的 registry/discovery/dependency/callback execution 从 legacy PyQt Editor `PluginLoader` 中提取为 Qt-free deep Module；`PluginLoader` 保持兼容并收敛为 Editor contribution、editor-ready、command bridge 与 Host signal Adapter

## 固定架构事实

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       FrameCore 中唯一引擎/产品大插件
       同时是 downstream nested plugin-host framework
       -> versions/1.0.0/runtime（版本实现承载边界）
            -> L2 VitaLoom capability/domain package
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon
```

- 不把 L2/L3/L4 提升为并列 FrameCore 插件。
- PyQt6/QPainter/OpenGL 是现有或遗留 UI Host Adapter，不是引擎根、插件 authority 或扩展规则来源。
- 不迁移到 Unity、Godot、Unreal、Electron 或其他 app shell。
- 保持 `.pond`、AI Command Registry、Inspector command binding、SR2D、package/project manifests、Player/export 与 L3/L4 lifecycle。

## PluginLoader 审计

当前 `core/VitaLoom/kernel/plugin_loader.py` 约 1321 行，同时承担两类职责：

| Qt-free nested Host 职责 | legacy Editor Adapter 职责 |
|---|---|
| filesystem scan、module import、`IRuntimePlugin` class discovery/实例构造 | Dock/Viewport/Menu/Theme contribution 到 LayoutManager |
| plugin registry、dependencies、scope、source、protected facts ownership | legacy `IEditorPlugin.on_editor_ready` |
| activation metadata 调用 E17 authority、catalog projection | Editor context 到 runtime projection 的兼容入口 |
| dependency ordering、E5 lifecycle plan execution | `plugin_loaded` / `plugin_unloaded` kernel signals |
| `on_load` / `on_unload` callback execution与 deterministic failure facts | command registry legacy bridge 与 UI cleanup |
| hot-reload candidate import/activation/deactivation primitives | pending dock tabify 与 ThemeManager concrete integration |

现有 E17/E5 Module 已决定 metadata/schema、L4 discovery/lifecycle plan、operator/reload plan；E20 不复制这些规则，只让新的 Host Module 调用它们并拥有 callback execution。

## 目标 Module 与 Interface

候选路径（以实现审计结果为准）：

```text
core/VitaLoom/core/runtime_plugin_host.py
```

该 Module 必须：

1. 不 import PyQt、`kernel.plugin_interfaces`、LayoutManager、EditorKernel、ThemeManager 或 concrete UI Host。
2. 拥有 registry/loaded/dependency/order/failure/discovery/scope/source/protected 状态。
3. 提供 plugin registration/discovery/import/dependency resolution/catalog/lifecycle execution 的小 Interface。
4. 通过窄 Adapter hooks 接收 activation-context resolution 与 Editor contribution/signal side effects；headless Adapter 可为空。
5. 直接执行 `IRuntimePlugin.on_load` / `on_unload`，并生成与现有 lifecycle report 兼容的确定性 facts。
6. legacy `PluginLoader` 对外属性与方法保持兼容，内部委托给 Host；现有测试和第三方调用不需同时迁移。

## 红测顺序

1. 新 `tests/test_runtime_plugin_host.py` 在拦截 PyQt/legacy plugin-interface import 时导入 Host Module。
2. headless Host 不需要 kernel/LayoutManager/IEditorPlugin 即可 register、dependency-order activate、reverse-order deactivate。
3. activation 失败时依赖者被稳定 skip，report 保持 `failed_action` / `skipped.activation` facts。
4. Host discovery 接受 plain `IRuntimePlugin`，并保持 ID、dependencies、scope、source、protected 与 activation metadata 校验。
5. legacy `PluginLoader` registry state 由 Host 拥有；UI contribution/editor-ready/signals 仍经 Adapter 恰好执行一次。

## 实现顺序

1. 写上述红测并记录初始失败。
2. 新增 Qt-free Host Module，先实现状态、registration/discovery、dependency/catalog 与 lifecycle callback execution。
3. 将 `PluginLoader` 初始化改为组合 Host，并为旧 public attributes 建立同一对象别名。
4. 将 `_scan_directory`、`_discover_plugin`、`_resolve_dependencies`、`_catalog_entries`、`_execute_lifecycle_target`、`_load_plugin`、`unload_plugin`、candidate import 委托给 Host。
5. 保留 Project World addon、operator、reload report 的现有外层 orchestration；它们继续调用 E5/E17 authority，不复制规则。
6. 运行 focused、expanded、full（明确 signature blocker）与四项架构门禁，更新状态与下一 prompt。

## 完成定义

- Host Module 在无 PyQt/EditorKernel 环境可 import 并执行 plain runtime plugin lifecycle。
- registry 与 callback execution authority 不再由 `PluginLoader` 自身实现。
- legacy Editor UI contribution、editor-ready、signals、command registry 行为兼容。
- plugin ID、dependency ordering、scope priority、official/user/embedded/L4 discovery、protected rules、activation context、reload/unload reports 不变。
- focused/expanded/full 回归与四项架构门禁有新证据；signature 缺依赖若仍存在必须明确记录。

## 非目标

- 不在 E20 替换 PyQt UI Host。
- 不在 E20 完成 native acceleration 或 OpenGL default-ready。
- 不重写 E17 activation schema、E5 lifecycle planner/operator/reload planner。
- 不宣称整个项目已经“彻底完善”。


## 实现结果（2026-07-20）

- 新增 Qt-free `core/VitaLoom/core/runtime_plugin_host.py`。`RuntimePluginHost` 位于唯一 L1 引擎大插件的版本 runtime 内，拥有 registry、loaded、dependencies、order、failure、discovery、scope、source、protected 与 lifecycle report facts；它不是 FrameCore 并列插件或第二根框架。
- Host 直接调用既有 E17 activation schema 与 E5 lifecycle planner，不复制其规则；plain `IRuntimePlugin` 可在无 PyQt、EditorKernel、LayoutManager 或 legacy `kernel.plugin_interfaces` 的环境完成 discovery、dependency-order activation 与 reverse-order deactivation。
- legacy `PluginLoader` 组合一个 `RuntimePluginHost`，旧 public state 与 Host 使用同一对象别名，并将 discovery、dependency resolution、catalog、lifecycle execution、load/unload、candidate import 与 bytecode invalidation 委托给 Host。
- `PluginLoader` 继续只负责 concrete Editor Adapter side effects：Dock/Viewport/Menu/Theme、command bridge、legacy `IEditorPlugin.on_editor_ready`、kernel signals、UI cleanup 与 pending dock tabify。
- 保持 metadata 原始名称的 legacy load signal、canonical unload signal、scope priority、protected facts、activation context、official/user/embedded/L4 discovery、reload/unload report 与 manifest 语义。
- 修正 `project/plugin_host_lifecycle.py` authority 说明：Qt-free `RuntimePluginHost` 负责 import/runtime callbacks，Editor/UI Adapter 只负责具体 UI contribution 和 legacy Host signals。

## 验证证据

| Gate | Fresh evidence |
|---|---|
| Previous gate | E19 已完成 Qt-free `IRuntimePlugin` Interface 与 legacy `IEditorPlugin` Adapter；基线为 `1226 passed, 25 skipped, 34 subtests passed`。 |
| Initial red | 新 E20 测试首次运行 `5 failed`：Host Module 尚不存在且 Loader 尚未组合 Host。 |
| Focused | `tests/test_runtime_plugin_host.py tests/test_runtime_plugin_contract.py`：`11 passed in 0.29s`。 |
| Expanded plugin lifecycle | activation/context/contract/commands/failure-isolation/lifecycle/operator/reload/hot-reload/runtime contract/Host：`54 passed in 1.10s`。 |
| Broader compatibility | engine architecture、Project World transition、startup、package governance/install/migration/services、community migration、layout、Host：`57 passed in 3.22s`。 |
| Full suite | 排除当前环境无法收集的 signature 文件后：`1231 passed, 25 skipped, 34 subtests passed in 92.20s`。 |
| Architecture guardrails | `project plugin model OK`、`core boundaries OK`、`GUI boundaries OK`、`release consistency OK`。 |
| Environment blocker | `tests/test_package_signature_warn_only.py` collection 仍因 `ModuleNotFoundError: No module named 'cryptography'` 失败；未宣称 signature 已验证。 |

## 稳定范围与未完成项

**本 Gate 已稳定：** Qt-free nested plugin Host 的 registry/discovery/dependency/callback execution Interface、legacy Loader state alias、Editor UI contribution Adapter 兼容，以及 E19 和既有 L3/L4 lifecycle 行为。

**仍未完成：** Project World addon scan/sync/operator/recovery orchestration 仍混在 legacy `PluginLoader`；manual hot-reload orchestration 仍在 Loader；legacy PyQt Host 替代尚未实施；native acceleration 与 OpenGL default-ready 仍缺完整 build/import/parity/benchmark/current-context evidence；signature 环境仍阻塞。

## 唯一下一 Gate

**Phase E21 — Qt-free Project-Scoped Nested Plugin Host Orchestration and Legacy `PluginLoader` Project Adapter.**

第一动作：先写 E21 phase plan 和红测，把 `clear_embedded_plugins`、`scan_project_addons`、`sync_plugins_for_project`、inspection/recovery 的 Project World orchestration 从 legacy Loader 提取到同一 L1/versioned-runtime 内的 Qt-free deep Module；它组合 E20 `RuntimePluginHost` 并继续调用既有 lifecycle/operator authorities。E21 不处理 manual hot reload、UI Host 替换、native/OpenGL，也不改变 L0–L4 拓扑或 manifests。
