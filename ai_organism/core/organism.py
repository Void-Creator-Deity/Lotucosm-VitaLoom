"""生物体实现"""

from typing import Dict, List, Tuple, Optional
import random
import numpy as np
import pygame
from ..tools import (
    TouchSensor, LightSensor, MuscleActuator, CiliaActuator, Connection,
    SensorTool, ActuatorTool, Membrane, CentralBrain
)
from .memory import MemoryGene


class Organism:
    """AI生命体 - 包含Tool系统和记忆继承机制
    
    这是AI生命体的核心类，实现了AI生命体的基本属性和行为，
    包括Tool系统管理、环境感知、决策、行动、学习和繁殖等功能。
    
    属性:
        id: str - 生命体唯一标识符
        position: np.ndarray - 位置坐标
        velocity: np.ndarray - 速度向量
        energy: float - 能量值
        age: int - 年龄
        generation: int - 代数
        membrane: Membrane - 细胞膜
        sensors: Dict[str, SensorTool] - 传感器集合
        actuators: Dict[str, ActuatorTool] - 执行器集合
        central_managers: Dict[str, CentralBrain] - 中枢管理器集合
        connections: List[Connection] - 连接列表
        inherited_memories: Dict[str, MemoryGene] - 遗传记忆库
        learned_memories: Dict[str, MemoryGene] - 学习记忆库
        current_action: str - 当前动作状态
        control_signals: Dict[str, float] - 当前控制信号
        uses_central_control: bool - 是否使用中枢控制
        color: Tuple[int, int, int] - 颜色
        radius: float - 半径
    """
    
    def __init__(self, organism_id: str, position: Tuple[float, float]):
        """初始化AI生命体
        
        参数:
            organism_id: str - 生命体唯一标识符
            position: Tuple[float, float] - 初始位置坐标
        """
        self.id = organism_id  # 生命体唯一标识符
        self.position = np.array(position, dtype=float)  # 位置坐标
        self.velocity = np.array([0.0, 0.0])  # 速度向量
        self.energy = 100.0  # 能量值，初始为100.0
        self.age = 0  # 年龄，初始为0
        self.generation = 0  # 代数，初始为0
        
        # 细胞膜 - 作为细胞边界
        self.membrane = Membrane(f"{organism_id}_membrane", self.position, 30)
        
        # Tool系统 - 存储各类工具组件
        self.sensors: Dict[str, SensorTool] = {}  # 传感器集合，{工具ID: 传感器对象}
        self.actuators: Dict[str, ActuatorTool] = {}  # 执行器集合，{工具ID: 执行器对象}
        self.central_managers: Dict[str, CentralBrain] = {}  # 中枢管理器集合
        self.connections: List[Connection] = []  # 连接列表，存储组件间的连接
        
        # 记忆系统 - 使用字典存储，提高查找效率
        self.inherited_memories: Dict[str, MemoryGene] = {}  # 遗传记忆，使用situation作为键
        self.learned_memories: Dict[str, MemoryGene] = {}  # 学习记忆，使用situation作为键
        
        # AI控制状态
        self.current_action = "explore"  # 当前动作状态，默认为"explore"（探索）
        self.control_signals: Dict[str, float] = {}  # 当前控制信号，{工具ID: 控制值}
        self.uses_central_control = False  # 是否使用中枢控制，默认为False
        
        # 外观 - 随机生成颜色
        self.color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        self.radius = self.membrane.radius  # 半径，由细胞膜半径决定
        
    def add_sensor(self, sensor: SensorTool):
        """添加传感器到AI生命体
        
        传感器用于感知环境信息，添加时会验证其位置是否在细胞膜内。
        
        参数:
            sensor: SensorTool - 要添加的传感器对象
        """
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(sensor.position + self.position):
            self.sensors[sensor.tool_id] = sensor
        
    def add_actuator(self, actuator: ActuatorTool):
        """添加执行器到AI生命体
        
        执行器用于与环境交互，添加时会验证其位置是否在细胞膜内，
        并初始化对应的控制信号。
        
        参数:
            actuator: ActuatorTool - 要添加的执行器对象
        """
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(actuator.position + self.position):
            self.actuators[actuator.tool_id] = actuator
            self.control_signals[actuator.tool_id] = 0.0  # 初始化控制信号为0
    
    def add_central_brain(self, central_brain: CentralBrain):
        """添加中枢管理器到AI生命体
        
        中枢管理器用于AI控制和决策，添加时会验证其位置是否在细胞膜内，
        并更新中枢控制状态。
        
        参数:
            central_brain: CentralBrain - 要添加的中枢管理器对象
        """
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(central_brain.position + self.position):
            self.central_managers[central_brain.tool_id] = central_brain
            self.uses_central_control = True  # 更新中枢控制状态
        
    def connect_tools(self, source_id: str, target_id: str, weight: float = 1.0, is_bidirectional: bool = False):
        """连接两个工具组件
        
        建立两个工具组件之间的连接，支持单向和双向连接，
        连接可以是传感器到执行器、传感器到中枢管理器、
        中枢管理器到执行器等任意组合。
        
        参数:
            source_id: str - 源工具的ID
            target_id: str - 目标工具的ID
            weight: float - 连接权重，默认为1.0
            is_bidirectional: bool - 是否为双向连接，默认为False
        """
        # 查找源Tool（可以是传感器、执行器或中枢管理器）
        source = (self.sensors.get(source_id) or 
                 self.actuators.get(source_id) or 
                 self.central_managers.get(source_id))
        
        # 查找目标Tool（可以是传感器、执行器或中枢管理器）
        target = (self.sensors.get(target_id) or 
                 self.actuators.get(target_id) or 
                 self.central_managers.get(target_id))
        
        if source and target:
            # 创建连接对象
            connection = Connection(source, target, weight, is_bidirectional)
            self.connections.append(connection)
            source.connections.append(connection)
            if is_bidirectional:
                target.connections.append(connection)
            
    def perceive_environment(self, environment) -> str:
        """感知环境，生成情境描述
        
        通过传感器感知环境信息，并结合内部状态生成情境描述字符串，
        用于后续的决策和记忆匹配。
        
        参数:
            environment - 环境对象，包含环境中的所有对象和属性
        
        返回:
            str - 情境描述字符串，格式为"感知1_感知2_..._感知n"，如"touch_high_light_low"
        """
        perceptions = []
        
        # 传感器感知环境
        for sensor in self.sensors.values():
            sensor_value = sensor.sense(environment, self.position)
            # 只添加有意义的感知（>0.1），减少后续处理量
            if sensor_value > 0.5:
                perceptions.append(f"{sensor.get_icon()}_high")  # 高感知值
            elif sensor_value > 0.1:
                perceptions.append(f"{sensor.get_icon()}_low")  # 低感知值
        
        # 加入内部状态感知
        if self.energy < 30:
            perceptions.append("low_energy")  # 低能量状态
        if self.age > 200:
            perceptions.append("old")  # 年老状态
        
        # 使用集合去重，避免重复感知
        perceptions = list(set(perceptions))
        return "_".join(perceptions) if perceptions else "neutral"  # 无感知时返回"neutral"
    
    def decide_action(self, situation: str) -> Dict[str, float]:
        """基于记忆决定控制信号
        
        根据当前情境，从记忆库中匹配最合适的记忆，并返回对应的控制信号。
        如果没有匹配的记忆，则生成随机控制信号。
        
        参数:
            situation: str - 当前情境描述
        
        返回:
            Dict[str, float] - 控制信号字典，{工具ID: 控制值}
        """
        situation_tags = set(situation.split("_"))
        if not situation_tags:
            return self._random_control()  # 无情境时随机决策
        
        # 更高效的记忆匹配 - 直接从字典中查找
        if situation in self.learned_memories:
            # 优先使用学习记忆
            return self.learned_memories[situation].action_pattern.copy()
        elif situation in self.inherited_memories:
            # 使用遗传记忆
            return self.inherited_memories[situation].action_pattern.copy()
        
        # 无精确匹配，尝试标签匹配
        all_memories = list(self.inherited_memories.values()) + list(self.learned_memories.values())
        if not all_memories:
            return self._random_control()  # 无记忆时随机决策
        
        # 更高效的记忆匹配 - 使用集合交集
        relevant_memories = []
        for memory in all_memories:
            memory_tags = set(memory.situation.split("_"))
            if memory_tags.intersection(situation_tags):
                relevant_memories.append(memory)
        
        if not relevant_memories:
            # 无相关记忆，随机探索
            return self._random_control()
            
        # 优化最佳记忆选择 - 避免lambda函数的额外开销
        best_memory = relevant_memories[0]
        best_score = best_memory.success_rate * best_memory.strength
        
        for memory in relevant_memories[1:]:
            current_score = memory.success_rate * memory.strength
            if current_score > best_score:
                best_memory = memory
                best_score = current_score
        
        return best_memory.action_pattern.copy()
    
    def _random_control(self) -> Dict[str, float]:
        """生成随机控制信号
        
        当没有匹配的记忆时，生成随机控制信号用于探索环境。
        
        返回:
            Dict[str, float] - 随机控制信号字典，{工具ID: 控制值}
        """
        controls = {}
        for actuator_id in self.actuators:
            controls[actuator_id] = random.uniform(-1, 1)  # 生成[-1, 1]范围内的随机数
        return controls
        
    def apply_controls(self, controls: Dict[str, float]):
        """应用控制信号到执行器
        
        将控制信号应用到对应的执行器，产生力并更新位置，
        同时消耗能量。
        
        参数:
            controls: Dict[str, float] - 控制信号字典，{工具ID: 控制值}
        """
        total_force = np.array([0.0, 0.0])
        
        for actuator_id, control_signal in controls.items():
            if actuator_id in self.actuators:
                actuator = self.actuators[actuator_id]
                force = actuator.apply_force(control_signal)
                total_force += force
                self.control_signals[actuator_id] = control_signal
                
        # 应用物理规则，更新速度和位置
        self.velocity = total_force * 0.1  # 速度与力成正比
        self.position += self.velocity  # 更新位置
        
        # 能量消耗 - 与控制信号强度成正比
        energy_cost = sum(abs(signal) for signal in controls.values()) * 0.1
        self.energy -= energy_cost
        
    def learn_from_experience(self, situation: str, controls: Dict[str, float], success: bool):
        """从经验中学习
        
        根据当前情境、控制信号和结果，更新或创建学习记忆。
        
        参数:
            situation: str - 当前情境描述
            controls: Dict[str, float] - 应用的控制信号
            success: bool - 行动是否成功
        """
        # 直接从字典中查找，提高效率
        if situation in self.learned_memories:
            # 强化或削弱现有记忆
            memory = self.learned_memories[situation]
            if memory.success_rate > 0.5 and success:
                # 记忆成功，强化记忆
                memory.strength = min(1.0, memory.strength + 0.1)
            elif memory.success_rate < 0.5 and not success:
                # 记忆失败，强化记忆
                memory.strength = min(1.0, memory.strength + 0.1)
            else:
                # 记忆预测错误，削弱记忆
                memory.strength = max(0.1, memory.strength - 0.2)
        else:
            # 创建新记忆
            new_memory = MemoryGene(situation, controls.copy(), 1.0 if success else 0.0)
            self.learned_memories[situation] = new_memory
        
    def reproduce(self) -> 'Organism':
        """繁殖后代
        
        创建一个新的AI生命体，继承当前生命体的Tool结构和记忆，
        并对记忆进行随机变异。
        
        返回:
            Organism - 新创建的后代AI生命体
        """
        # 创建后代
        child = Organism(f"child_of_{self.id}", self.position.copy())
        child.generation = self.generation + 1
        
        # 继承Tool结构
        for sensor in self.sensors.values():
            # 复制传感器，位置有小随机偏移
            new_sensor = type(sensor)(sensor.tool_id, sensor.position + random.uniform(-5, 5))
            child.add_sensor(new_sensor)
            
        for actuator in self.actuators.values():
            # 复制执行器，位置有小随机偏移
            new_actuator = type(actuator)(actuator.tool_id, actuator.position + random.uniform(-5, 5))
            child.add_actuator(new_actuator)
            
        # 继承连接
        for connection in self.connections:
            child.connect_tools(connection.source.tool_id, connection.target.tool_id, connection.weight)
            
        # 记忆继承
        all_memories = list(self.inherited_memories.values()) + list(self.learned_memories.values())
        for memory in all_memories:
            # 记忆强度决定遗传概率
            if random.random() < memory.strength:
                inherited_memory = MemoryGene(
                    memory.situation,
                    memory.action_pattern.copy(),
                    memory.success_rate
                )
                inherited_memory.mutate()  # 记忆变异
                child.inherited_memories[memory.situation] = inherited_memory
                
        return child
    
    def update(self, environment):
        """每帧更新
        
        执行AI生命体的完整生命周期，包括环境感知、决策、行动、学习和更新。
        
        参数:
            environment - 环境对象
        """
        self.age += 1
        
        # 更新细胞膜位置
        self.membrane.position = self.position
        
        # 感知环境，生成情境描述
        situation = self.perceive_environment(environment)
        
        # 收集传感器值
        sensor_values = {}
        for sensor_id, sensor in self.sensors.items():
            sensor_value = sensor.sense(environment, self.position)
            sensor_values[sensor_id] = sensor_value
            # 处理传感器信号
            sensor.process(sensor_value)
        
        # 信号传递：传感器向连接的目标传递信号
        for sensor in self.sensors.values():
            sensor.transmit_signals()
        
        # 决策：根据是否使用中枢控制选择不同的决策方式
        if self.uses_central_control:
            # 使用中枢控制（学习算法）
            controls = self.use_central_control(sensor_values)
        else:
            # 直接反射（传统连接机制）
            controls = self.use_reflex(sensor_values)
        
        # 执行动作
        old_position = self.position.copy()
        self.apply_controls(controls)
        
        # 信号传递：执行器向连接的目标传递信号
        for actuator in self.actuators.values():
            actuator.transmit_signals()
        
        # 学习：根据是否使用中枢控制选择不同的学习方式
        success = self.evaluate_success(old_position, environment)
        if self.uses_central_control:
            # 使用强化学习
            for central_brain in self.central_managers.values():
                # 计算奖励
                reward = central_brain.calculate_reward(self, environment)
                # 学习
                central_brain.learn(reward)
            # 传统中枢学习
            self.central_learn(sensor_values, controls, success)
        else:
            # 传统学习
            self.learn_from_experience(situation, controls, success)
        
        # 更新所有Tool
        for sensor in self.sensors.values():
            sensor.update()
        
        for actuator in self.actuators.values():
            actuator.update()
        
        for central_brain in self.central_managers.values():
            central_brain.update()
        
        # 更新所有连接
        for connection in self.connections:
            connection.update()
        
        # 记录当前状态用于调试
        self.current_situation = situation
        
        # 记忆衰减 - 分开处理，避免重复创建列表
        # 使用列表副本避免修改字典时迭代问题
        for situation in list(self.inherited_memories.keys()):
            memory = self.inherited_memories[situation]
            memory.decay()
        
        # 优化学习记忆衰减
        for situation in list(self.learned_memories.keys()):
            memory = self.learned_memories[situation]
            memory.decay()
            # 如果记忆强度过低，移除它
            if memory.strength < 0.05:
                del self.learned_memories[situation]
    
    def use_central_control(self, sensor_values: dict) -> Dict[str, float]:
        """使用中枢管理器做决策
        
        整合所有中枢管理器的控制信号，并结合直接反射信号，
        生成最终的控制信号。
        
        参数:
            sensor_values: dict - 传感器值字典
        
        返回:
            Dict[str, float] - 控制信号字典
        """
        central_controls = {}
        
        # 整合所有中枢管理器的控制信号
        for brain in self.central_managers.values():
            brain_controls = brain.generate_control_signals(sensor_values)
            # 合并控制信号，相同执行器取平均值
            for actuator_id, signal in brain_controls.items():
                if actuator_id not in central_controls:
                    central_controls[actuator_id] = []
                central_controls[actuator_id].append(signal)
        
        # 计算平均值
        for actuator_id in central_controls:
            central_controls[actuator_id] = sum(central_controls[actuator_id]) / len(central_controls[actuator_id])
        
        # 补充直接反射信号（中枢控制优先级更高）
        reflex_controls = self.use_reflex(sensor_values)
        for actuator_id in reflex_controls:
            if actuator_id not in central_controls:
                central_controls[actuator_id] = reflex_controls[actuator_id]
        
        return central_controls
    
    def use_reflex(self, sensor_values: dict) -> Dict[str, float]:
        """直接反射决策：基于连接的直接信号传递
        
        遍历所有传感器到执行器的连接，直接传递信号，
        生成控制信号。
        
        参数:
            sensor_values: dict - 传感器值字典
        
        返回:
            Dict[str, float] - 控制信号字典
        """
        controls = {}
        
        # 遍历所有连接，传递信号
        for connection in self.connections:
            if isinstance(connection.source, SensorTool) and isinstance(connection.target, ActuatorTool):
                sensor_id = connection.source.tool_id
                actuator_id = connection.target.tool_id
                
                if sensor_id in sensor_values:
                    # 计算控制信号：传感器值 * 连接权重
                    signal = sensor_values[sensor_id] * connection.weight
                    
                    if actuator_id not in controls:
                        controls[actuator_id] = 0.0
                    controls[actuator_id] += signal
        
        # 归一化控制信号到[-1, 1]范围
        for actuator_id in controls:
            controls[actuator_id] = max(-1.0, min(1.0, controls[actuator_id]))
        
        return controls
    
    def communicate(self, other_cell) -> bool:
        """与其他细胞通信
        
        通过细胞膜与其他细胞进行通信，交换信息。
        
        参数:
            other_cell - 其他细胞对象
        
        返回:
            bool - 通信是否成功
        """
        return self.membrane.cell_to_cell_communication(other_cell)
    
    def ingest_food(self, food_objects):
        """自动吞噬食物
        
        通过细胞膜自动吞噬附近的食物，并增加能量。
        
        参数:
            food_objects - 食物对象列表
        
        返回:
            remaining_food - 未被吞噬的食物对象列表
        """
        remaining_food, ingested_food = self.membrane.auto_ingest(food_objects)
        
        # 处理吞噬的食物，增加能量
        for food in ingested_food:
            self.energy += food.energy_value if hasattr(food, 'energy_value') else 10.0
        
        return remaining_food
    
    def central_learn(self, sensor_values: dict, controls: Dict[str, float], success: bool):
        """使用中枢管理器学习
        
        让所有中枢管理器学习传感器-执行器关联。
        
        参数:
            sensor_values: dict - 传感器值字典
            controls: Dict[str, float] - 控制信号字典
            success: bool - 行动是否成功
        """
        for brain in self.central_managers.values():
            # 学习所有传感器-执行器关联
            for sensor_id in sensor_values:
                for actuator_id in controls:
                    brain.learn_association(sensor_id, actuator_id, success)
    
    def evaluate_success(self, old_position: np.ndarray, environment) -> bool:
        """评估行动是否成功
        
        基于当前状态评估行动是否成功。
        
        参数:
            old_position: np.ndarray - 行动前的位置
            environment - 环境对象
        
        返回:
            bool - 行动是否成功
        """
        # 简化评估：如果能量增加或靠近食物则成功
        food_nearby = len(environment.get_nearby_food(self.position, 50)) > 0
        energy_increased = self.energy > 50
        return food_nearby or energy_increased
    
    def draw(self, surface):
        """绘制生物体 - 优化版
        
        在指定表面上绘制AI生命体，包括细胞膜、传感器、执行器、
        中枢管理器和它们之间的连接。
        
        参数:
            surface - 绘制表面
        """
        # 绘制细胞膜（只显示为环）
        x, y = int(self.position[0]), int(self.position[1])
        
        # 只绘制可见区域内的内容，优化性能
        screen_rect = surface.get_rect()
        organism_rect = pygame.Rect(x - self.radius * 2, y - self.radius * 2, 
                                  self.radius * 4, self.radius * 4)
        if not screen_rect.colliderect(organism_rect):
            return
        
        # 绘制细胞膜外环
        pygame.draw.circle(surface, (100, 150, 255), (x, y), self.radius, 2)
        
        # 预先计算坐标，减少重复计算
        tool_positions = {}
        
        # 绘制传感器
        for sensor in self.sensors.values():
            tool_x = x + int(sensor.position[0])
            tool_y = y + int(sensor.position[1])
            tool_positions[sensor] = (tool_x, tool_y)
            # 直接绘制，不修改原始位置
            sensor.draw_at_position(surface, (tool_x, tool_y))
            
        # 绘制执行器
        for actuator in self.actuators.values():
            tool_x = x + int(actuator.position[0])
            tool_y = y + int(actuator.position[1])
            tool_positions[actuator] = (tool_x, tool_y)
            # 直接绘制，不修改原始位置
            actuator.draw_at_position(surface, (tool_x, tool_y))
            
        # 绘制中枢管理器
        for central_brain in self.central_managers.values():
            tool_x = x + int(central_brain.position[0])
            tool_y = y + int(central_brain.position[1])
            tool_positions[central_brain] = (tool_x, tool_y)
            # 直接绘制，不修改原始位置
            central_brain.draw_at_position(surface, (tool_x, tool_y))
            
        # 绘制连接
        for connection in self.connections:
            # 获取源和目标位置
            source_pos = tool_positions.get(connection.source, (x, y))
            target_pos = tool_positions.get(connection.target, (x, y))
            
            # 根据权重决定颜色和宽度
            if connection.weight > 0:
                color = (100, 100, 255)  # 兴奋性连接 - 蓝色
            else:
                color = (255, 100, 100)  # 抑制性连接 - 红色
                
            line_width = max(1, int(2 * abs(connection.weight)))
            pygame.draw.line(surface, color, source_pos, target_pos, line_width)
            
            # 简化信号传递效果，只在连接活跃时绘制
            if connection.signal_active:
                # 优化：减少计算，使用简单的闪烁效果
                current_time = pygame.time.get_ticks()
                if current_time % 60 < 30:  # 每60毫秒闪烁一次
                    # 只绘制一个点，不使用动态效果
                    mid_x = (source_pos[0] + target_pos[0]) // 2
                    mid_y = (source_pos[1] + target_pos[1]) // 2
                    pygame.draw.circle(surface, (255, 255, 255), (mid_x, mid_y), 2)