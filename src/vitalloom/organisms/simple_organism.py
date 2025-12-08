"""简单生物体实现"""

from .organism import Organism
from typing import Dict, Any, Tuple

class SimpleOrganism(Organism):
    """简单生物体 - 无PVAEC引擎的基本生物体

    简单生物体是最基础的生物体类型，没有复杂的PVAEC引擎，
    主要通过简单的反射机制和随机行为与环境交互。
    """

    def __init__(self, organism_id: str, position: Tuple[float, float], **kwargs: Any):
        """初始化简单生物体

        参数:
            organism_id: str - 生物体唯一标识符
            position: Tuple[float, float] - 初始位置
            kwargs: 其他参数
        """
        super().__init__(organism_id, position, **kwargs)

        # 简单生物体特有属性
        self.reflex_strength = float(kwargs.get('reflex_strength', 0.5))  # 反射强度
        self.random_behavior_probability = float(kwargs.get('random_behavior_probability', 0.3))  # 随机行为概率

    def update(self, environment: Any):
        """每帧更新生物体状态

        参数:
            environment - 环境实例
        """
        if self.dead:
            return

        # 调用父类更新
        super().update(environment)

        # 简单生物体的行为逻辑
        self.perform_simple_behavior(environment)

    def perform_simple_behavior(self, environment: Any):
        """执行简单行为

        参数:
            environment - 环境实例
        """
        import random

        # 随机行为
        if random.random() < self.random_behavior_probability:
            self.perform_random_action(environment)
        else:
            # 反射行为
            self.perform_reflex_action(environment)

    def perform_random_action(self, environment: Any):
        """执行随机行为

        参数:
            environment - 环境实例
        """
        import random

        # 随机选择一个执行器组件
        actuators = [comp for comp in self.components.values() if hasattr(comp, 'act')]
        if actuators:
            actuator = random.choice(actuators)
            # 生成随机动作
            action = {
                'value': random.uniform(-1.0, 1.0)
            }
            # 执行动作
            actuator.act(environment, self, action)

    def perform_reflex_action(self, environment: Any):
        """执行反射行为

        参数:
            environment - 环境实例
        """
        # 收集传感器数据
        sensor_data: Dict[str, Dict[str, Any]] = {}
        for component in self.components.values():
            if hasattr(component, 'sense'):
                sensor_result = component.sense(environment, self)
                sensor_data[component.id] = sensor_result

        # 简单的反射逻辑：如果有传感器数据，生成相应的动作
        for _, sensor_result in sensor_data.items():
            if 'value' in sensor_result and isinstance(sensor_result['value'], (int, float)) and abs(sensor_result['value']) > 0.1:
                # 查找关联的执行器（简单匹配）
                for actuator in self.components.values():
                    if hasattr(actuator, 'act'):
                        # 生成反射动作
                        action_dict: Dict[str, float] = {
                            'value': sensor_result['value'] * self.reflex_strength
                        }
                        # 执行动作
                        actuator.act(environment, self, action_dict)

    def get_status(self) -> Dict[str, Any]:
        """获取简单生物体状态

        返回:
            Dict[str, Any] - 状态信息
        """
        status = super().get_status()
        status.update({
            'type': 'simple_organism',
            'reflex_strength': self.reflex_strength,
            'random_behavior_probability': self.random_behavior_probability
        })
        return status
