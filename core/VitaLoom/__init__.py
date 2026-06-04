"""VitaLoom 包：插件化 PyQt6 编辑器框架；入口 `kernel.EditorKernel`。排错见 README.md。"""

# 导出新的内核系统
from .kernel import EditorKernel, PluginLoader, EventBus, LayoutManager

__all__ = [
    'EditorKernel',       # 新的编辑器内核
    'PluginLoader',       # 插件加载器
    'EventBus',           # 事件总线
    'LayoutManager',      # 布局管理器
]
