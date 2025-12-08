"""智能生物体实现"""

from .organism import Organism
from vitalloom.core.pvaec_cycle import PVAECCycle
from vitalloom.components.components_base import ComponentBase
from typing import Dict, Any, Tuple

class IntelligentOrganism(Organism):
    """智能生物体 - 具有PVAEC引擎的复杂生物体

    智能生物体是具有复杂认知能力的生物体，能够通过PVAEC循环（感知-验证自主演化循环）
    不断学习和优化自身行为，实现智能的自主涌现。
    """

    def __init__(self, organism_id: str, position: Tuple[float, float], **kwargs: Any):
        """初始化智能生物体

        参数:
            organism_id: str - 生物体唯一标识符
            position: Tuple[float, float] - 初始位置
            kwargs: 其他参数
        """
        super().__init__(organism_id, position, **kwargs)

        # PVAEC循环实例
        self.pvaec_cycle = PVAECCycle()

        # 智能生物体特有属性
        self.learning_efficiency = float(kwargs.get('learning_efficiency', 1.0) if not isinstance(kwargs.get('learning_efficiency'), dict) else 1.0)  # 学习效率
        self.exploration_bias = float(kwargs.get('exploration_bias', 0.3) if not isinstance(kwargs.get('exploration_bias'), dict) else 0.3)  # 探索偏差
        self.pvaec_engine = None  # PVAEC引擎组件

        # 初始化时查找PVAEC引擎
        self.find_pvaec_engine()

    def find_pvaec_engine(self):
        """查找PVAEC引擎组件"""
        for component in self.components.values():
            if hasattr(component, 'generate_control_signals'):
                self.pvaec_engine = component
                break

    def update(self, environment: Any):
        """每帧更新生物体状态

        参数:
            environment - 环境实例
        """
        if self.dead:
            return

        # 调用父类更新
        super().update(environment)

        # 执行PVAEC循环
        self.run_pvaec_cycle(environment)

    def run_pvaec_cycle(self, environment: Any) -> bool:
        """运行PVAEC循环

        参数:
            environment - 环境实例

        返回:
            bool - 循环是否成功
        """
        # 执行完整的PVAEC循环
        return self.pvaec_cycle.run_cycle(self, environment)

    def add_component(self, component: ComponentBase) -> bool:
        """添加组件到生物体

        参数:
            component: ComponentBase - 组件实例

        返回:
            bool - 添加是否成功
        """
        success = super().add_component(component)

        # 检查是否添加了PVAEC引擎
        if success and hasattr(component, 'generate_control_signals'):
            self.pvaec_engine = component

        return success

    def remove_component(self, component_id: str) -> bool:
        """从生物体中移除组件

        参数:
            component_id: str - 组件ID

        返回:
            bool - 移除是否成功
        """
        # 检查是否要移除PVAEC引擎
        component = self.get_component(component_id)
        if component and hasattr(component, 'generate_control_signals'):
            self.pvaec_engine = None

        return super().remove_component(component_id)

    def perceive(self, environment: Any) -> Dict[str, Any]:
        """感知环境

        参数:
            environment - 环境实例

        返回:
            Dict[str, Any] - 感知结果
        """
        perception: Dict[str, Any] = {}

        # 收集所有传感器的感知结果
        for component in self.components.values():
            if hasattr(component, 'sense'):
                sensor_result = component.sense(environment, self)
                perception[component.id] = sensor_result

        return perception

    def generate_action(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """生成动作

        参数:
            perception: Dict[str, Any] - 感知结果

        返回:
            Dict[str, Any] - 动作指令
        """
        if self.pvaec_engine:
            # 使用PVAEC引擎生成控制信号
            sensor_values: Dict[str, float] = {}
            for sensor_id, sensor_result in perception.items():
                if 'value' in sensor_result:
                    sensor_values[sensor_id] = float(sensor_result['value'])

            # 生成控制信号
            control_signals = self.pvaec_engine.generate_control_signals(sensor_values)

            # 构建动作指令
            actions: Dict[str, Any] = {}
            for actuator_id, value in control_signals.items():
                actions[actuator_id] = {
                    'value': value
                }

            return actions
        else:
            # 如果没有PVAEC引擎，使用简单的随机动作
            return self._generate_simple_action()

    def _generate_simple_action(self) -> Dict[str, Any]:
        """生成简单动作

        返回:
            Dict[str, Any] - 动作指令
        """
        import random

        actions: Dict[str, Any] = {}
        # 随机选择一个执行器生成动作
        actuators = [comp for comp in self.components.values() if hasattr(comp, 'act')]
        if actuators:
            actuator = random.choice(actuators)
            actions[actuator.id] = {
                'value': random.uniform(-1.0, 1.0)
            }

        return actions

    def execute_action(self, environment: Any, action: Dict[str, Any]) -> Dict[str, Any]:
        """执行动作

        参数:
            environment - 环境实例
            action: Dict[str, Any] - 动作指令

        返回:
            Dict[str, Any] - 执行结果
        """
        results: Dict[str, Any] = {}

        # 执行每个动作
        for actuator_id, action_details in action.items():
            actuator = self.get_component(actuator_id)
            if actuator and hasattr(actuator, 'act'):
                result = actuator.act(environment, self, action_details)
                results[actuator_id] = result

        return results

    def learn_from_experience(self, perception: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any], new_perception: Dict[str, Any]) -> None:
        """从经验中学习

        参数:
            perception: Dict[str, Any] - 行动前的感知
            action: Dict[str, Any] - 执行的行动
            result: Dict[str, Any] - 行动结果
            new_perception: Dict[str, Any] - 行动后的感知
        """
        # 计算行动成功率
        success_rate = self._calculate_success_rate(perception, new_perception)

        # 更新PVAEC引擎的关联
        if self.pvaec_engine:
            # 学习传感器和执行器的关联
            for sensor_id in perception.keys():
                for actuator_id in action.keys():
                    self.pvaec_engine.learn_association(sensor_id, actuator_id, success_rate > 0.5)

        # 存储记忆
        if self.memory_system:
            memory_entry: Dict[str, Any] = {
                'situation': perception,
                'action_pattern': action,
                'result': result,
                'success_rate': success_rate,
                'timestamp': self.age
            }
            self.memory_system.store(memory_entry)

    def _calculate_success_rate(self, old_perception: Dict[str, Any], new_perception: Dict[str, Any]) -> float:
        """计算行动成功率

        参数:
            old_perception: Dict[str, Any] - 行动前的感知
            new_perception: Dict[str, Any] - 行动后的感知

        返回:
            float - 行动成功率 (0-1)
        """
        # 简单的成功率计算：比较前后感知差异
        # 如果环境对生物体更有利，成功率更高
        success: float = 0.5  # 默认成功率

        # 检查能量变化
        if self.energy > getattr(self, '_previous_energy', self.energy):
            success += 0.3
        elif self.energy < getattr(self, '_previous_energy', self.energy):
            success -= 0.3

        self._previous_energy = self.energy

        # 限制成功率在0-1之间
        return max(0.0, min(1.0, success))

    def get_status(self) -> Dict[str, Any]:
        """获取生物体状态

        返回:
            Dict[str, Any] - 状态信息
        """
        status = super().get_status()
        status.update({
            'type': 'intelligent_organism',
            'has_pvaec_engine': self.pvaec_engine is not None,
            'learning_efficiency': self.learning_efficiency,
            'exploration_bias': self.exploration_bias,
            'has_memory': self.memory_system is not None
        })
        return status
