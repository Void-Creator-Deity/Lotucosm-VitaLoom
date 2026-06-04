"""PS 执行器：肌肉/纤毛/繁殖等，接收传感器信号输出力或行为（非 SR 脚本执行器）。

架构数据流::

    sensor.output_signal → connections → actuator.process_signal → Organism 运动

排错: 见 `builtin/README.md`；SR 推力见 `actuator_pulse_pvaec` 与 GameViewport 耦合。
"""
from typing import Optional, Tuple, Any, Dict
import numpy as np
from builtin.components.components_base import ComponentBase


class MuscleActuator(ComponentBase):
    """PS 肌肉执行器：将输入信号转为定向力（非 SR 纤毛耦合）。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """MuscleActuator.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault('component_type', 'muscle_actuator')
        super().__init__(component_id=component_id, **kwargs)
        self.current_force = 0.0
        self.register_property('max_force', kwargs.get('max_force', 10.0), float, min=0.0, max=50.0)
        self.register_property('energy_cost', kwargs.get('energy_cost', 0.1), float, min=0.0, max=1.0, step=0.01)

    def process_signal(self, signal: float) -> Optional[float]:
        """处理输入信号，输出力向量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 将信号转换为力
        force = signal * self.max_force
        self.current_force = force
        return force

    def get_force_vector(self, direction: float) -> np.ndarray:
        """获取力向量。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        force_x = self.current_force * np.cos(direction)
        force_y = self.current_force * np.sin(direction)
        return np.array([force_x, force_y])

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态。

        
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
        status.update({
            'current_force': self.current_force,
            'max_force': self.max_force,
            'energy_cost': self.energy_cost
        })
        return status


class CiliaActuator(ComponentBase):
    """PS 纤毛执行器：扭矩输出；SR 同名效应器由脚本+拓扑边驱动。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """CiliaActuator.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault('component_type', 'cilia_actuator')
        super().__init__(component_id=component_id, **kwargs)
        self.current_torque = 0.0
        self.register_property('max_torque', kwargs.get('max_torque', 5.0), float, min=0.0, max=20.0)
        self.register_property('energy_cost', kwargs.get('energy_cost', 0.05), float, min=0.0, max=1.0, step=0.01)

    def process_signal(self, signal: float) -> Optional[float]:
        """处理输入信号，输出扭矩。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        torque = signal * self.max_torque
        self.current_torque = torque
        return torque

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态。

        
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
        status.update({
            'current_torque': self.current_torque,
            'max_torque': self.max_torque,
            'energy_cost': self.energy_cost
        })
        return status


class ReproductionActuator(ComponentBase):
    """PS 繁殖触发执行器：信号阈值触发 reproduce（非 SR 膜模板繁殖）。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """ReproductionActuator.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault('component_type', 'reproduction_actuator')
        super().__init__(component_id=component_id, **kwargs)
        self.register_property('reproduction_threshold', kwargs.get('reproduction_threshold', 0.8), float, min=0.0, max=1.0, step=0.05)
        self.register_property('energy_cost', kwargs.get('energy_cost', 0.5), float, min=0.0, max=5.0, step=0.1)
        self.can_reproduce = False

    def process_signal(self, signal: float) -> Optional[float]:
        """处理输入信号，判断是否可以繁殖。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.can_reproduce = signal >= self.reproduction_threshold
        return signal

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态。

        
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
        status.update({
            'reproduction_threshold': self.reproduction_threshold,
            'energy_cost': self.energy_cost,
            'can_reproduce': self.can_reproduce
        })
        return status


# 兼容别名：旧代码使用 Actuator / Motor / Flagellum
Actuator = MuscleActuator
Motor = MuscleActuator
Flagellum = CiliaActuator
