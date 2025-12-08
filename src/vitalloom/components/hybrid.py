from typing import Dict, Any
from .components_base import ComponentBase

class HybridComponent(ComponentBase):
    """
    复合器组件，兼具传感和执行功能
    例如：纤毛复合器 - 既能感知水流，又能产生推进力
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """
        初始化复合器组件

        参数:
        - component_id: 组件ID
        - organism_id: 所属生物体ID
        - kwargs: 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 复合器特有属性
        self.is_sensor = True
        self.is_actuator = True
        self.is_hybrid = True  # 标记为复合器
        self.sensor_sensitivity = kwargs.get('sensor_sensitivity', 1.0)
        self.actuator_strength = kwargs.get('actuator_strength', 1.0)
        self.mode = kwargs.get('mode', 'auto')  # 'sensor', 'actuator', 'auto'

        # 位置属性
        self.location = kwargs.get('location', 'both')  # 'internal', 'external', 'both'
        self.acquired = kwargs.get('acquired', False)
        self.congenital = kwargs.get('congenital', True)
        self.attach_point = kwargs.get('attach_point', None)

    def sense(self, environment: Any, organism: Any = None) -> Dict[str, Any]:
        """
        感知功能实现

        参数:
        - environment: 环境实例
        - organism: 生物体实例
        - action: 可选，动作指令

        返回:
        - Dict[str, Any]: 感知结果
        """
        result: Dict[str, Any] = {}
        if self.mode in ['sensor', 'auto']:
            # 实现传感逻辑
            result = {
                'type': self.type,
                'sensitivity': self.sensor_sensitivity,
                'value': 0.0
            }

            # 简单的感知模拟
            # 实际项目中需要根据具体复合器类型实现
            result['value'] = self._simulate_sensing(environment, organism)

        return result

    def act(self, environment: Any, organism: Any, action: Any = None) -> Dict[str, Any]:
        """
        执行功能实现

        参数:
        - environment: 环境实例
        - organism: 生物体实例
        - action: 行动指令

        返回:
        - Dict[str, Any]: 执行结果
        """
        result: Dict[str, Any] = {}
        if self.mode in ['actuator', 'auto']:
            # 实现执行逻辑
            result = {
                'type': self.type,
                'strength': self.actuator_strength,
                'success': False
            }

            # 简单的执行模拟
            # 实际项目中需要根据具体复合器类型实现
            result['success'] = self._simulate_action(environment, organism, action)

        return result

    def _simulate_sensing(self, environment: Any, organism: Any) -> float:
        """
        模拟感知功能

        参数:
        - environment: 环境实例
        - organism: 生物体实例

        返回:
        - float: 感知值
        """
        # 简单的感知模拟
        return 0.5  # 默认感知值

    def _simulate_action(self, environment: Any, organism: Any, action: Any) -> bool:
        """
        模拟执行功能

        参数:
        - environment: 环境实例
        - organism: 生物体实例
        - action: 行动指令

        返回:
        - bool: 执行是否成功
        """
        # 简单的执行模拟
        return True

    def switch_mode(self, mode: str) -> bool:
        """
        切换复合器模式

        参数:
        - mode: 新模式 ('sensor', 'actuator', 'auto')

        返回:
        - bool: 切换是否成功
        """
        if mode in ['sensor', 'actuator', 'auto']:
            self.mode = mode
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取复合器状态

        返回:
        - Dict[str, Any]: 复合器状态
        """
        status = super().get_status()
        status.update({
            'is_sensor': self.is_sensor,
            'is_actuator': self.is_actuator,
            'sensor_sensitivity': self.sensor_sensitivity,
            'actuator_strength': self.actuator_strength,
            'mode': self.mode
        })
        return status
