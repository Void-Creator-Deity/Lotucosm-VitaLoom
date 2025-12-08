"""组件系统的基类定义"""

from typing import Optional, Dict, Any, List, TypeVar, TYPE_CHECKING
import numpy as np
import random

# 类型变量，用于避免循环导入
T = TypeVar('T')

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from .connection import Connection

# 类型别名，用于简化类型注解
ConnectionType = 'Connection'

class ComponentBase:
    """组件基类 - 所有具体组件的父类

    定义了所有组件的通用属性和方法，包括信号处理、连接管理、
    状态更新和遗传特性等。

    属性:
        id: str - 组件唯一标识符
        organism_id: str - 所属生物体ID
        position: np.ndarray - 位置坐标
        connections: List['Connection'] - 连接列表
        activation: float - 激活值
        state: str - 状态标识: idle, active, processing
        genetic_strength: float - 遗传强度
        mutation_rate: float - 变异率
        input_signals: Dict[str, float] - 输入信号字典
        output_signal: float - 输出信号
        signal_threshold: float - 信号激活阈值
        transmitting: bool - 防止信号传递循环的标志

        # 位置属性
        location: str - 组件位置: 'internal', 'external', 'both'
        acquired: bool - 是否是后天获得的
        congenital: bool - 是否是先天组件
        attach_point: Optional[str] - 附着点（对于体外组件）
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """初始化组件对象

        参数:
            component_id: str - 组件唯一标识符
            organism_id: str - 所属生物体ID
            kwargs: 其他参数
        """
        self.id = component_id  # 组件唯一标识符
        self.organism_id = organism_id  # 所属生物体ID
        self.position = np.array(kwargs.get('position', (0.0, 0.0)), dtype=float)  # 位置坐标
        self.connections: List['Connection'] = []  # 连接列表
        self.activation = 0.0  # 激活值
        self.state = "idle"  # 状态标识: idle, active, processing
        self.type = self.__class__.__name__.lower()  # 组件类型

        # 遗传特性
        self.genetic_strength = kwargs.get('genetic_strength', 1.0)  # 遗传强度，影响遗传概率
        self.mutation_rate = kwargs.get('mutation_rate', 0.1)  # 变异率，控制遗传变异的概率

        # 信号处理
        self.input_signals: Dict[str, float] = {}  # 输入信号字典，{源组件ID: 信号值}
        self.output_signal: float = 0.0  # 输出信号
        self.signal_threshold = kwargs.get('signal_threshold', 0.1)  # 信号激活阈值，超过此值则激活
        self.transmitting = False  # 防止信号传递循环的标志

        # 位置属性
        self.location = kwargs.get('location', 'internal')  # 'internal', 'external', 'both'
        self.acquired = kwargs.get('acquired', False)
        self.congenital = kwargs.get('congenital', True)
        self.attach_point = kwargs.get('attach_point', None)

        # 传感器和执行器标识
        self.is_sensor: bool = kwargs.get('is_sensor', False)
        self.is_actuator: bool = kwargs.get('is_actuator', False)

        # 物理属性
        self.velocity: np.ndarray = np.array(kwargs.get('velocity', (0.0, 0.0)), dtype=float)
        self.acceleration: np.ndarray = np.array(kwargs.get('acceleration', (0.0, 0.0)), dtype=float)
        self.decay_level: float = kwargs.get('decay_level', 0.0)
        self.floating: bool = kwargs.get('floating', False)

        # 能量相关属性
        self.energy_consumption: float = kwargs.get('energy_consumption', 0.1)

        # 传感器相关属性
        self.sensor_sensitivity: float = kwargs.get('sensor_sensitivity', 1.0)
        self.sense_range: float = kwargs.get('sense_range', 10.0)

        # 执行器相关属性
        self.actuator_strength: float = kwargs.get('actuator_strength', 1.0)
        self.actuation_speed: float = kwargs.get('actuation_speed', 1.0)

        # 混合组件属性
        self.is_hybrid: bool = kwargs.get('is_hybrid', False)
        self.mode: str = kwargs.get('mode', 'balanced')  # balanced, sensor_primary, actuator_primary

        # 膜组件属性
        self.is_membrane: bool = kwargs.get('is_membrane', False)
        self.permeability: float = kwargs.get('permeability', 0.5)
        self.thickness: float = kwargs.get('thickness', 1.0)
        self.surface_area: float = kwargs.get('surface_area', 1.0)

        # PVAEC引擎属性
        self.is_pvaec_engine: bool = kwargs.get('is_pvaec_engine', False)
        self.learning_rate: float = kwargs.get('learning_rate', 0.1)
        self.exploration_rate: float = kwargs.get('exploration_rate', 0.1)

        # 统计属性
        self.usage_count: int = kwargs.get('usage_count', 0)
        self.name: str = kwargs.get('name', f"component_{component_id}")

    def reset_state(self):
        """重置组件状态"""
        self.activation = 0.0
        self.state = "idle"
        self.input_signals.clear()
        self.output_signal = 0.0
        self.transmitting = False

    def process(self, input_value: float) -> Optional[float]:
        """处理输入，返回输出值

        更新激活状态，并根据输入值生成输出信号。

        参数:
            input_value: float - 输入值

        返回:
            Optional[float] - 处理后的输出值，None表示无输出
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        # 基础处理逻辑，子类可以重写
        self.output_signal = input_value
        return self.output_signal

    def update(self):
        """每帧更新

        更新组件状态，包括连接更新、输入信号重置和状态恢复等。
        """
        # 更新所有连接
        for connection in self.connections:
            if hasattr(connection, 'update'):
                connection.update()

        # 重置输入信号
        self.input_signals.clear()

        # 如果没有活动，恢复到闲置状态
        if self.state == "active" and abs(self.activation) < self.signal_threshold:
            self.state = "idle"

    def transmit_signals(self):
        """向所有连接的目标传递信号

        通过所有连接向目标组件传递信号，避免循环传递。
        """
        # 避免重复传递信号
        if self.transmitting:
            return

        try:
            self.transmitting = True
            for connection in self.connections:
                # 只向目标组件传递信号（即作为源的连接）
                if hasattr(connection, 'source') and connection.source == self:
                    # 检查目标组件是否已经在传递信号，避免循环
                    if hasattr(connection, 'target') and hasattr(connection.target, 'transmitting') and not connection.target.transmitting:
                        # 传递信号，经过连接的权重处理
                        if hasattr(connection, 'transmit_signal'):
                            transmitted_value = connection.transmit_signal(self.output_signal)
                            # 更新目标组件的输入信号字典
                            if hasattr(connection.target, 'input_signals'):
                                connection.target.input_signals[self.id] = transmitted_value
        finally:
            # 确保无论如何都会重置transmitting标志
            self.transmitting = False

    def mutate(self):
        """变异

        对组件的遗传特性进行随机变异，包括遗传强度和信号阈值。
        """
        if random.random() < self.mutation_rate:  # 根据变异率决定是否变异
            # 遗传强度变异，服从高斯分布
            self.genetic_strength = np.clip(self.genetic_strength + random.gauss(0, 0.1), 0.5, 2.0)
            # 信号阈值变异，服从高斯分布
            self.signal_threshold = np.clip(self.signal_threshold + random.gauss(0, 0.05), 0.01, 0.5)

    def clone(self):
        """克隆组件

        创建一个组件的副本，具有相同的属性值，
        但使用不同的ID，以便于区分。

        返回:
            ComponentBase: 克隆的组件实例
        """
        # 创建一个新的组件实例，使用当前类
        # 为克隆组件生成一个新的ID，格式为 "原ID_clone_随机数"
        new_id = f"{self.id}_clone_{random.randint(1000, 9999)}"
        # 使用当前类的构造函数创建新实例
        cloned_component = self.__class__(new_id, self.organism_id)

        # 复制所有属性
        cloned_component.position = self.position.copy()
        cloned_component.connections = []  # 新组件没有连接
        cloned_component.activation = self.activation
        cloned_component.state = self.state
        cloned_component.genetic_strength = self.genetic_strength
        cloned_component.mutation_rate = self.mutation_rate
        cloned_component.input_signals = self.input_signals.copy()
        cloned_component.output_signal = self.output_signal
        cloned_component.signal_threshold = self.signal_threshold
        cloned_component.location = self.location
        cloned_component.acquired = self.acquired
        cloned_component.congenital = self.congenital
        cloned_component.attach_point = self.attach_point

        # 复制传感器和执行器标识
        cloned_component.is_sensor = self.is_sensor
        cloned_component.is_actuator = self.is_actuator

        # 复制物理属性
        cloned_component.velocity = self.velocity.copy()
        cloned_component.acceleration = self.acceleration.copy()
        cloned_component.decay_level = self.decay_level
        cloned_component.floating = self.floating

        return cloned_component

    def get_status(self) -> Dict[str, Any]:
        """获取组件状态

        返回组件的当前状态信息。

        返回:
            dict: 组件状态信息
        """
        return {
            'id': self.id,
            'type': self.type,
            'location': self.location,
            'acquired': self.acquired,
            'congenital': self.congenital,
            'attach_point': self.attach_point,
            'state': self.state,
            'activation': self.activation,
            'genetic_strength': self.genetic_strength
        }

    def add_connection(self, connection: Any) -> None:
        """添加连接

        参数:
            connection: Any - 要添加的连接
        """
        if connection not in self.connections:
            self.connections.append(connection)

    def draw(self, surface: Any) -> None:
        """绘制组件

        参数:
            surface: Any - 绘制表面
        """
        pass

    def sense(self, environment: Any, organism: Any = None) -> Dict[str, Any]:
        """传感器感知环境

        参数:
            environment: Any - 环境对象
            organism: Any - 所属生物体

        返回:
            Dict[str, Any] - 感知结果
        """
        return {}

    def act(self, environment: Any, organism: Any, action: Any = None) -> Dict[str, Any]:
        """执行器执行动作

        参数:
            environment: Any - 环境对象
            organism: Any - 所属生物体
            action: Any - 动作指令

        返回:
            Dict[str, Any] - 动作结果
        """
        return {}

    def learn_association(self, *args: Any, **kwargs: Any) -> None:
        """学习关联关系

        支持两种调用方式：
        1. 标准方式：learn_association(situation, action, outcome)
        2. PVAECEngine方式：learn_association(sensor_id, actuator_id, success)

        参数:
            *args: 可变参数
            **kwargs: 关键字参数
        """
        pass

    def generate_control_signals(self, sensor_values: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """生成控制信号

        参数:
            sensor_values: Optional[Dict[str, float]] - 传感器值字典

        返回:
            Dict[str, float] - 控制信号字典
        """
        return {}

    @property
    def radius(self) -> float:
        """组件半径属性

        返回:
            float - 组件半径
        """
        return 5.0
