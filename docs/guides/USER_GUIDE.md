# VitaLoom Engine 深度使用指南

> **安装与 5 分钟上手**请读 [README_QUICK_START.md](README_QUICK_START.md)。  
> **文档总索引**：[docs/INDEX.md](../INDEX.md)

## 📚 目录

1. [基本使用](#基本使用)
2. [插件/Mod 开发指南](#插件mod-开发指南)
3. [实体类型开发](#实体类型开发)
4. [组件类型开发](#组件类型开发)
5. [API 参考](#api-参考)
6. [示例项目](#示例项目)
7. [常见问题](#常见问题)

---

## 🚀 快速开始

已合并至 **[README_QUICK_START.md](README_QUICK_START.md)**（依赖安装、`python main.py`、打开示范工程）。下文从界面与编辑流程展开。

---

## 📖 基本使用

### 界面概览

VitaLoom Engine 采用类似 Unity 的界面布局：

- **顶部菜单栏** - 文件、编辑、工具等操作
- **工具栏** - 常用工具快捷按钮
- **左侧面板** - Hierarchy（层级面板）
- **右侧面板** - Inspector（属性面板）、Project（项目浏览器）
- **底部面板** - Console（控制台）
- **中央视口** - Scene（场景编辑）、Game（游戏运行）、Cell Editor（细胞编辑）

### 场景编辑

#### 创建实体

1. 在 **Scene Viewport** 中右键点击
2. 选择 **创建生物体** 或其他实体类型
3. 在场景中点击放置实体

#### 选择实体

- **单击** - 选择单个实体
- **Ctrl + 单击** - 多选实体
- **拖拽** - 移动选中的实体

#### 编辑属性

1. 选择实体
2. 在 **Inspector** 面板中查看和编辑属性
3. 修改会立即生效

### 运行模拟

1. 点击工具栏的 **▶ Play** 按钮
2. 切换到 **Game Viewport** 观察运行效果
3. 点击 **⏸ Pause** 暂停
4. 点击 **⏹ Stop** 停止

### 项目管理

#### 创建新项目

1. 菜单：**File > New Project**
2. 输入项目名称
3. 选择保存位置

#### 打开项目

1. 菜单：**File > Open Project**
2. 选择项目文件夹

#### 保存场景

1. 菜单：**File > Save Scene**
2. 或使用快捷键 `Ctrl + S`

---

## 🔌 插件/Mod 开发指南

VitaLoom Engine 采用 **FrameCore 大插件 + 版本 runtime + 能力包** 架构：L0 `FrameCore` 只发现 `lotucosm-vitaloom` 大插件；Hub 在大插件根；莲池运行时与织机宿主位于 `versions/<version>/runtime/`；主要 Dock/视口由 `*_plugin.py` 注册。你可以创建用户/社区插件扩展编辑器功能。详见 [docs/architecture.md](../architecture.md)。

### 插件类型

VitaLoom Engine 的新插件统一从 Qt-free `IRuntimePlugin` 开始；能力由 `provides` 与已验证、Host-copied 的 metadata 声明。常见扩展类别包括：

1. **Dock surface** - 可停靠的编辑器面板
2. **Viewport surface** - 编辑器中央工作区
3. **菜单/工具栏** - 命令入口
4. **主题** - 视觉配置
5. **实体类型** - 领域实体扩展
6. **组件类型** - 领域组件扩展
7. **其他 runtime 服务** - 无 UI 的功能插件

`IEditorPlugin`、`IDockProvider`、`IViewportProvider` 仍保留 public import，供已有插件和兼容回归使用；它们不是新的运行时发现或 Editor-ready authoring authority。实体/组件 provider 的既有继承契约不在本节变更范围内。

### 插件基础结构

新插件必须实现 Qt-free `IRuntimePlugin`：

```python
from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class MyPlugin(IRuntimePlugin):
    def get_plugin_info(self) -> Dict[str, Any]:
        """返回稳定插件信息。"""
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "插件描述",
            "dependencies": [],
            "provides": [],
        }

    def on_load(self, runtime_context):
        """插件加载时调用；必需初始化在这里完成。"""
        self.context = runtime_context

    def on_unload(self):
        """卸载时清理所有资源、订阅和已发布服务。"""
        pass

    def on_editor_ready(self):
        """可选、best-effort 的 Adapter-local Editor-ready 通知。"""
        pass
```

`on_editor_ready()` 只会在现有贡献投影之后以可调用能力检查投递；缺失、非可调用或抛错都不会改变 Host 生命周期。因此不要把必需初始化、持久状态或可移植插件契约放进该回调。

### 1. Dock 面板插件

Dock 面板是可以在编辑器边缘停靠的面板，如 Hierarchy、Inspector 等。新插件把 shell 事实放在 JSON-safe 的 `dock_surface` 贡献中；具体 PyQt widget factory 留在 `LegacyEditorPluginAdapter` 调用的 payload seam。

#### 完整示例

```python
from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QWidget


class MyDockPlugin(IRuntimePlugin):
    """自定义 Dock 面板插件。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyDock",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "一个自定义的 Dock 面板",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "my_dock.surface",
                    "kind": "dock_surface",
                    "dock_id": "my_dock",
                    "title_key": "my_dock.title",
                    "default_title": "My Panel",
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
        self.dock = None

    def on_unload(self):
        if self.dock:
            self.dock.deleteLater()

    def create_dock_widget(self) -> QDockWidget:
        """Adapter-local 的具体 PyQt 内容工厂。"""
        self.dock = QDockWidget("My Panel")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Hello from My Dock!"))
        self.dock.setWidget(widget)
        return self.dock
```

`editor_contributions` 只能包含可复制、JSON-safe 的 shell 事实；不要放入 widget、factory、callback、Qt 对象或 live state。`area` 使用 `left`、`right`、`top`、`bottom` 之一。不要为新插件实现 `get_dock_config()`。

### 2. 视口插件

视口是编辑器中央的主要工作区域，如 Scene、Game、Cell Editor 等。新插件用 `viewport_surface` 声明稳定的 ID、名称和排序；具体 widget 仍由 Adapter-local factory 提供。

#### 完整示例

```python
from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MyViewportPlugin(IRuntimePlugin):
    """自定义视口插件。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyViewport",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "一个自定义的视口",
            "dependencies": [],
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
        self.viewport = None

    def on_unload(self):
        if self.viewport:
            self.viewport.deleteLater()

    def create_viewport_widget(self) -> QWidget:
        """Adapter-local 的具体 PyQt 内容工厂。"""
        self.viewport = QWidget()
        layout = QVBoxLayout(self.viewport)
        label = QLabel("My Custom Viewport")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return self.viewport

    def on_viewport_activated(self):
        print("My viewport activated")

    def on_viewport_deactivated(self):
        print("My viewport deactivated")
```

不要为新插件实现 `get_viewport_id()` 或 `get_viewport_name()`；这些遗留 getter 的兼容投影不应成为新插件的契约。与 Dock 一样，贡献 metadata 不得携带 Qt 或其他 live objects。
### 3. 菜单/工具栏插件

添加自定义菜单项和工具栏按钮。

#### 完整示例

```python
from core.VitaLoom.kernel.plugin_interfaces import IMenuProvider
from typing import Dict, Any, List

class MyMenuPlugin(IMenuProvider):
    """菜单/工具栏插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyMenu",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "自定义菜单和工具栏",
            "dependencies": [],
            "provides": ["menu"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """返回菜单项列表"""
        return [
            {
                "path": "Tools/My Tool",  # 菜单路径
                "action": self.my_action,  # 回调函数
                "shortcut": "Ctrl+M"      # 快捷键（可选）
            },
            {
                "path": "Edit/Custom Action",
                "action": self.custom_action
            }
        ]
    
    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """返回工具栏项列表"""
        return [
            {
                "text": "My Tool",        # 按钮文本
                "action": self.my_action, # 回调函数
                "icon": None              # 图标路径（可选）
            }
        ]
    
    def my_action(self):
        print("My tool action triggered!")
    
    def custom_action(self):
        print("Custom action triggered!")
```

### 4. 主题插件

创建自定义 UI 主题。主题 profile 的可移植身份与配色由 Host 从 metadata 复制；QSS 仍是当前 Qt Adapter 的具体 payload。

#### 完整示例

```python
from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class MyThemePlugin(IRuntimePlugin):
    """主题插件：metadata 只包含 JSON-safe 的 profile 事实。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyThemePlugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "自定义主题",
            "dependencies": [],
            "provides": ["theme", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "my_theme.profile",
                    "kind": "theme_profile",
                    "theme_id": "my.theme",
                    "name_key": "theme.my_theme.name",
                    "default_name": "My Custom Theme",
                    "appearance": "dark",
                    "palette": {
                        "background": "#2D2D2D",
                        "text": "#FFFFFF",
                        "accent": "#0078D4",
                        "hover": "#005A9E",
                    },
                    "order": 100,
                }
            ],
        }

    def on_load(self, runtime_context) -> None:
        self.context = runtime_context

    def on_unload(self) -> None:
        self.context = None

    def get_theme_name(self) -> str:
        return "My Custom Theme"

    def get_stylesheet(self) -> str:
        """当前 LegacyEditorPluginAdapter 消费的具体 QSS payload seam。"""
        return """
        QMainWindow {
            background-color: #2D2D2D;
            color: #FFFFFF;
        }
        QDockWidget {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #0078D4;
            color: #FFFFFF;
            border: none;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #005A9E;
        }
        """
```

`theme_profile`、palette 与排序是由 Host 复制的 JSON-safe metadata：不要在其中放入 QSS 工厂、QWidget、Qt 对象、回调或 live state。`get_stylesheet()` 仅保留为 Adapter-local 的具体 PyQt payload seam。`IThemeProvider` 仍可作为历史兼容导入，但不再是新主题插件的作者模板。

### 5. 实体类型插件

提供自定义实体类型（如新的生物体类型）。

#### 完整示例

```python
from core.VitaLoom.kernel.plugin_interfaces import IEntityTypeProvider
from core.Lotucosm.entity import EntityBase
from typing import Dict, Any, List, Type

class MyEntityTypePlugin(IEntityTypeProvider):
    """实体类型插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyEntityTypes",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "自定义实体类型",
            "dependencies": [],
            "provides": ["entity_type"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_entity_types(self) -> List[Type]:
        """返回实体类型列表"""
        from my_entities import MyCustomEntity
        return [MyCustomEntity]
    
    def create_entity(self, entity_type: str, **kwargs):
        """创建实体实例"""
        if entity_type == "MyCustomEntity":
            from my_entities import MyCustomEntity
            return MyCustomEntity(**kwargs)
        return None
```

### 6. 组件类型插件

提供自定义组件类型（如新的传感器、执行器等）。

#### 完整示例

```python
from core.VitaLoom.kernel.plugin_interfaces import IComponentTypeProvider
from builtin.components.components_base import ComponentBase
from typing import Dict, Any, List, Type

class MyComponentTypePlugin(IComponentTypeProvider):
    """组件类型插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyComponents",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "自定义组件类型",
            "dependencies": [],
            "provides": ["component_type"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_component_types(self) -> List[Type]:
        """返回组件类型列表"""
        from my_components import MyCustomSensor, MyCustomActuator
        return [MyCustomSensor, MyCustomActuator]
    
    def create_component(self, component_type: str, **kwargs):
        """创建组件实例"""
        if component_type == "MyCustomSensor":
            from my_components import MyCustomSensor
            return MyCustomSensor(**kwargs)
        elif component_type == "MyCustomActuator":
            from my_components import MyCustomActuator
            return MyCustomActuator(**kwargs)
        return None
```

### 插件间通信

插件之间通过**事件总线**进行通信，避免直接依赖。

#### 发布事件

```python
def on_load(self, editor_context):
    self.context = editor_context
    # 发布事件
    self.context.event_bus.publish("my_event", {
        "data": "hello",
        "timestamp": time.time()
    })
```

#### 订阅事件

```python
def on_load(self, editor_context):
    self.context = editor_context
    # 订阅事件
    self.context.event_bus.subscribe("my_event", self.on_my_event)

def on_my_event(self, data):
    print(f"Received event: {data}")

def on_unload(self):
    # 记得取消订阅
    self.context.event_bus.unsubscribe("my_event", self.on_my_event)
```

### 服务注册表（Service Registry）

对于“可复用能力”（例如下载器、统一格式解析器等），推荐通过 `EditorContext.services` 注册和获取，而不是插件间直接 import。

#### 提供服务（Provider）

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

#### 使用服务（Consumer）

```python
def on_editor_ready(self):
    svc = self.context.services.get("my.service")
    if svc:
        print(svc.ping())
```

建议消费者插件增加“最小版本检查”（例如 `required >= 1.0.0`），并在不兼容时给出清晰日志告警。

示例插件：
- `workspace/extensions/community/example_service_provider/service_provider_plugin.py`
- `workspace/extensions/community/example_service_consumer/service_consumer_plugin.py`

### 插件开发流程

#### 1. 创建插件目录

```
workspace/extensions/user/
└── my_plugin/
    ├── __init__.py
    └── my_plugin_plugin.py
```

#### 2. 实现插件类

在 `my_plugin_plugin.py` 中实现插件类，继承相应的接口。

#### 3. 文件命名规则

**重要**：插件文件必须以 `_plugin.py` 结尾，插件加载器会自动扫描这些文件。

例如：
- ✅ `my_plugin_plugin.py` - 正确
- ✅ `custom_dock_plugin.py` - 正确
- ❌ `my_plugin.py` - 错误（不会被加载）

#### 4. 测试插件

1. 将插件安装/绑定到当前项目；本地开发扫描可设置 `VITALOOM_ENABLE_WORKSPACE_EXTENSIONS=1`
2. 启动或重启编辑器
3. 在 **Tools > 插件管理器** 中查看插件状态

### 插件管理

菜单：**Tools > 插件管理器**（实现类 `PackageManagerPlugin`）

插件管理器统一提供：

- **扩展包**：逻辑扩展包（`vitalloom.*`）= 一组编辑器插件 + 元数据（版本、来源、依赖）；清单来自产品版本 runtime 内的 `runtime/builtin/package_index.json`，可通过 `workspace/state/system/package_registries.json` 扩展来源。
- **运行时插件**：查看已加载插件、重载（开发中，多数情况需重启）、卸载、项目级启用/禁用。

常用操作：

- **项目禁用（立即生效）**：写入 `project.json.disabled_plugins`，并立即卸载对应插件。
- **项目启用**：从 `disabled_plugins` 移除；为保持启动顺序与 UI 注入稳定，建议重启编辑器。
- **对齐依赖**：打开工程缺包时，可在插件管理器中自动对齐 `required_packages`。

冷启动仅激活 `vitalloom.editor_essentials` 内插件；`workspace/extensions/user` 与 `workspace/extensions/community` 只是插件源、缓存或开发区，不会默认全局启用。打开工程后按当前项目的 manifest、lock 与项目插件命令同步激活集（见 [docs/compatibility_and_versions.md](../compatibility_and_versions.md)）。

注意：Lotucosm + VitaLoom 宿主（`vitalloom.core.platform`）不可卸载；插件管理器管的是可选扩展与编辑器插件实例。

#### 插件依赖

在 `get_plugin_info()` 中声明依赖：

```python
def get_plugin_info(self) -> Dict[str, Any]:
    return {
        "name": "MyPlugin",
        "dependencies": ["StandardUIPlugin", "UnityDarkThemePlugin"],
        "provides": ["dock"]
    }
```

插件加载器会自动解析依赖顺序，确保依赖插件先加载。`name` 须与 `package_index.json` 的 `plugins[]` 一致（含 `Plugin` 后缀）。

### 最佳实践

1. **资源清理** - 在 `on_unload()` 中清理所有资源
2. **错误处理** - 捕获异常，避免影响其他插件
3. **事件订阅** - 记得在卸载时取消所有事件订阅
4. **依赖声明** - 在 `get_plugin_info()` 中声明插件依赖
5. **模块化设计** - 保持插件功能单一、独立
6. **文档注释** - 为插件添加清晰的文档字符串

---

## 🧬 实体类型开发

实体类型是场景中的对象，如生物体、食物、障碍物等。

### 创建实体类型

#### 1. 继承 EntityBase

```python
from core.Lotucosm.entity import EntityBase
from typing import Tuple

class MyCustomEntity(EntityBase):
    """自定义实体类型"""
    
    def __init__(self, entity_id: str, position: Tuple[float, float], **kwargs):
        super().__init__(entity_id=entity_id, position=position, **kwargs)
        
        # 自定义属性
        self.custom_property = kwargs.get('custom_property', 0)
    
    def update(self, delta_time: float = 1.0):
        """更新实体逻辑"""
        super().update(delta_time)
        # 自定义更新逻辑
        pass
```

#### 2. 注册为实体类型插件

```python
from core.VitaLoom.kernel.plugin_interfaces import IEntityTypeProvider
from typing import List, Type

class MyEntityPlugin(IEntityTypeProvider):
    def get_entity_types(self) -> List[Type]:
        return [MyCustomEntity]
    
    def create_entity(self, entity_type: str, **kwargs):
        if entity_type == "MyCustomEntity":
            return MyCustomEntity(**kwargs)
        return None
```

### 实体类型示例

参考产品版本 runtime 内 `builtin/entity_types/` 目录下的示例：
- `organism.py` - 生物体基类
- `intelligent_organism.py` - 智能生物体
- `simple_organism.py` - 简单生物体

---

## 🧩 组件类型开发

组件是生物体的功能模块，如传感器、执行器等。

### 创建组件类型

#### 1. 继承 ComponentBase

```python
from builtin.components.components_base import ComponentBase
from typing import Tuple

class MyCustomSensor(ComponentBase):
    """自定义传感器组件"""
    
    def __init__(self, component_id: str, organism_id: str, 
                 position: Tuple[float, float], **kwargs):
        super().__init__(
            component_id=component_id,
            organism_id=organism_id,
            position=position,
            component_type="sensor",
            **kwargs
        )
        
        # 传感器特有属性
        self.sensitivity = kwargs.get('sensitivity', 1.0)
        self.range = kwargs.get('range', 100.0)
    
    def sense(self):
        """感知环境"""
        # 实现感知逻辑
        return 0.0
    
    def process_signal(self, signal: float):
        """处理信号"""
        # 实现信号处理逻辑
        pass
```

#### 2. 注册为组件类型插件

```python
from core.VitaLoom.kernel.plugin_interfaces import IComponentTypeProvider
from typing import List, Type

class MyComponentPlugin(IComponentTypeProvider):
    def get_component_types(self) -> List[Type]:
        return [MyCustomSensor]
    
    def create_component(self, component_type: str, **kwargs):
        if component_type == "MyCustomSensor":
            return MyCustomSensor(**kwargs)
        return None
```

### 组件类型示例

参考产品版本 runtime 内 `builtin/components/` 目录下的示例：
- `sensors.py` - 传感器组件
- `actuators.py` - 执行器组件
- `hybrid.py` - 复合器组件

---

## 📚 API 参考

### EditorContext API

编辑器上下文提供全局状态和功能访问。

```python
# 获取编辑器上下文
context = editor_context

# 访问内核
kernel = context.kernel

# 访问事件总线
event_bus = context.event_bus

# 访问布局管理器
layout_manager = kernel.layout_manager

# 访问插件加载器
plugin_loader = kernel.plugin_loader
```

### EventBus API

事件总线用于插件间通信。

```python
# 发布事件
event_bus.publish("event_name", {"data": "value"})

# 订阅事件
event_bus.subscribe("event_name", callback_function)

# 取消订阅
event_bus.unsubscribe("event_name", callback_function)
```

### LayoutManager API

布局管理器管理 UI 布局。

```python
# 添加 Dock 面板
layout_manager.add_dock(dock_widget, config)

# 添加视口
layout_manager.add_viewport(viewport_id, viewport_widget, provider)

# 添加菜单项
layout_manager.add_menu_items(menu_items)

# 添加工具栏项
layout_manager.add_toolbar_items(toolbar_items)
```

---

## 💡 示例项目

### 示例插件

项目包含四个示例插件，位于 `workspace/extensions/community/` 插件源：

1. **example_service_provider** - 可 Headless 导入的服务提供者
2. **example_service_consumer** - 可 Headless 导入的服务消费者
3. **example_custom_dock** - 显式依赖 PyQt6 的 Dock 面板示例
4. **example_custom_viewport** - 显式依赖 PyQt6 的视口示例

这些示例展示了：
- 如何创建插件
- 如何实现接口
- 如何使用事件总线
- 插件间如何通信

### 查看示例

```bash
# 查看 Dock 面板示例
cat workspace/extensions/community/example_custom_dock/custom_dock_plugin.py

# 查看视口示例
cat workspace/extensions/community/example_custom_viewport/custom_viewport_plugin.py
```

### 运行示例

1. 将示例插件安装/绑定到目标项目；本地开发扫描可设置 `VITALOOM_ENABLE_WORKSPACE_EXTENSIONS=1`
2. 启动编辑器：`python main.py`
3. 在界面中查看已激活的示例插件效果

---

## ❓ 常见问题

### 插件相关

**Q: 我的插件没有被加载？**

A: 检查以下几点：
1. 文件名是否以 `_plugin.py` 结尾
2. 类是否继承了正确的接口
3. 是否实现了所有必需的方法
4. 查看控制台是否有错误信息

**Q: 如何访问其他插件的功能？**

A: 使用事件总线进行通信，避免直接引用其他插件：

```python
# 发布事件
self.context.event_bus.publish("my_event", data)

# 订阅事件
self.context.event_bus.subscribe("my_event", callback)
```

**Q: 插件加载顺序如何控制？**

A: 在 `get_plugin_info()` 中声明 `dependencies`：

```python
def get_plugin_info(self):
    return {
        "dependencies": ["PluginA", "PluginB"]  # 依赖的插件
    }
```

插件加载器会自动解析依赖顺序。

**Q: 如何卸载插件？**

A: 在 **插件管理器** 中选择插件，点击 **卸载** 即可（当前会话生效）。

如果你希望“对某个项目永久禁用”，请使用 **🚫 项目禁用**（写入 `project.json.disabled_plugins`），打开该项目会自动应用。

### 开发相关

**Q: 如何调试插件？**

A: 
1. 使用 `print()` 输出调试信息到控制台
2. 查看 `logs/vitaloom_*.log` 文件
3. 使用事件总线发布调试事件
4. 在 **插件管理器** 中查看插件详情

**Q: 插件可以访问文件系统吗？**

A: 可以，但建议使用项目相关的路径：

```python
# 获取项目路径
project_path = self.context.current_project_path

# 访问项目资源
resource_path = os.path.join(project_path, "assets", "my_resource.png")
```

**Q: 如何创建自定义主题？**

A: 直接实现 `IRuntimePlugin`，在 `editor_contributions` 中声明 `theme_profile`，再参考主题插件示例提供 Adapter-local 的 QSS payload。

### 使用相关

**Q: 如何创建新项目？**

A: 菜单：**File > New Project**

**Q: 如何保存场景？**

A: 菜单：**File > Save Scene** 或快捷键 `Ctrl + S`

**Q: 如何运行模拟？**

A: 点击工具栏的 **▶ Play** 按钮，然后切换到 Game Viewport。

**Q: 如何编辑生物体？**

A: 
1. 在 Hierarchy 中选择生物体
2. 在 Inspector 中编辑属性
3. 双击生物体进入 Cell Editor 编辑内部结构

---

## 📖 进一步学习

### 推荐阅读顺序

1. [START_HERE.md](../../START_HERE.md) - 快速开始
2. [USER_GUIDE.md](USER_GUIDE.md) - 本指南（你正在阅读）
3. [PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md) - 插件开发详细指南
4. [docs/suite_architecture.md](../suite_architecture.md) / [docs/architecture.md](../architecture.md) - 架构说明
5. [README.md](../../README.md) - 项目总体介绍

### 代码示例

- `workspace/extensions/community/example_service_provider/` - Headless 服务提供者示例
- `workspace/extensions/community/example_service_consumer/` - Headless 服务消费者示例
- `workspace/extensions/community/example_custom_dock/` - PyQt6 Dock 面板示例
- `workspace/extensions/community/example_custom_viewport/` - PyQt6 视口示例
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/editor_extensions/` - 内置插件参考

### 获取帮助

- 查看项目文档
- 查看示例代码
- 在 GitHub Issues 中提问
- 参与项目讨论

---

## 🎉 开始开发

现在你已经了解了 VitaLoom Engine 的基本使用方法，可以开始：

1. **创建你的第一个插件** - 参考示例插件
2. **开发自定义实体类型** - 扩展生命体类型
3. **开发自定义组件** - 创建新的传感器或执行器
4. **分享你的作品** - 与其他开发者分享

祝你开发愉快！🚀

---

**VitaLoom Engine v1.0.0**  
高度模块化的生命模拟引擎平台

**最后更新**: 2026-01-31




