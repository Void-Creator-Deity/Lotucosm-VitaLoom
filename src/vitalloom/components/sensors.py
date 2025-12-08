"""传感器实现"""

from typing import Dict, Any
from .components_base import ComponentBase

class Sensor(ComponentBase):
    """传感器基类

    所有传感器的基类，提供传感器的基本功能和属性
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化传感器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 传感器特有属性
        self.sense_range = kwargs.get('sense_range', 50)  # 感知范围
        self.sensed_value = 0.0  # 感知值
        self.sense_time = 0  # 上次感知时间
        self.sense_interval = kwargs.get('sense_interval', 50)  # 感知间隔（毫秒）
        self.is_sensor = True  # 标记为传感器
        self.sensor_type = kwargs.get('sensor_type', 'general')  # 传感器类型

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def sense(self, environment: Any, organism: Any = None) -> Dict[str, Any]:
        """感知环境，返回感知值

        参数:
            environment - 环境对象
            organism - 生物体实例（可选）

        返回:
            Dict[str, Any] - 感知结果
        """
        # 子类实现具体的感知逻辑
        return {
            'type': self.sensor_type,
            'value': 0.0,
            'range': self.sense_range
        }

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        return self.sensed_value

    def update(self):
        """每帧更新"""
        super().update()
        # 传感器特有更新逻辑
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"

class TouchSensor(Sensor):
    """触觉传感器 - 检测接触

    触觉传感器的实现，用于检测环境中的接触压力。
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化触觉传感器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 传感器特有属性
        self.sense_range = kwargs.get('sense_range', 15)  # 感知范围15
        self.sensed_value = 0.0  # 感知值
        self.sense_time = 0  # 上次感知时间
        self.sense_interval = kwargs.get('sense_interval', 50)  # 感知间隔（毫秒）

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def sense(self, environment: Any, organism: Any = None) -> Dict[str, Any]:
        """感知环境，返回感知值

        检测环境中的接触压力，并返回感知结果。

        参数:
            environment - 环境对象
            organism - 生物体实例

        返回:
            Dict[str, Any] - 感知结果
        """
        # 计算世界坐标
        world_pos = organism.position + self.position

        # 检查接触
        contact_info = environment.check_contact(world_pos, self.sense_range)

        # 获取压力值
        self.sensed_value = contact_info.get("pressure", 0.0)

        # 返回感知结果
        return {
            'type': 'touch',
            'value': self.sensed_value,
            'range': self.sense_range,
            'contact': contact_info.get('contact', False)
        }

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        处理输入值并返回输出值，触觉传感器直接返回感知值。

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        return self.sensed_value  # 直接返回感知值

    def update(self):
        """每帧更新

        更新传感器状态，包括调用父类的更新方法和更新传感器特有状态。
        """
        super().update()
        # 传感器特有更新逻辑：根据感知值更新状态
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"

class LightSensor(ComponentBase):
    """光感传感器 - 检测光线

    光感传感器的实现，用于检测环境中的光线强度。
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化光感传感器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 传感器特有属性
        self.sense_range = kwargs.get('sense_range', 80)  # 感知范围80
        self.sensed_value = 0.0  # 感知值
        self.sense_time = 0  # 上次感知时间
        self.sense_interval = kwargs.get('sense_interval', 50)  # 感知间隔（毫秒）

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def sense(self, environment: Any, organism: Any = None) -> Dict[str, Any]:
        """感知环境，返回感知值

        检测环境中的光线强度，并返回感知结果。

        参数:
            environment - 环境对象
            organism - 生物体实例

        返回:
            Dict[str, Any] - 感知结果
        """
        # 计算世界坐标
        world_pos = organism.position + self.position

        # 获取光线强度
        light_level = environment.get_light_intensity(world_pos)

        # 保存感知值
        self.sensed_value = light_level

        # 返回感知结果
        return {
            'type': 'light',
            'value': self.sensed_value,
            'range': self.sense_range
        }

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        处理输入值并返回输出值，光感传感器直接返回感知值。

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        return self.sensed_value  # 直接返回感知值

    def update(self):
        """每帧更新

        更新传感器状态，包括调用父类的更新方法和更新传感器特有状态。
        """
        super().update()
        # 传感器特有更新逻辑：根据感知值更新状态
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"
