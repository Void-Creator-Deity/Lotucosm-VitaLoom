"""VitaLoom 编辑器插件契约：IEditorPlugin 及 Dock/视口/菜单/主题/实体/组件 Provider。

架构数据流::

    PluginLoader 发现插件类 → on_load(editor_context) → Provider 注册 UI
    on_unload 须释放 QWidget/Dock 引用

排错索引见 docs/lotucosm_core_troubleshooting.md（插件 Dock 未出现 → IDockProvider）。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type
from PyQt6.QtWidgets import QDockWidget, QWidget


class IEditorPlugin(ABC):
    """编辑器插件基类：元数据、加载/卸载与可选 on_editor_ready。

    生命周期:
        get_plugin_info → on_load → on_editor_ready → on_unload
    """
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """返回插件元数据 dict（name/version/dependencies/provides 等）。

        职责:
            供 PluginLoader 排序依赖与展示清单。

        时机:
            扫描插件包时首先调用。

        不变量:
            provides 声明能力类型（viewport/dock/menu 等）。

        排错:
            插件未加载 → dependencies 未满足或类未实现本接口。
        """
        pass
    
    @abstractmethod
    def on_load(self, editor_context):
        """插件加载：注册服务、订阅事件、创建 UI。

        职责:
            持有 editor_context 引用并挂载到内核。

        时机:
            EditorKernel 初始化插件阶段。

        不变量:
            须幂等或可检测重复加载；勿阻塞主线程过久。

        排错:
            加载后无 UI → 检查是否误写在 on_editor_ready 且未实现该方法。
        """
        pass
    
    @abstractmethod
    def on_unload(self):
        """卸载：释放 QWidget、断开信号、注销服务。

        职责:
            与 on_load 对称清理，避免悬挂引用。

        时机:
            编辑器关闭或热重载插件前。

        不变量:
            卸载后不得再访问已销毁的 editor_context 控件。

        排错:
            退出崩溃 → 查是否遗漏 deleteLater 或循环引用。
        """
        pass
    
    def on_editor_ready(self):
        """编辑器 UI 完全就绪后可选回调（默认空）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IDockProvider(IEditorPlugin):
    """Dock 面板提供者：create_dock_widget + get_dock_config。"""
    
    @abstractmethod
    def create_dock_widget(self) -> QDockWidget:
        """创建并返回 Dock 部件实例。

        职责:
            插件实现方构造并配置可嵌入主窗口的 QDockWidget。

        排错:
            Dock 空白 → 未在 on_load 中填充 widget 或 area 配置错误。
        """
        pass
    
    @abstractmethod
    def get_dock_config(self) -> Dict[str, Any]:
        """返回 title/area/default_visible/can_close 等布局配置。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IViewportProvider(IEditorPlugin):
    """视口提供者：scene/game/cell_editor 等自定义视口。"""
    
    @abstractmethod
    def create_viewport_widget(self) -> QWidget:
        """创建视口 QWidget。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def get_viewport_id(self) -> str:
        """返回视口唯一 ID（如 scene、game）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def get_viewport_name(self) -> str:
        """返回 UI 显示名称。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    def on_viewport_activated(self):
        """视口被选中/激活时调用。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    def on_viewport_deactivated(self):
        """视口失去焦点时调用。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IMenuProvider(IEditorPlugin):
    """菜单与工具栏项提供者。"""
    
    @abstractmethod
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """返回菜单项列表（path/action/shortcut/icon）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """返回工具栏按钮配置。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IThemeProvider(IEditorPlugin):
    """QSS 主题与颜色方案提供者。"""
    
    @abstractmethod
    def get_theme_name(self) -> str:
        """主题显示名。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def get_stylesheet(self) -> str:
        """完整 QSS 字符串。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def get_color_scheme(self) -> Dict[str, str]:
        """颜色 token 字典（供代码侧查询）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IEntityTypeProvider(IEditorPlugin):
    """向编辑器注册可创建的实体类型。"""
    
    @abstractmethod
    def get_entity_types(self) -> List[Type]:
        """返回实体类列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def create_entity(self, entity_type: str, **kwargs):
        """按类型名工厂创建实体实例。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass


class IComponentTypeProvider(IEditorPlugin):
    """向编辑器注册可创建的组件类型。"""
    
    @abstractmethod
    def get_component_types(self) -> List[Type]:
        """返回组件类列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
    
    @abstractmethod
    def create_component(self, component_type: str, **kwargs):
        """按类型名工厂创建组件实例。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        pass
