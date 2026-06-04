"""PS PVAEC 认知引擎组件：传感器–执行器关联学习（体内闭环，非 SR 中枢脚本）。

架构数据流::

    感知 dict → associations 查表 → 探索/利用控制各 actuator 输入

排错: 序列化 associations 见 `PondSerializer.serialize_component`；SR 中枢见 `sr_central_brain_pvaec`。
"""

from __future__ import annotations

import random
from typing import Optional, Any, Dict

from builtin.components.components_base import ComponentBase


class PVAECEngine(ComponentBase):
    """PS 体内认知引擎：关联表 + 探索/利用；非 SR CentralBrainPvaec 脚本。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs: Any):
        """PVAECEngine.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault("component_type", "pvaec_engine")
        super().__init__(component_id=component_id, **kwargs)
        self.is_pvaec_engine = True
        assoc = kwargs.get("associations")
        if isinstance(assoc, dict):
            self.associations: Dict[str, Dict[str, float]] = {
                str(sk): {str(ak): float(av) for ak, av in (sv or {}).items()}
                for sk, sv in assoc.items()
            }
        else:
            self.associations = {}
        self.learning_rate = float(kwargs.get("learning_rate", 0.05))
        self.exploration_rate = float(kwargs.get("exploration_rate", 0.1))
        self.success_threshold = float(kwargs.get("success_threshold", 0.5))
        self.register_property("learning_rate", self.learning_rate, float, min=0.0, max=1.0, step=0.01)
        self.register_property("exploration_rate", self.exploration_rate, float, min=0.0, max=1.0, step=0.01)
        self.register_property("success_threshold", self.success_threshold, float, min=0.0, max=1.0, step=0.01)

    def learn_association(self, sensor_id: str, actuator_id: str, success: bool) -> None:
        """PVAECEngine.learn_association。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5
        cur = self.associations[sensor_id][actuator_id]
        if success:
            self.associations[sensor_id][actuator_id] = min(1.0, cur + self.learning_rate)
        else:
            self.associations[sensor_id][actuator_id] = max(0.0, cur - self.learning_rate * 0.5)

    def generate_control_signals(self, sensor_values: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """PVAECEngine.generate_control_signals。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        control_signals: Dict[str, float] = {}
        sensor_values = sensor_values or {}
        for sensor_id, value in sensor_values.items():
            if sensor_id not in self.associations:
                continue
            for actuator_id, strength in self.associations[sensor_id].items():
                control_signals[actuator_id] = control_signals.get(actuator_id, 0.0) + float(value) * float(strength)
        if random.random() < self.exploration_rate:
            for aid in list(control_signals.keys()):
                if random.random() < 0.5:
                    control_signals[aid] = control_signals.get(aid, 0.0) + random.uniform(-0.5, 0.5)
        for aid in list(control_signals.keys()):
            control_signals[aid] = max(-1.0, min(1.0, control_signals[aid]))
        return control_signals

    def process(self, input_value: float) -> float:
        """旧版 API：与 process_signal 等价。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.process_signal(input_value)

    def process_signal(self, signal: float) -> float:
        """PVAECEngine.process_signal。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.output_signal = float(signal) * 0.8
        return self.output_signal

    def update(self, delta_time: float = 1.0) -> None:
        """PVAECEngine.update。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().update(delta_time)

    def get_status(self) -> Dict[str, Any]:
        """PVAECEngine.get_status。

        
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
        n_assoc = sum(len(v) for v in self.associations.values())
        status.update(
            {
                "learning_rate": self.learning_rate,
                "exploration_rate": self.exploration_rate,
                "success_threshold": self.success_threshold,
                "association_count": n_assoc,
            }
        )
        return status
