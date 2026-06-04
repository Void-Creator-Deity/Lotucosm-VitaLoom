# VitaLoom Engine 插件开发指南

## 概述

VitaLoom Engine 采用高度模块化的插件架构。除了核心框架之外，所有功能（包括 UI、视口、面板等）都以插件形式实现。

## 核心架构

### 核心框架（最小化）

核心框架只包含以下组件：

1. **EditorKernel** - 空白主窗口
2. **PluginLoader** - 插件加载器
3. **EventBus** - 事件总线
4. **LayoutManager** - 布局管理器
5. **EditorContext** - 编辑器上下文

### 插件系统

所有具体功能都通过插件实现：

- **视口插件** - Scene、Game、Cell Editor 等
- **Dock 面板插件** - Hierarchy、Inspector、Project、Console 等
- **菜单插件** - 菜单栏和工具栏
- **主题插件** - UI 主题
- **内容插件** - 实体类型、组件类型等

## 插件接口

### 基础插件接口

所有插件必须实现 `IEditorPlugin` 接口：

```python
from core.plugin.interfaces import IEditorPlugin

class MyPlugin(IEditorPlugin):
    def get_plugin_info(self):
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "Plugin description",
            "dependencies": [],  # 依赖的其他插件
            "provides": []       # 提供的接口类型
        }
    
    def on_load(self, editor_context):
        # 初始化插件
        self.context = editor_context
    
    def on_unload(self):
        # 清理资源
        pass
    
    def on_editor_ready(self):
        # 编辑器完全初始化后调用（可选）
        pass
```

### 专用插件接口

#### 1. Dock 面板插件 (`IDockProvider`)

```python
from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt

class MyDockPlugin(IDockProvider):
    def get_plugin_info(self):
        return {
            "name": "MyDock",
            "version": "1.0.0",
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def create_dock_widget(self):
        dock = QDockWidget("My Dock")
        # 创建你的 UI
        return dock
    
    def get_dock_config(self):
        return {
            "title": "My Dock",
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": True
        }
```

#### 2. 视口插件 (`IViewportProvider`)

```python
from core.plugin.interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget

class MyViewportPlugin(IViewportProvider):
    def get_plugin_info(self):
        return {
            "name": "MyViewport",
            "version": "1.0.0",
            "provides": ["viewport"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def create_viewport_widget(self):
        widget = QWidget()
        # 创建你的视口 UI
        return widget
    
    def get_viewport_id(self):
        return "my_viewport"
    
    def get_viewport_name(self):
        return "My Viewport"
    
    def on_viewport_activated(self):
        print("My viewport activated")
    
    def on_viewport_deactivated(self):
        print("My viewport deactivated")
```

#### 3. 菜单插件 (`IMenuProvider`)

```python
from core.plugin.interfaces import IMenuProvider

class MyMenuPlugin(IMenuProvider):
    def get_plugin_info(self):
        return {
            "name": "MyMenu",
            "version": "1.0.0",
            "provides": ["menu"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_menu_items(self):
        return [
            {
                "path": "Tools/My Tool",
                "action": self.my_action,
                "shortcut": "Ctrl+M"
            }
        ]
    
    def get_toolbar_items(self):
        return [
            {"text": "My Tool", "action": self.my_action}
        ]
    
    def my_action(self):
        print("My action triggered!")
```

#### 4. 主题插件 (`IThemeProvider`)

```python
from core.plugin.interfaces import IThemeProvider

class MyThemePlugin(IThemeProvider):
    def get_plugin_info(self):
        return {
            "name": "MyTheme",
            "version": "1.0.0",
            "provides": ["theme"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_theme_name(self):
        return "My Theme"
    
    def get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        /* ... more styles ... */
        """
    
    def get_color_scheme(self):
        return {
            "background": "#2d2d2d",
            "text": "#ffffff"
        }
```

## 插件间通信

使用事件总线进行插件间通信：

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
- `plugins/example_service_provider/service_provider_plugin.py`
- `plugins/example_service_consumer/service_consumer_plugin.py`

## 开发流程

### 1. 创建插件目录

```
plugins/
├── my_plugin/
│   ├── __init__.py
│   └── my_plugin_plugin.py
```

### 2. 实现插件类

在 `my_plugin_plugin.py` 中实现插件类，继承相应的接口。

### 3. 文件命名规则

插件文件必须以 `_plugin.py` 结尾，插件加载器会自动扫描这些文件。

### 4. 测试插件

重启编辑器，插件会自动加载。可以在 **Tools > Plugin Manager** 中查看和管理插件。

## 内置插件

VitaLoom Engine 包含以下内置官方插件（位于 `builtin/editor_extensions/`，属于 Official Mods）：

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
- **PluginManagerPlugin** - 插件管理器

## 示例插件

参考 `plugins/` 目录下的示例：

- **example_custom_viewport** - 自定义视口示例
- **example_custom_dock** - 自定义面板示例

这些示例展示了：
- 如何创建自定义 UI
- 如何使用事件总线通信
- 如何响应用户交互

## 最佳实践

1. **资源清理** - 在 `on_unload()` 中清理所有资源
2. **错误处理** - 捕获异常，避免影响其他插件
3. **事件订阅** - 记得在卸载时取消所有事件订阅
4. **依赖声明** - 在 `get_plugin_info()` 中声明插件依赖
5. **模块化设计** - 保持插件功能单一、独立

## 热重载

插件管理器支持热重载：

1. 打开 **Tools > Plugin Manager**
2. 选择要重载的插件
3. 点击 **🔄 Reload** 按钮

注意：热重载功能正在开发中，当前需要重启编辑器。

## 调试技巧

1. 使用 `print()` 输出调试信息到控制台
2. 检查 `logs/vitaloom_*.log` 文件
3. 使用事件总线发布调试事件
4. 在 Plugin Manager 中查看插件详情

## 常见问题

**Q: 我的插件没有被加载？**
A: 检查文件名是否以 `_plugin.py` 结尾，并且类是否继承了正确的接口。

**Q: 如何访问其他插件的功能？**
A: 使用事件总线进行通信，避免直接引用其他插件。

**Q: 插件加载顺序如何控制？**
A: 在 `get_plugin_info()` 中声明 `dependencies`，插件加载器会自动解析依赖顺序。

**Q: 如何禁用某个插件？**
A: 目前支持两种方式：

1. **项目级禁用（推荐）**：在 Plugin Manager 中选择插件，点击 **🚫 项目禁用**，会写入 `project.json.disabled_plugins`，打开该项目时会自动生效。
2. **物理移除（不推荐）**：删除/重命名插件文件（会影响所有项目）。

补充：如果你需要“一键禁用一组插件”，请使用 **Package Manager**（Unity 风格）：菜单 **Tools > Package Manager**。包清单默认来自 `builtin/package_index.json`，并可通过 `data/system/package_registries.json` 扩展来源。

补充（服务化包系统）：Package Manager 已将核心逻辑拆分为可复用服务并注册到 `EditorContext.services`：

- `package.catalog`：包源读取、优先级合并、更新候选计算
- `package.operations`：预览计划、写入覆盖、导出审计、回滚最近计划
- `package.operations` 还提供真实安装管线（zip 介质）与卸载接口，可用于官方/社区安装器插件复用

这意味着官方/社区插件可以在不耦合 UI 的情况下复用包系统能力。推荐只通过服务接口调用，不要直接依赖 `package_manager_plugin.py` 的窗口实现。

## 贡献

欢迎贡献新插件！请确保：
- 代码符合 PEP 8 规范
- 提供清晰的文档和注释
- 包含使用示例

---

**VitaLoom Engine - 高度模块化的生命模拟引擎**
