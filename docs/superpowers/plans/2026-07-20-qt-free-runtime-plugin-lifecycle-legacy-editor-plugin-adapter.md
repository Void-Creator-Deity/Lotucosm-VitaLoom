# Phase E19 — Qt-free Runtime Plugin Lifecycle Interface and Legacy IEditorPlugin Adapter Compatibility Authority

- **日期：** 2026-07-20
- **状态：** complete
- **前置 Gate：** E18 已完成 Editor/Player viewport capability publication 生命周期闭环；E14–E17 已稳定 L0/L1 registry、event seam、runtime projection 与 activation schema
- **唯一目标：** 在唯一 L1 引擎大插件的版本 runtime 内建立 Qt-free runtime plugin lifecycle Interface，让非 UI L2/L3/L4 插件不再依赖 legacy `kernel/plugin_interfaces.py::IEditorPlugin`；现有 `IEditorPlugin`、Dock、Viewport、Menu、Theme 等继续作为 PyQt Host Adapter 兼容层。

## 架构事实

`lotucosm-vitaloom` 是 FrameCore 唯一的 L1 引擎/产品大插件，同时是下层 plugin-host framework：

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin + nested plugin Host
      -> versions/1.0.0/runtime (versioned runtime boundary)
          -> L2 capability/domain package
          -> L3 engine extension / Host Adapter
          -> L4 Project World addon
```

本阶段只在上述 versioned runtime 内深化插件 lifecycle seam；不创建并列 FrameCore 插件，不把 L2/L3/L4 提升层级，也不让 PyQt 成为 extension authority。

## 审计证据

- `PluginLoader` 的 discovery、registry 类型、load、unload 与 hot reload 实例化当前全部以 `IEditorPlugin` 为唯一基类。
- `IEditorPlugin` 位于 legacy `kernel` Module，接口与文档使用 `editor_context`、Editor ready 和 QWidget 清理语义。
- 已明确声明 `activation_context: runtime` 的真实非 UI插件包括 `DownloaderPlugin`、`CellSimulationPlugin`、`PsReplayOverlayPlugin`；它们只应收到 E16 的窄 runtime projection。
- Dock、Viewport、Menu、Theme 等 Provider 是 legacy UI Host Adapter seam，不能因提取 runtime contract 而改成引擎根 authority。
- Entity/Component type provider 不包含 QWidget/PyQt 行为，属于 runtime/domain provider seam；旧 import path 必须通过 legacy compatibility Adapter 保持 `IEditorPlugin` subclass 语义。

## 设计约束

1. 新增 Qt-free `core/VitaLoom/core/runtime_plugin_contract.py`，定义最小 `IRuntimePlugin`：`get_plugin_info`、`on_load(runtime_context)`、`on_unload`。
2. `IEditorPlugin(IRuntimePlugin)` 只增加 legacy `on_editor_ready()`，保留所有旧 UI Provider 和第三方插件 subclass 兼容。
3. Qt-free Entity/Component provider Interface 与 runtime lifecycle 同址；`kernel/plugin_interfaces.py` 以同时继承 runtime provider 与 `IEditorPlugin` 的 compatibility Adapter 保留旧 import/subclass seam。
4. `PluginLoader` 以 `IRuntimePlugin` 发现、登记、加载、卸载与重载；只有 `IEditorPlugin` 才调用 `on_editor_ready()`。
5. UI registration 仍只通过 `IDockProvider` / `IViewportProvider` / `IMenuProvider` / `IThemeProvider` 判断，不允许 runtime 基接口触碰 LayoutManager。
6. 迁移三个明确 runtime 插件到 Qt-free contract；不迁移 `LocalizationPlugin` 等依赖 kernel/widget/editor-ready 的 legacy 插件。
7. 不改变 `activation_context` 缺省/校验、plugin ID、dependency ordering、official/user/embedded/L4 discovery、operator reports、reload/unload、manifest 或 Project World lifecycle。

## 红测与验证顺序

1. 红测证明 runtime contract 在拦截 PyQt import 时可独立导入。
2. 红测证明 plain `IRuntimePlugin` 可被 discovery/load/unload，且不要求或调用 `on_editor_ready`。
3. 红测证明 `IEditorPlugin` 是兼容子类型，Dock/Viewport/Menu/Theme 仍是 legacy editor Adapter。
4. 红测证明 Entity/Component provider 的旧 import path 仍是 `IEditorPlugin`，同时满足 Qt-free provider Interface。
5. 红测证明三个明确 runtime 插件不再依赖 `kernel.plugin_interfaces`，metadata 与 plugin ID 不变。
6. 实现最小 deep Module 后，运行 focused、插件 lifecycle/activation/reload 扩展回归、E12–E18 回归、完整套件（如 signature 环境仍缺依赖则诚实排除并记录）和四项架构门禁。

## 完成定义

- 新 runtime lifecycle Module 可在 PyQt 不可导入环境中加载。
- Runtime-only plugin 不需要 legacy editor callback 即可完成 discovery/load/unload/hot reload。
- 旧 `IEditorPlugin` 与 UI Provider public seam 保持兼容；现有 UI registration 行为不变。
- 三个明确 runtime 插件只依赖 Qt-free runtime contract。
- 相关测试、compileall、架构门禁和文档证据闭环；主线只命名一个下一 Gate。

## 非目标

- 不删除或替换 PyQt/QPainter/OpenGL Host Adapter。
- 不选定 Unity、Godot、Unreal、Electron 或其他 app shell。
- 不扩大 runtime activation projection，不建立 god context。
- 不修改 `.pond`、AI Command Registry、Inspector binding、SR2D、package/project manifests、Player/export 语义。
- 不在本阶段宣称 native acceleration、OpenGL default-ready、signature 环境或整个项目已完成。

## E19 完成证据（2026-07-20）

- 新增 Qt-free `runtime_plugin_contract.py`，以 `IRuntimePlugin` 统一 metadata/load/unload；Entity/Component provider 作为 runtime/domain Interface 同址。
- `IEditorPlugin(IRuntimePlugin)` 现在只保留 legacy `on_editor_ready()`；Dock、Viewport、Menu、Theme Provider 仍由旧 Editor Host Adapter 管理。
- 旧 `kernel.plugin_interfaces.IEntityTypeProvider` / `IComponentTypeProvider` 保持 `IEditorPlugin` subclass 兼容，同时适配 Qt-free provider Interface。
- `PluginLoader` 的 discovery、registry、load/unload 与 reload 实例化接受 `IRuntimePlugin`；仅对 `IEditorPlugin` 调用 `on_editor_ready()`，UI registration 判断保持不变。
- `DownloaderPlugin`、`CellSimulationPlugin`、`PsReplayOverlayPlugin` 已迁移到 Qt-free contract，plugin ID 与 `activation_context: runtime` 保持不变。

验证：

```text
E19 red: 6 failed
E19 focused: 6 passed
Plugin/lifecycle/activation/operator/reload expansion: 128 passed, 1 skipped
Full suite excluding tests/test_package_signature_warn_only.py: 1226 passed, 25 skipped, 34 subtests passed in 99.04s
Architecture gates: project plugin model OK; core boundaries OK; GUI boundaries OK; release consistency OK
Changed-file compileall: passed
```

环境限制：`tests/test_package_signature_warn_only.py` 仍在 collection 阶段因当前 `.venv` 缺少 `cryptography` 失败；未安装网络依赖，不宣称 signature 已验证。

## 唯一下一 Gate

**Phase E20 — Qt-free Nested Plugin Host Runtime Execution Authority and Legacy `PluginLoader` UI Contribution Adapter.** 第一动作：审计 `PluginLoader` 中 discovery/import、registry ownership、activation callback execution、unload/reload 与 kernel signal/LayoutManager UI contribution 的混合职责；先写 headless/runtime red tests，再把非 UI Host 执行规则提取到版本 runtime 内的 Qt-free deep Module，让 Editor、Player、headless 与未来 UI Host 共享同一 runtime plugin Host，而 legacy `PluginLoader` 只保留 UI contribution、Editor-ready 与 Host signal Adapter。不得复制 E17 activation schema、E18 cleanup、L4 lifecycle planner 或 operator authority，也不得改变 L0–L4 拓扑。
