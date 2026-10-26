# 社区插件源

这里保存可供项目安装、引用或开发扫描的第三方/示例扩展。每个子目录包含 `*_plugin.py`，可选 `plugin.json` manifest。

> `workspace/extensions/user/` 与 `workspace/extensions/community/` 是插件源、缓存或开发区，**不会默认全局启用**。项目应通过 manifest/lock 与插件安装命令激活；本地开发可设置 `VITALOOM_ENABLE_WORKSPACE_EXTENSIONS=1` 扫描这些源。

## 示例

| 目录 | 类型 | Headless | 说明 |
|---|---|---:|---|
| `example_service_provider/` | `IRuntimePlugin` | 是 | 在 `on_load()` 向 runtime context 的 `services` 注册时间服务 |
| `example_service_consumer/` | `IRuntimePlugin` | 是 | 通过 `dependencies` 等待 provider，并在 `on_load()` 消费服务 |
| `example_custom_dock/` | `IRuntimePlugin` | 否 | 以可移植 `dock_surface` 声明编辑器外壳；Qt 工厂仅为 Adapter-local payload seam |
| `example_custom_viewport/` | `IRuntimePlugin` | 否 | 以可移植 `viewport_surface` 声明编辑器外壳；Qt 工厂仅为 Adapter-local payload seam |

## 新插件作者契约

新插件应直接继承 Qt-free `core.VitaLoom.core.runtime_plugin_contract.IRuntimePlugin`。`get_plugin_info()` 的 `editor_contributions` 只发布由 Host 复制的 JSON-safe 外壳事实；不要把 QWidget、Qt 对象、工厂、回调或任何 live state 放入 metadata。必需初始化应放在 `on_load()` 与已声明的 contracts 中；`on_editor_ready()` 只是可选、best-effort 的 Adapter 通知。

Dock 与 Viewport 的 `create_dock_widget()` / `create_viewport_widget()` 仍可保留，但它们是 `LegacyEditorPluginAdapter` 消费的具体 PyQt payload seam，不是新的插件继承或生命周期权威。

`core.VitaLoom.kernel.plugin_interfaces` 中的 `IEditorPlugin`、`IDockProvider`、`IViewportProvider` 等公开导入继续保留给历史兼容；**不要把它们作为新插件模板**。真正创建 QWidget 的 GUI payload 仍必须在自己的 module 中显式导入 PyQt6。

测试夹具位于 `tests/fixtures/workspace/extensions/user/`，只构成 **compatibility-only regression surface**，并且 **not an official new-plugin template**；它们用于隔离 PluginLoader 的历史兼容回归，不是新的作者示例。
