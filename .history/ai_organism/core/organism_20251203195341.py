"""生物体实现"""

from typing import Dict, List, Tuple, Optional
import random
import numpy as np
import pygame
from ..tools import (
    TouchSensor, LightSensor, MuscleActuator, CiliaActuator, Connection,
    SensorTool, ActuatorTool, MembraneTool, CentralBrainTool
)
from .memory import MemoryGene


class Organism:
    """生物体 - 包含Tool系统和记忆继承"""
    
    def __init__(self, organism_id: str, position: Tuple[float, float]):
        self.id = organism_id
        self.position = np.array(position, dtype=float)
        self.velocity = np.array([0.0, 0.0])
        self.energy = 100.0
        self.age = 0
        self.generation = 0
        
        # 细胞膜 - 作为细胞边界
        self.membrane = MembraneTool(f"{organism_id}_membrane", self.position, 30)
        
        # Tool系统
        self.sensors: Dict[str, SensorTool] = {}
        self.actuators: Dict[str, ActuatorTool] = {}
        self.central_brains: Dict[str, CentralBrainTool] = {}  # 中枢管理器集合
        self.connections: List[Connection] = []
        
        # 记忆系统
        self.memory_bank: List[MemoryGene] = []  # 遗传记忆
        self.learned_memories: List[MemoryGene] = []  # 学习记忆
        
        # AI控制状态
        self.current_action = "explore"
        self.control_signals: Dict[str, float] = {}  # 当前控制信号
        self.has_central_control = False  # 是否有中枢控制
        
        # 外观
        self.color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        self.radius = self.membrane.radius
        
    def add_sensor(self, sensor: SensorTool):
        """添加传感器，确保位于细胞膜内"""
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(sensor.position + self.position):
            self.sensors[sensor.tool_id] = sensor
        
    def add_actuator(self, actuator: ActuatorTool):
        """添加效应器，确保位于细胞膜内"""
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(actuator.position + self.position):
            self.actuators[actuator.tool_id] = actuator
            self.control_signals[actuator.tool_id] = 0.0
    
    def add_central_brain(self, central_brain: CentralBrainTool):
        """添加中枢管理器，确保位于细胞膜内"""
        # 验证位置是否在细胞膜内
        if self.membrane.is_inside(central_brain.position + self.position):
            self.central_brains[central_brain.tool_id] = central_brain
            self.has_central_control = True
        
    def connect_tools(self, source_id: str, target_id: str, weight: float = 1.0, is_bidirectional: bool = False):
        """连接两个Tool"""
        # 查找源Tool（可以是传感器、效应器或中枢）
        source = (self.sensors.get(source_id) or 
                 self.actuators.get(source_id) or 
                 self.central_brains.get(source_id))
        
        # 查找目标Tool（可以是传感器、效应器或中枢）
        target = (self.sensors.get(target_id) or 
                 self.actuators.get(target_id) or 
                 self.central_brains.get(target_id))
        
        if source and target:
            connection = Connection(source, target, weight, is_bidirectional)
            self.connections.append(connection)
            source.connections.append(connection)
            if is_bidirectional:
                target.connections.append(connection)
            
    def perceive_environment(self, environment) -> str:
        """感知环境，返回情境描述"""
        perceptions = []
        
        # 传感器感知
        for sensor in self.sensors.values():
            sensor_value = sensor.sense(environment, self.position)
            # 只添加有意义的感知（>0.1），减少后续处理量
            if sensor_value > 0.5:
                perceptions.append(f"{sensor.get_icon()}_high")
            elif sensor_value > 0.1:
                perceptions.append(f"{sensor.get_icon()}_low")
        
        # 内部状态 - 限制条件数量
        if self.energy < 30:
            perceptions.append("low_energy")
        if self.age > 200:
            perceptions.append("old")
        
        # 使用集合去重，避免重复感知
        perceptions = list(set(perceptions))
        return "_".join(perceptions) if perceptions else "neutral"
    
    def decide_action(self, situation: str) -> Dict[str, float]:
        """基于记忆决定控制信号"""
        situation_tags = set(situation.split("_"))
        if not situation_tags:
            return self._random_control()
        
        # 合并记忆列表，避免重复创建列表
        all_memories = self.memory_bank + self.learned_memories
        if not all_memories:
            return self._random_control()
        
        # 更高效的记忆匹配 - 使用集合交集
        relevant_memories = []
        for memory in all_memories:
            memory_tags = set(memory.situation.split("_"))
            if memory_tags.intersection(situation_tags):
                relevant_memories.append(memory)
        
        if not relevant_memories:
            # 无记忆，随机探索
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
        """生成随机控制信号"""
        controls = {}
        for actuator_id in self.actuators:
            controls[actuator_id] = random.uniform(-1, 1)
        return controls
        
    def apply_controls(self, controls: Dict[str, float]):
        """应用控制信号到效应器"""
        total_force = np.array([0.0, 0.0])
        
        for actuator_id, control_signal in controls.items():
            if actuator_id in self.actuators:
                actuator = self.actuators[actuator_id]
                force = actuator.apply_force(control_signal)
                total_force += force
                self.control_signals[actuator_id] = control_signal
                
        # 应用物理
        self.velocity = total_force * 0.1
        self.position += self.velocity
        
        # 能量消耗
        energy_cost = sum(abs(signal) for signal in controls.values()) * 0.1
        self.energy -= energy_cost
        
    def learn_from_experience(self, situation: str, controls: Dict[str, float], success: bool):
        """从经验中学习"""
        # 寻找类似记忆
        for memory in self.learned_memories:
            if memory.situation == situation:
                # 强化或削弱现有记忆
                if memory.success_rate > 0.5 and success:
                    memory.strength = min(1.0, memory.strength + 0.1)
                elif memory.success_rate < 0.5 and not success:
                    memory.strength = min(1.0, memory.strength + 0.1)
                else:
                    memory.strength = max(0.1, memory.strength - 0.2)
                return
                
        # 创建新记忆
        new_memory = MemoryGene(situation, controls.copy(), 1.0 if success else 0.0)
        self.learned_memories.append(new_memory)
        
    def reproduce(self) -> 'Organism':
        """繁殖后代"""
        child = Organism(f"child_of_{self.id}", self.position.copy())
        child.generation = self.generation + 1
        
        # 继承Tool结构
        for sensor in self.sensors.values():
            new_sensor = type(sensor)(sensor.tool_id, sensor.position + random.uniform(-5, 5))
            child.add_sensor(new_sensor)
            
        for actuator in self.actuators.values():
            new_actuator = type(actuator)(actuator.tool_id, actuator.position + random.uniform(-5, 5))
            child.add_actuator(new_actuator)
            
        # 继承连接
        for connection in self.connections:
            child.connect_tools(connection.source.tool_id, connection.target.tool_id, connection.weight)
            
        # 记忆继承
        all_memories = self.memory_bank + self.learned_memories
        for memory in all_memories:
            if random.random() < memory.strength:
                inherited_memory = MemoryGene(
                    memory.situation,
                    memory.action_pattern.copy(),
                    memory.success_rate
                )
                inherited_memory.mutate()
                child.memory_bank.append(inherited_memory)
                
        return child
    
    def update(self, environment):
        """每帧更新"""
        self.age += 1
        
        # 更新细胞膜位置
        self.membrane.position = self.position
        
        # 感知环境
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
        
        # 决策：根据是否有中枢控制选择不同的决策方式
        if self.has_central_control:
            # 使用中枢控制（学习算法）
            controls = self._central_control_decision(sensor_values)
        else:
            # 直接反射（传统连接机制）
            controls = self._reflex_decision(sensor_values)
        
        # 执行
        old_position = self.position.copy()
        self.apply_controls(controls)
        
        # 信号传递：效应器向连接的目标传递信号
        for actuator in self.actuators.values():
            actuator.transmit_signals()
        
        # 学习：仅中枢控制时使用中枢管理器的学习机制
        success = self._evaluate_success(old_position, environment)
        if self.has_central_control:
            # 使用中枢管理器学习
            self._central_learn(sensor_values, controls, success)
        else:
            # 传统学习
            self.learn_from_experience(situation, controls, success)
        
        # 更新所有Tool
        for sensor in self.sensors.values():
            sensor.update()
        
        for actuator in self.actuators.values():
            actuator.update()
        
        for central_brain in self.central_brains.values():
            central_brain.update()
        
        # 更新所有连接
        for connection in self.connections:
            connection.update()
        
        # 记忆衰减 - 分开处理，避免重复创建列表
        for memory in self.memory_bank:
            memory.decay()
        
        # 优化学习记忆衰减
        for memory in list(self.learned_memories):  # 使用副本避免修改时迭代问题
            memory.decay()
            # 如果记忆强度过低，移除它
            if memory.strength < 0.05:
                self.learned_memories.remove(memory)
    
    def _central_control_decision(self, sensor_values: dict) -> Dict[str, float]:
        """使用中枢管理器做决策"""
        central_controls = {}
        
        # 整合所有中枢管理器的控制信号
        for brain in self.central_brains.values():
            brain_controls = brain.generate_control_signals(sensor_values)
            # 合并控制信号，相同效应器取平均值
            for actuator_id, signal in brain_controls.items():
                if actuator_id not in central_controls:
                    central_controls[actuator_id] = []
                central_controls[actuator_id].append(signal)
        
        # 计算平均值
        for actuator_id in central_controls:
            central_controls[actuator_id] = sum(central_controls[actuator_id]) / len(central_controls[actuator_id])
        
        # 补充直接反射信号（中枢控制优先级更高）
        reflex_controls = self._reflex_decision(sensor_values)
        for actuator_id in reflex_controls:
            if actuator_id not in central_controls:
                central_controls[actuator_id] = reflex_controls[actuator_id]
        
        return central_controls
    
    def _reflex_decision(self, sensor_values: dict) -> Dict[str, float]:
        """直接反射决策：基于连接的直接信号传递"""
        controls = {}
        
        # 遍历所有连接，传递信号
        for connection in self.connections:
            if isinstance(connection.source, SensorTool) and isinstance(connection.target, ActuatorTool):
                sensor_id = connection.source.tool_id
                actuator_id = connection.target.tool_id
                
                if sensor_id in sensor_values:
                    # 计算控制信号
                    signal = sensor_values[sensor_id] * connection.weight
                    
                    if actuator_id not in controls:
                        controls[actuator_id] = 0.0
                    controls[actuator_id] += signal
        
        # 归一化控制信号
        for actuator_id in controls:
            controls[actuator_id] = max(-1.0, min(1.0, controls[actuator_id]))
        
        return controls
    
    def _central_learn(self, sensor_values: dict, controls: Dict[str, float], success: bool):
        """使用中枢管理器学习"""
        for brain in self.central_brains.values():
            # 学习所有传感器-效应器关联
            for sensor_id in sensor_values:
                for actuator_id in controls:
                    brain.learn_association(sensor_id, actuator_id, success)
    
    def _evaluate_success(self, old_position: np.ndarray, environment) -> bool:
        """评估行动是否成功"""
        # 简化评估：如果能量增加或靠近食物则成功
        food_nearby = len(environment.get_nearby_food(self.position, 50)) > 0
        energy_increased = self.energy > 50
        return food_nearby or energy_increased
    
    def draw(self, surface):
        """绘制生物体"""
        # 绘制主体
        x, y = int(self.position[0]), int(self.position[1])
        pygame.draw.circle(surface, self.color, (x, y), self.radius)
        pygame.draw.circle(surface, (0, 0, 0), (x, y), self.radius, 2)
        
        # 绘制所有Tool（相对于生物体位置）
        # 先绘制所有Tool，不修改它们的原始位置
        for sensor in self.sensors.values():
            tool_x = x + int(sensor.position[0])
            tool_y = y + int(sensor.position[1])
            # 保存原始位置
            original_pos = sensor.position.copy()
            # 设置世界坐标
            sensor.position = np.array([tool_x, tool_y])
            sensor.draw(surface)
            # 恢复原始位置
            sensor.position = original_pos
            
        for actuator in self.actuators.values():
            tool_x = x + int(actuator.position[0])
            tool_y = y + int(actuator.position[1])
            # 保存原始位置
            original_pos = actuator.position.copy()
            # 设置世界坐标
            actuator.position = np.array([tool_x, tool_y])
            actuator.draw(surface)
            # 恢复原始位置
            actuator.position = original_pos
            
        # 直接绘制连接，不修改连接的原始位置
        for connection in self.connections:
            # 计算世界坐标
            source_x = x + int(connection.source.position[0])
            source_y = y + int(connection.source.position[1])
            target_x = x + int(connection.target.position[0])
            target_y = y + int(connection.target.position[1])
            
            # 直接绘制连接，不修改原始连接的位置
            # 根据权重决定颜色和宽度
            if connection.weight > 0:
                color = (100, 100, 255)  # 兴奋性连接 - 蓝色
            else:
                color = (255, 100, 100)  # 抑制性连接 - 红色
                
            line_width = max(1, int(2 * abs(connection.weight)))
            pygame.draw.line(surface, color, (source_x, source_y), (target_x, target_y), line_width)
            
            # 简化信号传递效果，只在连接活跃时绘制
            if connection.signal_active:
                progress = (pygame.time.get_ticks() // 30) % 100 / 100.0
                pulse_x = int(source_x + (target_x - source_x) * progress)
                pulse_y = int(source_y + (target_y - source_y) * progress)
                pygame.draw.circle(surface, (255, 255, 255), (pulse_x, pulse_y), 3)
