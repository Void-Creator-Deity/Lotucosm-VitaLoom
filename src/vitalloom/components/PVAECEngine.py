from .components_base import ComponentBase
from typing import Dict, Any, Optional
import random

class PVAECEngine(ComponentBase):
    """
    PVAEC引擎组件（原中枢大脑）
    实现感知-验证自主演化循环的核心逻辑
    兼具复合器功能但不继承复合器，留好扩展后面有可能对接ai智能体
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """
        初始化PVAEC引擎

        参数:
        - component_id: 组件ID
        - organism_id: 所属生物体ID
        - kwargs: 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # PVAEC引擎特有属性
        self.associations: Dict[str, Dict[str, float]] = {}  # {传感器ID: {执行器ID: 关联强度}}
        self.learning_rate = kwargs.get('learning_rate', 0.1)  # 学习率
        self.success_threshold = kwargs.get('success_threshold', 0.5)  # 成功阈值
        self.exploration_rate = kwargs.get('exploration_rate', 0.3)  # 探索率

        # 位置属性
        self.location = kwargs.get('location', 'internal')  # 通常位于内部
        self.congenital = kwargs.get('congenital', True)  # 通常是先天组件

    def learn_association(self, sensor_id: str, actuator_id: str, success: bool):
        """
        学习传感器和执行器的关联

        参数:
        - sensor_id: 传感器ID
        - actuator_id: 执行器ID
        - success: 行动是否成功
        """
        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}  # 初始化该传感器的关联字典
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5  # 初始关联强度

        # 根据成功与否调整关联强度
        if success:
            # 成功时增强关联
            self.associations[sensor_id][actuator_id] = min(1.0, self.associations[sensor_id][actuator_id] + self.learning_rate)
        else:
            # 失败时减弱关联
            self.associations[sensor_id][actuator_id] = max(0.0, self.associations[sensor_id][actuator_id] - self.learning_rate * 0.5)

    def generate_control_signals(self, sensor_values: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        根据传感器输入生成控制信号

        参数:
        - sensor_values: 传感器值字典（可选）

        返回:
        - Dict[str, float]: 控制信号字典
        """
        control_signals: Dict[str, float] = {}

        # 处理sensor_values为None的情况
        if sensor_values is None:
            sensor_values = {}

        # 根据关联生成控制信号
        for sensor_id, value in sensor_values.items():
            if sensor_id in self.associations:
                for actuator_id, strength in self.associations[sensor_id].items():
                    if actuator_id not in control_signals:
                        control_signals[actuator_id] = 0.0
                    # 传感器值乘以关联强度，累加到控制信号
                    control_signals[actuator_id] += value * strength

        # 添加探索行为，增加系统的探索能力
        if random.random() < self.exploration_rate:
            # 随机选择一些执行器添加随机信号
            for actuator_id in control_signals:
                if random.random() < 0.5:
                    control_signals[actuator_id] += random.uniform(-0.5, 0.5)

        # 归一化控制信号到[-1, 1]范围
        for actuator_id in control_signals:
            control_signals[actuator_id] = max(-1.0, min(1.0, control_signals[actuator_id]))

        return control_signals

    def process(self, input_value: float) -> float:
        """
        处理输入信号

        参数:
        - input_value: 输入信号值

        返回:
        - float: 处理后的输出信号
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        # PVAEC引擎的核心处理逻辑
        # 实际项目中需要与PVAEC循环集成
        self.output_signal = input_value * 0.8  # 简单的信号处理

        return self.output_signal

    def update(self):
        """
        更新PVAEC引擎状态
        """
        super().update()
        # PVAEC引擎特有更新逻辑
        # 可以添加记忆衰减、关联优化等逻辑

    def get_status(self) -> Dict[str, Any]:
        """
        获取PVAEC引擎状态

        返回:
        - Dict[str, Any]: 引擎状态信息
        """
        status = super().get_status()
        status.update({
            'learning_rate': self.learning_rate,
            'success_threshold': self.success_threshold,
            'exploration_rate': self.exploration_rate,
            'association_count': sum(len(acts) for acts in self.associations.values())
        })
        return status
