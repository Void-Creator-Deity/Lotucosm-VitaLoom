"""执行器实现"""

from typing import Dict, Any
import math
import numpy as np
from .components_base import ComponentBase

class Actuator(ComponentBase):
    """执行器基类

    所有执行器的基类，提供执行器的基本功能和属性
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化执行器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: Any - 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 执行器特有属性
        self.force_strength = kwargs.get('force_strength', 5.0)  # 力的强度
        self.current_force = 0.0  # 当前力值
        self.actuation_speed = kwargs.get('actuation_speed', 1.0)  # 执行速度
        self.is_actuator = True  # 标记为执行器
        self.actuator_type = kwargs.get('actuator_type', 'general')  # 执行器类型

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def act(self, environment: Any, organism: Any, action: Any = None) -> Dict[str, Any]:
        """执行动作，返回执行结果

        参数:
            environment: Any - 环境对象
            organism: Any - 生物体实例
            action: Any - 行动指令（可选）

        返回:
            Dict[str, Any] - 执行结果
        """
        # 子类实现具体的执行逻辑
        return {
            'type': self.actuator_type,
            'success': False,
            'message': 'Not implemented'
        }

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        return input_value * 0.9

    def update(self):
        """每帧更新"""
        super().update()
        # 执行器特有更新逻辑

class MuscleActuator(Actuator):
    """肌肉执行器 - 收缩产生力

    肌肉执行器的实现，通过收缩产生力，力的方向垂直于其位置向量。

    属性:
        contraction: float - 收缩程度，范围0-1
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化肌肉执行器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: Any - 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 执行器特有属性
        self.force_strength = kwargs.get('force_strength', 8.0)  # 力的强度
        self.current_force = 0.0  # 当前力值
        self.last_force = 0.0  # 上次力值
        self.force_decay_rate = kwargs.get('force_decay_rate', 0.1)  # 力衰减率
        self.contraction = 0.0  # 收缩程度 0-1

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def act(self, environment: Any, organism: Any, action: Any = None) -> Dict[str, Any]:
        """执行动作，返回执行结果

        根据动作指令施加力，返回执行结果。

        参数:
            environment: Any - 环境对象
            organism: Any - 生物体实例
            action: Dict[str, Any] - 行动指令

        返回:
            Dict[str, Any] - 执行结果
        """
        # 获取控制信号
        control_signal = action.get('value', 0.0)

        # 计算力向量
        force_vector = self.apply_force(control_signal)

        # 应用力到生物体
        organism.apply_force(force_vector)

        # 返回执行结果
        return {
            'type': 'muscle',
            'force_vector': force_vector.tolist(),
            'contraction': self.contraction,
            'force_strength': self.force_strength,
            'success': True
        }

    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量

        根据控制信号计算收缩程度，并生成垂直于位置向量的力。

        参数:
            control_signal: float - 控制信号，范围-1到1

        返回:
            np.ndarray - 力向量
        """
        self.contraction = np.clip(abs(control_signal), 0, 1)  # 限制收缩程度在0-1之间
        self.current_force = self.contraction * self.force_strength  # 计算当前力

        # 肌肉产生的力方向垂直于其位置向量（简化模型）
        force_dir = np.array([-self.position[1], self.position[0]])
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)  # 归一化

        # 根据控制信号方向调整力的方向
        direction = 1 if control_signal > 0 else -1

        return force_dir * self.current_force * direction  # 返回力向量

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        肌肉执行器处理输入信号，生成控制信号。

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        # 肌肉执行器的处理逻辑
        self.output_signal = input_value * 0.9  # 简单的信号处理

        return self.output_signal

    def update(self):
        """每帧更新

        更新执行器状态，包括调用父类的更新方法和更新执行器特有状态。
        """
        super().update()
        # 执行器特有更新逻辑
        # 力的衰减
        if abs(self.current_force) > 0:
            self.current_force *= (1 - self.force_decay_rate)
            if abs(self.current_force) < 0.01:
                self.current_force = 0.0

class CiliaActuator(Actuator):
    """纤毛执行器 - 摆动产生推进力

    纤毛执行器的实现，通过摆动产生推进力，力的方向与位置向量相反。

    属性:
        swing_phase: float - 摆动相位，范围0-2π
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化纤毛执行器

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: Any - 其他参数
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 执行器特有属性
        self.force_strength = kwargs.get('force_strength', 4.0)  # 力的强度
        self.current_force = 0.0  # 当前力值
        self.last_force = 0.0  # 上次力值
        self.force_decay_rate = kwargs.get('force_decay_rate', 0.1)  # 力衰减率
        self.swing_phase = 0.0  # 摆动相位，范围0-2π

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 通常位于外部

    def act(self, environment: Any, organism: Any, action: Any = None) -> Dict[str, Any]:
        """执行动作，返回执行结果

        根据动作指令施加力，返回执行结果。

        参数:
            environment: Any - 环境对象
            organism: Any - 生物体实例
            action: Dict[str, Any] - 行动指令

        返回:
            Dict[str, Any] - 执行结果
        """
        # 获取控制信号
        control_signal = action.get('value', 0.0)

        # 计算力向量
        force_vector = self.apply_force(control_signal)

        # 应用力到生物体
        organism.apply_force(force_vector)

        # 返回执行结果
        return {
            'type': 'cilia',
            'force_vector': force_vector.tolist(),
            'swing_phase': self.swing_phase,
            'force_strength': self.force_strength,
            'success': True
        }

    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量

        根据控制信号更新摆动相位，并生成与位置向量相反的推进力。

        参数:
            control_signal: float - 控制信号

        返回:
            np.ndarray - 力向量
        """
        # 更新摆动相位
        self.swing_phase = (self.swing_phase + control_signal * 0.1) % (2 * math.pi)
        self.current_force = control_signal * self.force_strength  # 计算当前力

        # 纤毛产生的力方向与其位置方向相反（推进）
        force_dir = -self.position
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)  # 归一化

        return force_dir * self.current_force  # 返回力向量

    def process(self, input_value: float) -> float:
        """处理输入，返回输出值

        纤毛执行器处理输入信号，生成控制信号。

        参数:
            input_value: float - 输入值

        返回:
            float - 处理后的输出值
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        # 纤毛执行器的处理逻辑
        self.output_signal = input_value * 0.8  # 简单的信号处理

        return self.output_signal

    def update(self):
        """每帧更新

        更新执行器状态，包括调用父类的更新方法和更新执行器特有状态。
        """
        super().update()
        # 执行器特有更新逻辑
        # 力的衰减
        if abs(self.current_force) > 0:
            self.current_force *= (1 - self.force_decay_rate)
            if abs(self.current_force) < 0.01:
                self.current_force = 0.0
