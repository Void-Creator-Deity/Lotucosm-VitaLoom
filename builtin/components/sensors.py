"""PS 传感器：触觉/光感标量输出（非 SR chemo 通道）。

架构数据流（PS）::

    PVAECOrchestrator._perception_phase → component.sense(environment) → output_signal

SR 边界::

    SR 膜受体由 `sensor_patrol_pvaec` 等脚本写 `sr_channel_out`；**不**用本模块直连最近食物坐标。
    趋食梯度见 `scene_runtime_ambient.nutrient_gradient_at` 与 `sr_membrane_topology`。

排错: 见 `builtin/README.md`（传感器无输出 / SR 与 PS 混谈）。
"""
from typing import Optional, Tuple, Any, Dict
import numpy as np
from builtin.components.components_base import ComponentBase


class TouchSensor(ComponentBase):
    """PS 触觉传感器：邻近实体距离反比聚合为 `sensed_value`。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """TouchSensor.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault('component_type', 'touch_sensor')
        super().__init__(component_id=component_id, **kwargs)
        self.sensed_value = 0.0
        self.register_property('signal_threshold', kwargs.get('signal_threshold', 0.5), float, min=0.0, max=1.0, step=0.1)
        self.register_property('sensing_range', kwargs.get('sensing_range', 50.0), float, min=0.0, max=200.0)

    def process_signal(self, signal: float) -> Optional[float]:
        """处理输入信号。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 传感器不处理输入信号，只感知环境
        return None

    def sense(self, environment: Any) -> float:
        """查询邻近实体并写入 `sensed_value`（PS；非 SR chemo/GPS）。

        职责: 调用 `environment.get_nearby_entities`，按距离反比聚合为标量输出。
        时机: `PVAECOrchestrator._perception_phase` 或 Organism update 链。
        不变量: 环境须实现 `get_nearby_entities`；**不**输出最近食物世界坐标。
        排错: 恒为 0 → 查 sensing_range 与 Environment；SR 趋食勿查本类（见 README）。
        """
        # 检查附近是否有其他实体
        nearby = environment.get_nearby_entities(self.world_position, self.sensing_range)
        
        # 计算接触强度
        contact_strength = 0.0
        for entity in nearby:
            distance = np.linalg.norm(entity.position - self.world_position)
            if distance < self.sensing_range:
                contact_strength += 1.0 / (distance + 1.0)
        
        self.sensed_value = contact_strength
        self.output_signal = contact_strength
        
        # 更新状态
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"
        
        return self.sensed_value

    def get_status(self) -> Dict[str, Any]:
        """获取传感器状态。

        
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
            'sensed_value': self.sensed_value,
            'signal_threshold': self.signal_threshold,
            'sensing_range': self.sensing_range
        })
        return status


class LightSensor(ComponentBase):
    """PS 光感传感器：读取环境光照标量，无全局食物坐标。"""

    def __init__(self, component_id: Optional[str] = None, **kwargs):
        """LightSensor.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        kwargs.setdefault('component_type', 'light_sensor')
        super().__init__(component_id=component_id, **kwargs)
        self.sensed_value = 0.0
        self.register_property('signal_threshold', kwargs.get('signal_threshold', 0.3), float, min=0.0, max=1.0, step=0.1)
        self.register_property('sensing_range', kwargs.get('sensing_range', 100.0), float, min=0.0, max=500.0)

    def process_signal(self, signal: float) -> Optional[float]:
        """处理输入信号。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 传感器不处理输入信号，只感知环境
        return None

    def sense(self, environment: Any) -> float:
        """读取 `get_light_intensity` 标量（PS；非 SR 营养梯度）。

        职责: 以 `world_position` 查询环境光照强度，写入 `sensed_value`/`output_signal`。
        时机: PS 感知阶段；SR 光/营养感知由场景脚本与 `nutrient_gradient_at` 承担。
        不变量: 仅标量强度，无全局食物向量；阈值由 `signal_threshold` 决定 active/idle。
        排错: 恒为 0 → 查 Environment 光照实现；勿与 SR chemo 通道混淆。
        """
        # 获取光照强度
        light_intensity = environment.get_light_intensity(self.world_position)
        self.sensed_value = light_intensity
        self.output_signal = light_intensity
        
        # 更新状态
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"
        
        return self.sensed_value

    def get_status(self) -> Dict[str, Any]:
        """获取传感器状态。

        
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
            'sensed_value': self.sensed_value,
            'signal_threshold': self.signal_threshold,
            'sensing_range': self.sensing_range
        })
        return status


# 兼容别名：旧代码使用 Sensor / ProximitySensor
Sensor = TouchSensor
ProximitySensor = TouchSensor
