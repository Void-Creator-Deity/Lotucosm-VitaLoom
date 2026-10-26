# VitaLoom Engine 插件开发指南

## 概述

**插件化仅指织机（VitaLoom）编辑器 UI**：Dock、视口、菜单、主题等通过 `*_plugin.py` 注册。

**不是插件：**

- **Lotucosm（莲池）** — 产品版本 `runtime/core/Lotucosm/` 运行时（Cosmos、Pond、`.pond` tick）
- **工程内容** — `workspace/projects/` 场景与脚本

架构分层见 [docs/architecture.md](../architecture.md)。

## 核心架构

### 织机宿主（产品版本 `runtime/core/VitaLoom/`）

编辑器壳层，负责加载插件并挂载 UI，不替代莲池 tick：

1. **EditorKernel** — 主窗口
2. **PluginLoader** — 扫描 `*_plugin.py`
3. **EventBus** / **LayoutManager** / **EditorContext**

### 编辑器插件（本文档范围）

通过 Qt-free `IRuntimePlugin` 实现；`IEditorPlugin` 仅保留给未迁移社区插件的兼容导入：

- **视口插件** — Scene、Game、Cell Editor
- **Dock 插件** — Hierarchy、Inspector、Project、Console
- **菜单 / 主题插件**

官方组件与实体类型在产品版本 `runtime/builtin/components`、`runtime/builtin/entity_types`，由莲池运行时与工厂注册，**与 Dock 插件不是同一机制**。

## 插件接口

### 基础插件接口

新插件必须实现 Qt-free `IRuntimePlugin`；`IEditorPlugin` 是旧插件的兼容导入，不再是运行时发现或 Editor-ready 投递的前提：

```python
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

class MyPlugin(IRuntimePlugin):
    def get_plugin_info(self):
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "Plugin description",
            "dependencies": [],  # 依赖的其他插件
            "provides": []       # 提供的接口类型
        }

    def on_load(self, runtime_context):
        # 初始化插件；不要依赖具体 Qt Host 对象
        self.context = runtime_context

    def on_unload(self):
        # 清理资源
        pass

    def on_editor_ready(self):
        # 可选、Adapter-local、best-effort 通知；不可作为必需初始化步骤
        pass
```

当现有社区插件仍继承 `IEditorPlugin` 时，兼容行为会继续保留；新代码不应再以该旧接口作为能力声明。
### 专用编辑器贡献

Dock 与 Viewport 的**新作者路径**都直接继承 Qt-free `IRuntimePlugin`。在 `get_plugin_info()` 中通过 `editor_contributions` 声明可复制、JSON-safe 的 Editor shell 事实；现有 `LegacyEditorPluginAdapter` 负责把这些事实投影到 Qt 布局，并只在该 Adapter-local seam 调用具体 widget factory。

不要把 widget、factory、callback、Qt 对象或其他 live state 放进 `editor_contributions`。`create_dock_widget()` 与 `create_viewport_widget()` 可以继续包含 PyQt 内容，但不是 portable metadata，也不需要旧 provider 的 `get_dock_config()`、`get_viewport_id()` 或 `get_viewport_name()`。

#### 1. Dock 面板插件

```python
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QDockWidget


class MyDockPlugin(IRuntimePlugin):
    def get_plugin_info(self):
        return {
            "name": "MyDock",
            "version": "1.0.0",
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "my_dock.surface",
                    "kind": "dock_surface",
                    "dock_id": "my_dock",
                    "title_key": "my_dock.title",
                    "default_title": "My Dock",
                    "area": "right",
                    "default_visible": True,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 100,
                    "refresh_events": [],
                }
            ],
        }

    def on_load(self, runtime_context):
        self.context = runtime_context

    def on_unload(self):
        pass

    def create_dock_widget(self) -> QDockWidget:
        # LegacyEditorPluginAdapter 调用的具体 PyQt payload seam。
        return QDockWidget("My Dock")
```

`area` 只使用 portable token：`left`、`right`、`top` 或 `bottom`。Dock 标识、标题 key、默认标题和可见性都由贡献元数据声明；Host 会复制并验证这些事实，不能由 widget 反向成为运行时 authority。

#### 2. 视口插件

```python
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QWidget


class MyViewportPlugin(IRuntimePlugin):
    def get_plugin_info(self):
        return {
            "name": "MyViewport",
            "version": "1.0.0",
            "provides": ["viewport", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "my_viewport.surface",
                    "kind": "viewport_surface",
                    "viewport_id": "my_viewport",
                    "name_key": "my_viewport.name",
                    "default_name": "My Viewport",
                    "order": 100,
                    "refresh_events": [],
                }
            ],
        }

    def on_load(self, runtime_context):
        self.context = runtime_context

    def on_unload(self):
        pass

    def create_viewport_widget(self) -> QWidget:
        # LegacyEditorPluginAdapter 调用的具体 PyQt payload seam。
        return QWidget()

    def on_viewport_activated(self):
        print("My viewport activated")

    def on_viewport_deactivated(self):
        print("My viewport deactivated")
```

`viewport_id`、显示名称与排序来自声明式贡献，而不是旧 getter。`IEditorPlugin`、`IDockProvider` 与 `IViewportProvider` 的 public import 会为历史插件继续保留，但它们只属于 compatibility regression surface，不是新插件模板。

#### 3. 菜单插件 (`IMenuProvider`)
### 发布事件

```python
def on_load(self, editor_context):
    self.context = editor_context
    # 发布事件
    self.context.event_bus.publish("my_event", {"data": "hello"})
```

### 订阅事件

```python
def on_load(self, editor_context):
    self.context = editor_context
    # 订阅事件
    self.context.event_bus.subscribe("my_event", self.on_my_event)

def on_my_event(self, data):
    print(f"Received: {data}")

def on_unload(self):
    # 记得取消订阅
    self.context.event_bus.unsubscribe("my_event", self.on_my_event)
```

### 服务注册表（Service Registry）

除了事件总线，插件还可以通过 `EditorContext.services` 暴露可复用能力（避免硬编码 import）。

#### 提供服务

```python
class MyService:
    service_name = "my.service"
    service_version = "1.0.0"

    def ping(self):
        return "pong"

def on_load(self, editor_context):
    self.context = editor_context
    self.context.services.register("my.service", MyService())

def on_unload(self):
    self.context.services.unregister("my.service")
```

#### 消费服务

```python
def on_editor_ready(self):
    service = self.context.services.get("my.service")
    if service:
        print(service.ping())
```

推荐同时做版本门槛校验（例如 `>=1.0.0`），避免多个插件升级后发生静默兼容性问题。

示例参考：
- `workspace/extensions/community/example_service_provider/service_provider_plugin.py`
- `workspace/extensions/community/example_service_consumer/service_consumer_plugin.py`

## 开发流程

### 1. 创建插件目录

```text
workspace/extensions/user/
└── my_plugin/
    ├── __init__.py
    └── my_plugin_plugin.py
```

### 2. 实现插件类

在 `my_plugin_plugin.py` 中实现插件类，继承相应的接口。

### 3. 文件命名规则

插件文件必须以 `_plugin.py` 结尾，插件加载器会自动扫描这些文件。

### 4. 测试插件

`workspace/extensions/` 是插件源，不会默认全局启用。将插件安装/绑定到当前项目，或在本地开发时设置 `VITALOOM_ENABLE_WORKSPACE_EXTENSIONS=1` 后启动编辑器；随后可在 **Tools > 插件管理器**（`PackageManagerPlugin`）中查看和管理。

### 5. 嵌入当前项目的 L4 addon

若扩展要随单个 Project World 分发，放入 `<project>/addons/<addon>/`，并提供 authority manifest：

```text
<project>/addons/my_plugin/
├── plugin.json
└── my_plugin_plugin.py
```

```json
{
  "schema_version": 1,
  "id": "MyPlugin",
  "version": "1.0.0",
  "entry": "my_plugin_plugin.py",
  "runtime": {
    "plugin_id": "lotucosm-vitaloom",
    "version": ">=1.0.0,<2.0.0"
  },
  "dependencies": []
}
```

项目 addon 仅在 project-open 后发现。`plugin.json` 与 `get_plugin_info()` 的 id/version/dependencies 必须一致；入口必须留在 addon 根内。缺 manifest、路径逃逸、symlink、重复 id、runtime 不兼容、缺依赖或循环依赖都会 fail closed，不会使用递归扫描结果“尽力加载”。

## 内置插件

VitaLoom Engine 包含以下内置官方插件（位于产品版本 runtime 的 `builtin/editor_extensions/`，属于 Official Mods）：

- **UnityDarkThemePlugin** - Unity Dark 主题
- **StandardUIPlugin** - 标准菜单和工具栏
- **HierarchyPlugin** - 场景层级面板
- **InspectorPlugin** - 属性检视器
- **ProjectBrowserPlugin** - 项目浏览器
- **ConsolePlugin** - 控制台
- **SceneViewportPlugin** - 场景视口
- **GameViewportPlugin** - 游戏视口
- **CellEditorPlugin** - 细胞编辑器
- **CellSimulationPlugin** - 细胞模拟系统
- **PackageManagerPlugin** - 插件管理器（扩展包 + 运行时插件）
- **HotReloadPlugin** - 热重载菜单（未列入 `package_index`，默认不激活）

`PluginManagerPlugin` 已合并进 `PackageManagerPlugin`，模块仅作兼容存根。

## 示例插件

`workspace/extensions/community/` 是社区插件源、缓存与开发区，不会在冷启动时默认全局启用。目录内提供四个正式示例：

- **example_service_provider** - 只依赖基础插件 Interface，可在无 PyQt6 环境 Headless 导入并注册服务
- **example_service_consumer** - 通过 `dependencies` 声明 provider 顺序，可在无 PyQt6 环境消费服务
- **example_custom_dock** - 显式依赖 PyQt6 的自定义 Dock 面板示例
- **example_custom_viewport** - 显式依赖 PyQt6 的自定义视口示例

这些示例分别展示服务注册表、依赖拓扑、事件通信和 UI 注入。运行时应先将插件安装/绑定到目标项目；仅在本地开发扫描时设置 `VITALOOM_ENABLE_WORKSPACE_EXTENSIONS=1`。

## 最佳实践

1. **资源清理** - 在 `on_unload()` 中清理所有资源
2. **错误处理** - 捕获异常，避免影响其他插件
3. **事件订阅** - 记得在卸载时取消所有事件订阅
4. **依赖声明** - 在 `get_plugin_info()` 中声明插件依赖
5. **模块化设计** - 保持插件功能单一、独立

## 热重载

插件管理器提供 **重载** 按钮；`HotReloadPlugin` 可在菜单中重载 `user_mod` 插件（需自行将其加入工程包映射或设置 `VITALOOM_EAGER_PLUGINS=1` 调试）。

多数官方插件仍建议 **重启编辑器** 后再验证 UI 注入与依赖顺序。

## 生命周期故障检查与恢复

开发 L3/L4 插件时，不要从 PyQt Dock 私有字段推断加载状态。通过共享命令检查 live Host：

```text
plugin.host.inspect
plugin.host.recovery.list
```

若当前 report 提供 `retry_project_lifecycle`，必须把 list/inspect 返回的 `project_path`、`report_id`、`action` 和 `operator_confirmation_required` 原样传给 `plugin.host.recovery.resolve`。任何 catalog、active set 或 report 变化都会使旧确认失效。

failed/partial callback 可能已经产生第三方副作用。retry 只会重新执行标准 manifest discovery 和 lifecycle sync，不会 force-unload、force-import 或通用回滚；必要时先修复插件实现并重启 Host。

## 调试技巧

1. 使用 `print()` 输出调试信息到控制台
2. 检查 `logs/vitaloom_*.log` 文件
3. 使用事件总线发布调试事件
4. 在 **插件管理器** 中查看插件详情

## 常见问题

**Q: 我的插件没有被加载？**
A: 检查文件名是否以 `_plugin.py` 结尾，并且类是否继承了正确的接口。

**Q: 如何访问其他插件的功能？**
A: 使用事件总线进行通信，避免直接引用其他插件。

**Q: 插件加载顺序如何控制？**
A: 在 `get_plugin_info()` 中声明 `dependencies`，插件加载器会自动解析依赖顺序。

**Q: 如何禁用某个插件？**
A: 目前支持两种方式：

1. **项目级禁用（推荐）**：在 **插件管理器** 中选择插件，点击 **项目禁用**，会写入 `project.json.disabled_plugins`，打开该项目时会自动生效。
2. **按扩展包禁用**：在插件管理器的扩展包列表中禁用整包（同样写入 `disabled_plugins`）。
3. **物理移除（不推荐）**：删除/重命名插件文件（会影响所有项目）。

包清单默认来自产品版本 runtime 内的 `runtime/builtin/package_index.json`，并可通过 `workspace/state/system/package_registries.json` 扩展来源。

**服务化包系统**：插件管理器已将核心逻辑拆分为可复用服务并注册到 `EditorContext.services`：

- `package.catalog`：包源读取、优先级合并、更新候选计算
- `package.operations`：预览计划、写入覆盖、导出审计、回滚最近计划
- `package.operations` 还提供真实安装管线（zip 介质）与卸载接口，可用于官方/社区安装器插件复用

这意味着官方/社区插件可以在不耦合 UI 的情况下复用包系统能力。推荐只通过服务接口调用，不要直接依赖 `package_manager_plugin.py` 的窗口实现。

## 模拟运行时接缝（SR / PS）

全引擎 SR 播放与 PS 批处理的分阶段统一见 [docs/runtime_unification_roadmap.md](../runtime_unification_roadmap.md)。

插件开发时请遵守：

1. **不要**在插件内实现第二套 `GameViewport` tick 或 `Pond.update` 循环。
2. **生态/指标类 UI** 应使用 `core.VitaLoom.simulation.ecology_registry.collect_ecology_snapshots(editor_context)`，不要直接读取视口私有字段。
3. **可订阅事件**：`simulation_transport_state`、`ps_experiment_state`、`ps_experiment_finished`（与官方 `StandardUIPlugin` / 实验 Dock 一致）。
4. **批处理/实验** 应注册到 `EditorContext.services`（键名建议带插件前缀），或复用官方 `ps_experiment` 服务，勿 fork `PsExperimentRunner`。
5. **视口叠加**（Phase C.2 后）通过规划中的 `vitalloom.runtime.replay` 包，不在社区插件里改 `game_viewport.py`。

## 贡献

欢迎贡献新插件！请确保：
- 代码符合 PEP 8 规范
- 提供清晰的文档和注释
- 包含使用示例

---

**VitaLoom Engine - 高度模块化的生命模拟引擎**






