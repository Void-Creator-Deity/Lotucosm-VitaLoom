# VitaLoom Engine 深度使用指南

> **安装与 5 分钟上手**请读 [README_QUICK_START.md](README_QUICK_START.md)。  
> **文档总索引**：[docs/INDEX.md](docs/INDEX.md)

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

VitaLoom Engine 采用**极致模块化**架构，除了核心框架外，所有功能都以插件形式实现。你可以创建自己的插件来扩展编辑器功能。

### 插件类型

VitaLoom Engine 支持以下 7 种插件接口：

1. **IDockProvider** - Dock 面板插件
2. **IViewportProvider** - 视口插件
3. **IMenuProvider** - 菜单/工具栏插件
4. **IThemeProvider** - 主题插件
5. **IEntityTypeProvider** - 实体类型插件
6. **IComponentTypeProvider** - 组件类型插件
7. **基础插件** - 其他功能插件

### 插件基础结构

所有插件必须实现 `IEditorPlugin` 接口：

```python
from core.plugin.interfaces import IEditorPlugin
from typing import Dict, Any

class MyPlugin(IEditorPlugin):
    def get_plugin_info(self) -> Dict[str, Any]:
        """返回插件信息"""
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "插件描述",
            "dependencies": [],  # 依赖的其他插件
            "provides": []       # 提供的接口类型
        }
    
    def on_load(self, editor_context):
        """插件加载时调用"""
        self.context = editor_context
        # 初始化代码
    
    def on_unload(self):
        """插件卸载时调用 - 必须清理所有资源"""
        # 清理代码
        pass
    
    def on_editor_ready(self):
        """编辑器完全初始化后调用（可选）"""
        pass
```

### 1. Dock 面板插件

Dock 面板是可以在编辑器边缘停靠的面板，如 Hierarchy、Inspector 等。

#### 完整示例

```python
from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Dict, Any

class MyDockPlugin(IDockProvider):
    """自定义 Dock 面板插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyDock",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "一个自定义的 Dock 面板",
            "dependencies": [],
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.dock = None
    
    def on_unload(self):
        if self.dock:
            self.dock.deleteLater()
    
    def create_dock_widget(self) -> QDockWidget:
        """创建 Dock 窗口"""
        self.dock = QDockWidget("My Panel")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # 添加你的 UI 组件
        label = QLabel("Hello from My Dock!")
        layout.addWidget(label)
        
        button = QPushButton("Click Me")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        self.dock.setWidget(widget)
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        """返回 Dock 配置"""
        return {
            "title": "My Panel",
            "area": Qt.DockWidgetArea.RightDockWidgetArea,  # 停靠位置
            "default_visible": True,  # 默认是否可见
            "can_close": True         # 是否允许关闭
        }
    
    def on_button_clicked(self):
        print("Button clicked!")
```

#### Dock 配置说明

- **area**: 停靠位置
  - `Qt.DockWidgetArea.LeftDockWidgetArea` - 左侧
  - `Qt.DockWidgetArea.RightDockWidgetArea` - 右侧
  - `Qt.DockWidgetArea.TopDockWidgetArea` - 顶部
  - `Qt.DockWidgetArea.BottomDockWidgetArea` - 底部

### 2. 视口插件

视口是编辑器中央的主要工作区域，如 Scene、Game、Cell Editor 等。

#### 完整示例

```python
from core.plugin.interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from typing import Dict, Any

class MyViewportPlugin(IViewportProvider):
    """自定义视口插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyViewport",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "一个自定义的视口",
            "dependencies": [],
            "provides": ["viewport"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.viewport = None
    
    def on_unload(self):
        if self.viewport:
            self.viewport.deleteLater()
    
    def create_viewport_widget(self) -> QWidget:
        """创建视口部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("My Custom Viewport")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.viewport = widget
        return widget
    
    def get_viewport_id(self) -> str:
        """返回视口 ID（唯一标识）"""
        return "my_viewport"
    
    def get_viewport_name(self) -> str:
        """返回视口显示名称"""
        return "My Viewport"
    
    def on_viewport_activated(self):
        """视口被激活时调用"""
        print("My viewport activated")
    
    def on_viewport_deactivated(self):
        """视口被停用时调用"""
        print("My viewport deactivated")
```

### 3. 菜单/工具栏插件

添加自定义菜单项和工具栏按钮。

#### 完整示例

```python
from core.plugin.interfaces import IMenuProvider
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

创建自定义 UI 主题。

#### 完整示例

```python
from core.plugin.interfaces import IThemeProvider
from typing import Dict, Any

class MyThemePlugin(IThemeProvider):
    """主题插件"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyTheme",
            "version": "1.0.0",
            "author": "Your Name",
            "description": "自定义主题",
            "dependencies": [],
            "provides": ["theme"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def get_theme_name(self) -> str:
        return "My Custom Theme"
    
    def get_stylesheet(self) -> str:
        """返回 QSS 样式表"""
        return """
        QMainWindow {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        QDockWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #005a9e;
        }
        """
    
    def get_color_scheme(self) -> Dict[str, str]:
        """返回颜色方案"""
        return {
            "background": "#2d2d2d",
            "text": "#ffffff",
            "accent": "#0078d4",
            "hover": "#005a9e"
        }
```

### 5. 实体类型插件

提供自定义实体类型（如新的生物体类型）。

#### 完整示例

```python
from core.plugin.interfaces import IEntityTypeProvider
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
from core.plugin.interfaces import IComponentTypeProvider
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
- `plugins/example_service_provider/service_provider_plugin.py`
- `plugins/example_service_consumer/service_consumer_plugin.py`

### 插件开发流程

#### 1. 创建插件目录

```
plugins/
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

1. 重启编辑器
2. 插件会自动加载
3. 在 **Tools > Plugin Manager** 中查看插件状态

### 插件管理

#### 查看已加载插件

菜单：**Tools > Plugin Manager**

在插件管理器中可以：
- 查看所有已加载的插件
- 查看插件详细信息
- 重载插件（开发时）
- 卸载插件（实验性）

#### 插件依赖

在 `get_plugin_info()` 中声明依赖：

```python
def get_plugin_info(self) -> Dict[str, Any]:
    return {
        "name": "MyPlugin",
        "dependencies": ["StandardUI", "UnityDarkTheme"],  # 依赖的插件
        "provides": ["dock"]
    }
```

插件加载器会自动解析依赖顺序，确保依赖插件先加载。

#### 包管理（Package Manager）

除了逐个插件管理外，编辑器还提供 **Unity 风格的包管理器**：包 = 一组插件 + 元数据（版本、来源、依赖等）。

菜单：**Tools > Package Manager**

- **项目禁用（立即生效）**：会写入 `project.json.disabled_plugins`，并立即卸载该包内已加载的插件。
- **项目启用（稳定起见需要重启）**：会从 `disabled_plugins` 移除，但为了保持启动顺序与 UI 注入稳定，重新加载建议重启编辑器。

包清单来源支持：
- **本地清单**：`builtin/package_index.json`
- **Registry 配置**：`data/system/package_registries.json`（可配置 file/url 源，失败会被忽略并提示）

注意：Kernel/Framework 仍保持最小内核职责不变；包管理器属于官方插件层（Official Mods）。

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
from core.plugin.interfaces import IEntityTypeProvider
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

参考 `builtin/entity_types/` 目录下的示例：
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
from core.plugin.interfaces import IComponentTypeProvider
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

参考 `builtin/components/` 目录下的示例：
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

项目包含两个示例插件，位于 `plugins/` 目录：

1. **example_custom_dock** - 自定义 Dock 面板示例
2. **example_custom_viewport** - 自定义视口示例

这些示例展示了：
- 如何创建插件
- 如何实现接口
- 如何使用事件总线
- 插件间如何通信

### 查看示例

```bash
# 查看 Dock 面板示例
cat plugins/example_custom_dock/custom_dock_plugin.py

# 查看视口示例
cat plugins/example_custom_viewport/custom_viewport_plugin.py
```

### 运行示例

1. 启动编辑器：`python main.py`
2. 插件会自动加载
3. 在界面中查看示例插件效果

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

A: 在 Plugin Manager 中选择插件，点击 **🗑️ 卸载** 按钮即可（当前会话生效）。

如果你希望“对某个项目永久禁用”，请使用 **🚫 项目禁用**（写入 `project.json.disabled_plugins`），打开该项目会自动应用。

### 开发相关

**Q: 如何调试插件？**

A: 
1. 使用 `print()` 输出调试信息到控制台
2. 查看 `logs/vitaloom_*.log` 文件
3. 使用事件总线发布调试事件
4. 在 Plugin Manager 中查看插件详情

**Q: 插件可以访问文件系统吗？**

A: 可以，但建议使用项目相关的路径：

```python
# 获取项目路径
project_path = self.context.current_project_path

# 访问项目资源
resource_path = os.path.join(project_path, "assets", "my_resource.png")
```

**Q: 如何创建自定义主题？**

A: 实现 `IThemeProvider` 接口，参考主题插件示例。

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

1. **START_HERE.md** - 快速开始
2. **USER_GUIDE.md** - 本指南（你正在阅读）
3. **PLUGIN_DEVELOPMENT_GUIDE.md** - 插件开发详细指南
4. **ARCHITECTURE_DIAGRAM.txt** - 架构说明
5. **README.md** - 项目总体介绍

### 代码示例

- `plugins/example_custom_dock/` - Dock 面板示例
- `plugins/example_custom_viewport/` - 视口示例
- `builtin/editor_extensions/` - 内置插件参考

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
