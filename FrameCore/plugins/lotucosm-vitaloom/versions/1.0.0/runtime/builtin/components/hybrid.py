"""PS 混合组件：同一实体上切换 sensor/actuator 模式的轻量实现。

排错: 见 `builtin/README.md`。
"""

from typing import Optional, Any, Dict

from builtin.components.components_base import ComponentBase


class HybridComponent(ComponentBase):
    """PS 混合组件：mode 切换 sensor/actuator 信号转发。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """HybridComponent.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault("component_type", "hybrid_component")
        super().__init__(component_id=component_id, **kwargs)
        self.mode = kwargs.get("mode", "sensor")
        self.last_signal = 0.0
        self.register_property("mode", self.mode, str)

    def process_signal(self, signal: float):
        """HybridComponent.process_signal。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.last_signal = float(signal)
        self.output_signal = self.last_signal
        return self.last_signal

    def get_status(self) -> Dict[str, Any]:
        """HybridComponent.get_status。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        status = super().get_status()
        status.update(
            {
                "mode": self.mode,
                "last_signal": self.last_signal,
            }
        )
        return status
