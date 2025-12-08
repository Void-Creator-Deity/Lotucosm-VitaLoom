"""生物体基类实现"""

from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
import numpy as np
from vitalloom.components.components_base import ComponentBase


if TYPE_CHECKING:
    from ..core.memory import MemoryGene


class Organism:
    """生物体基类 - 所有生物体的父类

    定义了所有生物体的通用属性和方法，包括组件管理、能量管理、
    繁殖机制和环境交互等。
    """

    def __init__(self, organism_id: str, position: Tuple[float, float], **kwargs: Any):
        """初始化生物体

        参数:
            organism_id: str - 生物体唯一标识符
            position: Tuple[float, float] - 初始位置
            kwargs: 其他参数
        """
        self.id = organism_id  # 生物体唯一标识符
        self.name: str = kwargs.get('name', organism_id)  # 生物体名称
        self.position = np.array(position, dtype=float)  # 位置坐标
        self.velocity = np.array([0.0, 0.0], dtype=float)  # 速度向量
        self.acceleration = np.array([0.0, 0.0], dtype=float)  # 加速度向量
        self.energy: float = float(kwargs.get('energy', 100.0))  # 初始能量
        self.max_energy: float = float(kwargs.get('max_energy', 200.0))  # 最大能量
        self.health: float = float(kwargs.get('health', 100.0))  # 健康值
        self.max_health: float = float(kwargs.get('max_health', 100.0))  # 最大健康值
        self.age: int = 0  # 年龄（迭代次数）
        self.dead: bool = False  # 是否死亡

        # 组件管理
        self.components: Dict[str, ComponentBase] = {}  # 组件字典，{组件ID: 组件实例}
        self.sensors: Dict[str, ComponentBase] = {}  # 传感器组件字典
        self.actuators: Dict[str, ComponentBase] = {}  # 执行器组件字典
        self.membrane: Optional[ComponentBase] = None  # 细胞膜组件
        self.connections: List[Dict[str, str | float]] = []  # 组件连接列表，[{'source': 源组件ID, 'target': 目标组件ID, 'weight': 权重}]
        self.control_signals: Dict[str, float] = {}  # 控制信号字典
        self.inherited_memories: List['MemoryGene'] = []  # 遗传记忆列表

        # 遗传特性
        self.mutation_rate: float = float(kwargs.get('mutation_rate', 0.1))  # 变异率
        self.inheritance_rate: float = float(kwargs.get('inheritance_rate', 0.8))  # 遗传率

        # 能量消耗率
        self.energy_consumption_rate: float = float(kwargs.get('energy_consumption_rate', 0.01))  # 基础能量消耗率

        # 记忆系统
        self.memory_system: Optional[Any] = kwargs.get('memory_system', None)  # 记忆系统实例

        # 学习和行为相关属性
        self.generation: int = int(kwargs.get('generation', 0))  # 世代数
        self.current_action: str = str(kwargs.get('current_action', 'idle'))  # 当前动作
        self.learned_memories: List['MemoryGene'] = []  # 学习记忆列表

        # 形状属性
        self.radius: float = float(kwargs.get('radius', 20.0))  # 生物体半径
        self.learning_efficiency: float = float(kwargs.get('learning_efficiency', 0.5))  # 学习效率
        self.exploration_bias: float = float(kwargs.get('exploration_bias', 0.3))  # 探索偏向

    def add_component(self, component: ComponentBase) -> bool:
        """添加组件到生物体

        参数:
            component: ComponentBase - 组件实例

        返回:
            bool - 添加是否成功
        """
        if component.id in self.components:
            return False  # 组件ID已存在

        self.components[component.id] = component

        # 分类组件
        if component.type == 'sensor':
            self.sensors[component.id] = component
        elif component.type == 'actuator':
            self.actuators[component.id] = component

        # 特殊处理细胞膜组件
        if hasattr(component, 'radius') and component.type == 'membrane':
            self.membrane = component

        return True

    def add_sensor(self, sensor: ComponentBase) -> bool:
        """添加传感器组件

        参数:
            sensor: ComponentBase - 传感器组件实例

        返回:
            bool - 添加是否成功
        """
        if sensor.type != 'sensor':
            return False
        return self.add_component(sensor)

    def add_actuator(self, actuator: ComponentBase) -> bool:
        """添加执行器组件

        参数:
            actuator: ComponentBase - 执行器组件实例

        返回:
            bool - 添加是否成功
        """
        if actuator.type != 'actuator':
            return False
        return self.add_component(actuator)

    def connect_tools(self, source_id: str, target_id: str, weight: float = 1.0) -> bool:
        """连接两个组件

        参数:
            source_id: str - 源组件ID
            target_id: str - 目标组件ID
            weight: float - 连接权重，正值为兴奋性连接，负值为抑制性连接

        返回:
            bool - 连接是否成功
        """
        # 检查组件是否存在
        if source_id not in self.components or target_id not in self.components:
            return False

        # 检查是否已存在连接
        for conn in self.connections:
            if conn['source'] == source_id and conn['target'] == target_id:
                return False

        # 添加连接，包含权重信息
        self.connections.append({'source': source_id, 'target': target_id, 'weight': weight})

        # 实际创建组件间的连接对象，以便信号传递
        try:
            from vitalloom.components.connection import Connection
            source = self.components[source_id]
            target = self.components[target_id]
            conn = Connection(source, target, weight=weight)
            source.add_connection(conn)
            target.add_connection(conn)
        except ImportError:
            # 如果无法导入Connection类，仅记录连接信息
            pass

        return True

    def remove_component(self, component_id: str) -> bool:
        """从生物体中移除组件

        参数:
            component_id: str - 组件ID

        返回:
            bool - 移除是否成功
        """
        if component_id not in self.components:
            return False

        # 从相应的字典中移除
        if component_id in self.sensors:
            del self.sensors[component_id]
        if component_id in self.actuators:
            del self.actuators[component_id]

        # 移除细胞膜引用
        if self.membrane and getattr(self.membrane, 'id', None) == component_id:
            self.membrane = None

        # 移除组件
        del self.components[component_id]

        return True

    def get_component(self, component_id: str) -> Optional[ComponentBase]:
        """获取组件

        参数:
            component_id: str - 组件ID

        返回:
            Optional[ComponentBase] - 组件实例，不存在返回None
        """
        return self.components.get(component_id, None)

    def apply_force(self, force_vector: np.ndarray):
        """应用力到生物体

        参数:
            force_vector: np.ndarray - 力向量
        """
        self.acceleration += force_vector

    def update(self, environment: Any):
        """每帧更新生物体状态

        参数:
            environment - 环境实例
        """
        if self.dead:
            return

        # 更新年龄
        self.age += 1

        # 更新位置和速度
        self.update_physics()

        # 更新组件
        self.update_components(environment)

        # 消耗能量
        self.consume_energy()

        # 检查能量和健康
        self.check_vital_signs()

        # 更新记忆系统
        if self.memory_system:
            self.memory_system.update()

    def draw(self, surface: Any):
        """绘制生物体及其组件

        参数:
            surface - 绘制表面
        """
        try:
            import pygame
            # 绘制生物体主体
            pos = self.position.astype(int)
            pygame.draw.circle(surface, (100, 150, 200), tuple(pos), self.radius)

            # 绘制细胞膜
            if self.membrane:
                pygame.draw.circle(surface, (150, 200, 250), tuple(pos), self.radius + 2, 2)

            # 绘制传感器
            for sensor in self.sensors.values():
                if hasattr(sensor, 'draw'):
                    sensor.draw(surface)

            # 绘制执行器
            for actuator in self.actuators.values():
                if hasattr(actuator, 'draw'):
                    actuator.draw(surface)
        except ImportError:
            pass  # 如果pygame未导入，跳过绘制

    def update_physics(self):
        """更新物理状态（位置、速度、加速度）"""
        # 更新速度
        self.velocity += self.acceleration

        # 限制速度
        max_speed = 5.0
        speed = np.linalg.norm(self.velocity)
        if speed > max_speed:
            self.velocity = (self.velocity / speed) * max_speed

        # 更新位置
        self.position += self.velocity

        # 重置加速度
        self.acceleration *= 0

    def update_components(self, environment: Any):
        """更新所有组件

        参数:
            environment - 环境实例
        """
        # 1. 更新所有组件状态
        for value in self.components.values():
            value.update()

        # 2. 处理信号传递
        for value in self.components.values():
            # 处理传感器输入（感知）
            if hasattr(value, 'sense') and value.is_sensor:
                sense_result = value.sense(environment, self)
                if sense_result:
                    # 将感知结果转换为输出信号
                    output_signal = sense_result.get('signal_value', 0.0)
                    value.output_signal = output_signal

            # 处理执行器动作
            elif hasattr(value, 'act') and value.is_actuator:
                # 计算输入信号总和
                input_sum = sum(value.input_signals.values()) if value.input_signals else 0.0
                if abs(input_sum) > value.signal_threshold:
                    # 生成动作
                    action_result = value.act(environment, self, {'signal': input_sum})
                    if action_result:
                        # 更新执行器状态
                        value.output_signal = action_result.get('signal_value', 0.0)

            # 普通组件处理输入信号
            else:
                # 计算输入信号总和
                input_sum = sum(value.input_signals.values()) if value.input_signals else 0.0
                if abs(input_sum) > value.signal_threshold:
                    # 处理输入信号
                    output = value.process(input_sum)
                    if output is not None:
                        value.output_signal = output

            # 3. 传递信号到连接的组件
            value.transmit_signals()

    def consume_energy(self):
        """消耗能量"""
        # 基础能量消耗
        self.energy -= self.energy_consumption_rate

        # 组件能量消耗
        for _, _ in self.components.items():
            self.energy -= 0.001  # 每个组件的基础消耗

    def check_vital_signs(self):
        """检查生命体征，判断是否死亡"""
        if self.energy <= 0 or self.health <= 0:
            self.die()

    def die(self):
        """生物体死亡处理"""
        self.dead = True
        print(f"生物体 {self.id} 死亡，年龄: {self.age}")

        # 释放组件到环境
        for component in self.components.values():
            self.release_component(component)

    def release_component(self, component: ComponentBase):
        """释放组件到环境

        参数:
            component: ComponentBase - 要释放的组件
        """
        # 实际项目中需要与环境系统集成
        # 例如：environment.add_floating_component(component, self.position)
        _ = component  # 占位符，避免未使用变量警告
        pass

    def ready_to_reproduce(self) -> bool:
        """检查是否准备好繁殖

        返回:
            bool - 是否准备好繁殖
        """
        # 简单的繁殖条件：能量超过阈值且健康良好
        return self.energy > self.max_energy * 0.6 and self.health > self.max_health * 0.8

    def reproduce(self) -> Optional['Organism']:
        """繁殖，创建子代

        返回:
            Optional['Organism'] - 子代生物体，繁殖失败返回None
        """
        if not self.ready_to_reproduce():
            return None

        # 消耗能量
        self.energy -= self.max_energy * 0.3

        # 创建子代
        offspring_id = f"{self.id}_offspring_{self.age}"
        # 将numpy数组转换为元组，匹配构造函数的类型要求
        offspring_position = tuple((self.position + np.random.randn(2) * 20).tolist())
        offspring = self.__class__(offspring_id, offspring_position)

        # 遗传组件
        self.inherit_components(offspring)

        # 遗传记忆
        self.inherit_memory(offspring)

        # 应用变异
        offspring.mutate()

        return offspring

    def inherit_components(self, offspring: 'Organism'):
        """遗传组件给子代

        参数:
            offspring: 'Organism' - 子代生物体
        """
        for _, comp in self.components.items():
            # 先天组件100%遗传，后天组件按遗传率遗传
            if comp.congenital or np.random.random() < self.inheritance_rate:
                # 复制组件
                component_copy = self._copy_component(comp)
                if component_copy:
                    offspring.add_component(component_copy)

    def inherit_memory(self, offspring: 'Organism'):
        """遗传记忆给子代

        参数:
            offspring: 'Organism' - 子代生物体
        """
        if self.memory_system and offspring.memory_system:
            # 记忆遗传逻辑
            pass

    def _copy_component(self, component: ComponentBase) -> Optional[ComponentBase]:
        """复制组件

        参数:
            component: ComponentBase - 要复制的组件

        返回:
            Optional[ComponentBase] - 复制的组件实例
        """
        # 实际项目中需要实现组件的深拷贝
        # 这里简化处理，直接返回原组件（实际项目需要改进）
        return component

    def mutate(self):
        """变异处理

        对生物体的属性和组件进行随机变异
        """
        # 变异率
        if np.random.random() < self.mutation_rate:
            # 简单的属性变异
            self.mutation_rate += np.random.randn() * 0.01
            self.inheritance_rate += np.random.randn() * 0.01

            # 限制在合理范围内
            self.mutation_rate = max(0.01, min(0.5, self.mutation_rate))
            self.inheritance_rate = max(0.5, min(0.99, self.inheritance_rate))

        # 组件变异
        for component in self.components.values():
            component.mutate()

    def can_capture(self, component: ComponentBase) -> bool:
        """检查是否可以捕获组件

        参数:
            component: ComponentBase - 待捕获的组件

        返回:
            bool - 是否可以捕获
        """
        # 检查距离
        if self.membrane:
            distance = np.linalg.norm(component.position - self.position)
            return bool(distance <= self.membrane.radius + 10)
        return False

    def capture_component(self, component: ComponentBase) -> bool:
        """捕获组件

        参数:
            component: ComponentBase - 待捕获的组件

        返回:
            bool - 捕获是否成功
        """
        if not self.can_capture(component):
            return False

        # 消耗能量
        capture_cost = 5.0
        if self.energy < capture_cost:
            return False

        self.energy -= capture_cost

        # 设置组件为后天获得
        component.acquired = True
        component.congenital = False

        # 添加组件
        return self.add_component(component)

    def get_status(self) -> Dict[str, Any]:
        """获取生物体状态

        返回:
            Dict[str, Any] - 状态信息
        """
        return {
            'id': self.id,
            'position': self.position.tolist(),
            'energy': self.energy,
            'health': self.health,
            'age': self.age,
            'component_count': len(self.components),
            'dead': self.dead,
            'mutation_rate': self.mutation_rate,
            'inheritance_rate': self.inheritance_rate
        }
