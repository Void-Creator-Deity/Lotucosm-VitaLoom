"""
平台内核 - 包含运行时引擎、编辑器框架、API和插件系统 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from .Lotucosm import EntityBase, Pond, Cosmos, get_cosmos, Component, System

# 编辑器框架 - 使用新的插件化架构
try:
    from .VitaLoom.kernel import EditorKernel
except Exception:
    EditorKernel = None
from .api import (
    expose_property,
    register_component,
    register_system,
    script_method,
    EventBus,
    get_event_bus,
    subscribe,
    unsubscribe,
    publish,
    EventType,
    ScriptRuntime,
    get_script_runtime,
    execute_script,
    execute_script_file
)
from .plugin import (
    IEditorPlugin,
    IDockProvider,
    IViewportProvider,
    IMenuProvider,
    IThemeProvider,
)

__all__ = [
    # 运行时引擎
    'EntityBase',
    'Pond',
    'Cosmos',
    'get_cosmos',
    'Component',
    'System',
    
    # 编辑器框架（新架构）
    'EditorKernel',
    
    # 扩展API
    'expose_property',
    'register_component',
    'register_system',
    'script_method',
    'EventBus',
    'get_event_bus',
    'subscribe',
    'unsubscribe',
    'publish',
    'EventType',
    'ScriptRuntime',
    'get_script_runtime',
    'execute_script',
    'execute_script_file',
    
    # 插件系统
    'IEditorPlugin',
    'IDockProvider',
    'IViewportProvider',
    'IMenuProvider',
    'IThemeProvider',
]
