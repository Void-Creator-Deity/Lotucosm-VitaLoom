"""PS 组件基类：继承 `core.Lotucosm.component.Component` 的 builtin 薄封装。

架构数据流::

    ComponentBase ← sensors / actuators / membrane / PVAECEngine

不变量: 与 core `Component` 的 connections、register_property 语义一致。

排错: 见 `builtin/README.md`；SR 膜脚本不经过本包。
"""

from typing import Optional, Dict, Any, Tuple
# 直接继承完整的 Component（而非 EntityBase），保证所有属性就绪
from core.Lotucosm.component import Component


class ComponentBase(Component):
    """PS 组件统一父类；生命周期随 Organism 加载/卸载与每帧 update。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs: Any):
        """初始化组件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # Component.__init__ 会调用 EntityBase.__init__，完整初始化所有字段
        super().__init__(component_id=component_id, **kwargs)

        # 位置/挂载扩展属性（Component 已有 location/acquired/congenital/attach_point，
        # 此处保留以防子类使用不同版本的 Component）
        if not hasattr(self, 'location'):
            self.location: str = kwargs.get('location', 'internal')
        if not hasattr(self, 'acquired'):
            self.acquired: bool = kwargs.get('acquired', False)
        if not hasattr(self, 'congenital'):
            self.congenital: bool = kwargs.get('congenital', True)
        if not hasattr(self, 'attach_point'):
            self.attach_point: Optional[str] = kwargs.get('attach_point', None)
