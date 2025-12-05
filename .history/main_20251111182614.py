import pygame
import numpy as np
import random
import math
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# 初始化Pygame
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tool继承算法模拟器")
clock = pygame.time.Clock()
font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 100, 100)
GREEN = (100, 255, 100) 
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)
PURPLE = (200, 100, 200)
ORANGE = (255, 150, 50)
CYAN = (100, 255, 255)

class Tool:
    """Tool基类 - 所有具体Tool的父类"""
    
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        self.tool_id = tool_id
        self.position = np.array(position, dtype=float)
        self.connections = []  # 连接的Tool
        self.activation = 0.0
        self.state = "idle"  # 状态标识
        
        # 遗传特性
        self.genetic_strength = 1.0
        self.mutation_rate = 0.1
        
    def process(self, input_value: float) -> Optional[float]:
        """处理输入，返回输出值"""
        raise NotImplementedError("子类必须实现process方法")
        
    def update(self):
        """每帧更新"""
        pass
        
    def mutate(self):
        """变异"""
        if random.random() < self.mutation_rate:
            self.genetic_strength = np.clip(self.genetic_strength + random.gauss(0, 0.1), 0.5, 2.0)
            
    def draw(self, surface):
        """绘制Tool"""
        raise NotImplementedError("子类必须实现draw方法")
        
    def get_icon(self):
        """获取Tool类型图标"""
        raise NotImplementedError("子类必须实现get_icon方法")

class SensorTool(Tool):
    """传感器Tool基类"""
    def __init__(self, tool_id: str, position: Tuple[float, float], sense_range: float):
        super().__init__(tool_id, position)
        self.sense_range = sense_range
        self.sensed_value = 0.0
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值"""
        raise NotImplementedError("传感器子类必须实现sense方法")

class ActuatorTool(Tool):
    """效应器Tool基类"""
    def __init__(self, tool_id: str, position: Tuple[float, float], force_strength: float):
        super().__init__(tool_id, position)
        self.force_strength = force_strength
        self.current_force = 0.0
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量"""
        raise NotImplementedError("效应器子类必须实现apply_force方法")

# ==================== 具体Tool实现 ====================

class TouchSensor(SensorTool):
    """触觉传感器 - 检测接触"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, sense_range=15)
        
    def sense(self, environment, organism_position) -> float:
        world_pos = organism_position + self.position
        contact_info = environment.check_contact(world_pos, self.sense_range)
        self.sensed_value = contact_info["pressure"]
        return self.sensed_value
        
    def process(self, input_value: float) -> Optional[float]:
        return self.sensed_value
        
    def draw(self, surface):
        x, y = int(self.position[0]), int(self.position[1])
        color = GREEN if self.activation > 0 else (50, 150, 50)
        
        # 触觉传感器图标 - 波纹状
        pygame.draw.circle(surface, color, (x, y), 12)
        
        # 激活时的波纹效果
        if self.activation > 0.3:
            wave_radius = int(12 + 8 * self.activation)
            pygame.draw.circle(surface, (100, 255, 100, 100), (x, y), wave_radius, 2)
            
    def get_icon(self):
        return "TOUCH"

class LightSensor(SensorTool):
    """光感传感器 - 检测光线"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, sense_range=80)
        
    def sense(self, environment, organism_position) -> float:
        world_pos = organism_position + self.position
        light_level = environment.get_light_intensity(world_pos)
        self.sensed_value = light_level
        return self.sensed_value
        
    def process(self, input_value: float) -> Optional[float]:
        return self.sensed_value
        
    def draw(self, surface):
        x, y = int(self.position[0]), int(self.position[1])
        color = YELLOW if self.activation > 0 else (150, 150, 50)
        
        # 光感传感器图标 - 太阳状
        pygame.draw.circle(surface, color, (x, y), 10)
        
        # 光线效果
        for i in range(8):
            angle = i * math.pi / 4
            end_x = x + 15 * math.cos(angle)
            end_y = y + 15 * math.sin(angle)
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)
            
    def get_icon(self):
        return "LIGHT"

class MuscleActuator(ActuatorTool):
    """肌肉效应器 - 收缩产生力"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, force_strength=8.0)
        self.contraction = 0.0  # 收缩程度 0-1
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        self.contraction = np.clip(control_signal, 0, 1)
        self.current_force = self.contraction * self.force_strength
        
        # 肌肉产生的力方向垂直于其位置向量（简化模型）
        force_dir = np.array([-self.position[1], self.position[0]])
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)
            
        return force_dir * self.current_force
        
    def process(self, input_value: float) -> Optional[float]:
        # 肌肉不处理输入，只响应控制信号
        return None
        
    def draw(self, surface):
        x, y = int(self.position[0]), int(self.position[1])
        
        # 根据收缩程度改变颜色
        base_red = 150 + int(105 * self.contraction)
        color = (base_red, 50, 50) if self.contraction > 0 else (150, 50, 50)
        
        # 肌肉图标 - 条状，收缩时变短变粗
        length = 20 - 8 * self.contraction
        width = 8 + 4 * self.contraction
        
        # 绘制肌肉纤维
        angle = math.atan2(self.position[1], self.position[0])
        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        
        # 绘制肌肉主体
        pygame.draw.line(surface, color, (x, y), (end_x, end_y), int(width))
        
        # 收缩时的纹理
        if self.contraction > 0.3:
            for i in range(3):
                progress = (i + 1) / 4
                mid_x = x + progress * length * math.cos(angle)
                mid_y = y + progress * length * math.sin(angle)
                perp_x = -math.sin(angle) * width * 0.3
                perp_y = math.cos(angle) * width * 0.3
                pygame.draw.line(surface, (200, 100, 100), 
                               (mid_x - perp_x, mid_y - perp_y),
                               (mid_x + perp_x, mid_y + perp_y), 2)
            
    def get_icon(self):
        return "MUSCLE"

class CiliaActuator(ActuatorTool):
    """纤毛效应器 - 摆动产生推进力"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, force_strength=4.0)
        self.swing_phase = 0.0  # 摆动相位
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        self.swing_phase = (self.swing_phase + control_signal * 0.1) % (2 * math.pi)
        self.current_force = control_signal * self.force_strength
        
        # 纤毛产生的力方向与其位置方向相反（推进）
        force_dir = -self.position
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)
            
        return force_dir * self.current_force
        
    def process(self, input_value: float) -> Optional[float]:
        return None
        
    def draw(self, surface):
        x, y = int(self.position[0]), int(self.position[1])
        color = CYAN if self.current_force > 0 else (50, 150, 150)
        
        # 纤毛图标 - 波浪状
        base_angle = math.atan2(self.position[1], self.position[0])
        swing_angle = base_angle + math.sin(self.swing_phase) * 0.5
        
        # 绘制纤毛
        end_x = x + 25 * math.cos(swing_angle)
        end_y = y + 25 * math.sin(swing_angle)
        
        pygame.draw.line(surface, color, (x, y), (end_x, end_y), 3)
        
        # 摆动效果
        if self.current_force > 0:
            for i in range(3):
                phase_offset = i * 0.3
                local_phase = self.swing_phase + phase_offset
                local_angle = base_angle + math.sin(local_phase) * 0.3
                local_end_x = x + 20 * math.cos(local_angle)
                local_end_y = y + 20 * math.sin(local_angle)
                pygame.draw.line(surface, (100, 200, 200), (x, y), (local_end_x, local_end_y), 1)
            
    def get_icon(self):
        return "CILIA"

class Connection:
    """Tool之间的连接"""
    def __init__(self, source: Tool, target: Tool, weight: float = 1.0):
        self.source = source
        self.target = target
        self.weight = weight
        self.signal_active = False
        
    def draw(self, surface):
        start_pos = self.source.position.astype(int)
        end_pos = self.target.position.astype(int)
        
        # 根据权重决定颜色和宽度
        if self.weight > 0:
            color = (100, 100, 255)  # 兴奋性连接 - 蓝色
        else:
            color = (255, 100, 100)  # 抑制性连接 - 红色
            
        line_width = max(1, int(2 * abs(self.weight)))
        pygame.draw.line(surface, color, start_pos, end_pos, line_width)
        
        # 信号传递效果
        if self.signal_active:
            progress = (pygame.time.get_ticks() // 30) % 100 / 100.0
            pulse_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            pulse_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
            pygame.draw.circle(surface, WHITE, (pulse_x, pulse_y), 3)

class MemoryGene:
    """记忆基因 - 用于继承算法"""
    def __init__(self, situation: str, action_pattern: Dict[str, float], success_rate: float):
        self.situation = situation  # 触发情境
        self.action_pattern = action_pattern  # 动作模式 {tool_id: 控制信号}
        self.success_rate = success_rate  # 成功率
        self.strength = 1.0  # 记忆强度
        self.age = 0
        
    def mutate(self):
        """记忆变异"""
        if random.random() < 0.1:
            # 动作模式微调
            for tool_id in self.action_pattern:
                if random.random() < 0.3:
                    self.action_pattern[tool_id] = np.clip(
                        self.action_pattern[tool_id] + random.gauss(0, 0.1), -1, 1
                    )
                    
    def decay(self):
        """记忆衰减"""
        self.age += 1
        self.strength *= 0.99

class Organism:
    """生物体 - 包含Tool系统和记忆继承"""
    
    def __init__(self, organism_id: str, position: Tuple[float, float]):
        self.id = organism_id
        self.position = np.array(position, dtype=float)
        self.velocity = np.array([0.0, 0.0])
        self.energy = 100.0
        self.age = 0
        self.generation = 0
        
        # Tool系统
        self.sensors: Dict[str, SensorTool] = {}
        self.actuators: Dict[str, ActuatorTool] = {}
        self.connections: List[Connection] = []
        
        # 记忆系统
        self.memory_bank: List[MemoryGene] = []  # 遗传记忆
        self.learned_memories: List[MemoryGene] = []  # 学习记忆
        
        # AI控制状态
        self.current_action = "explore"
        self.control_signals: Dict[str, float] = {}  # 当前控制信号
        
        # 外观
        self.color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        self.radius = 30
        
    def add_sensor(self, sensor: SensorTool):
        """添加传感器"""
        self.sensors[sensor.tool_id] = sensor
        
    def add_actuator(self, actuator: ActuatorTool):
        """添加效应器"""
        self.actuators[actuator.tool_id] = actuator
        self.control_signals[actuator.tool_id] = 0.0
        
    def connect_tools(self, source_id: str, target_id: str, weight: float = 1.0):
        """连接两个Tool"""
        source = self.sensors.get(source_id) or self.actuators.get(source_id)
        target = self.sensors.get(target_id) or self.actuators.get(target_id)
        
        if source and target:
            connection = Connection(source, target, weight)
            self.connections.append(connection)
            source.connections.append(connection)
            
    def perceive_environment(self, environment) -> str:
        """感知环境，返回情境描述"""
        perceptions = []
        
        # 传感器感知
        for sensor in self.sensors.values():
            sensor_value = sensor.sense(environment, self.position)
            if sensor_value > 0.5:
                perceptions.append(f"{sensor.get_icon()}_high")
            elif sensor_value > 0.1:
                perceptions.append(f"{sensor.get_icon()}_low")
                
        # 内部状态
        if self.energy < 30:
            perceptions.append("low_energy")
        if self.age > 200:
            perceptions.append("old")
            
        return "_".join(perceptions) if perceptions else "neutral"
    
    def decide_action(self, situation: str) -> Dict[str, float]:
        """基于记忆决定控制信号"""
        # 检索相关记忆
        relevant_memories = [m for m in self.memory_bank + self.learned_memories 
                           if any(s in m.situation for s in situation.split("_"))]
        
        if not relevant_memories:
            # 无记忆，随机探索
            return self._random_control()
            
        # 选择最佳记忆
        best_memory = max(relevant_memories, key=lambda m: m.success_rate * m.strength)
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
        # 更新成功率
        success_adjust = 0.1 if success else -0.1
        
        for memory in self.learned_memories:
            if memory.situation == situation:
                memory.success_rate = np.clip(memory.success_rate + success_adjust, 0, 1)
                memory.strength = min(1.0, memory.strength + 0.05)
                return
                
        # 创建新记忆
        new_memory = MemoryGene(situation, controls.copy(), 
                               success_rate=1.0 if success else 0.0)
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
        """更新生物状态"""
        self.age += 1
        
        # 感知环境
        situation = self.perceive_environment(environment)
        
        # 决策
        controls = self.decide_action(situation)
        
        # 执行
        old_position = self.position.copy()
        self.apply_controls(controls)
        
        # 学习
        success = self._evaluate_success(old_position, environment)
        self.learn_from_experience(situation, controls, success)
        
        # 记忆衰减
        for memory in self.memory_bank + self.learned_memories:
            memory.decay()
            
    def _evaluate_success(self, old_position: np.ndarray, environment) -> bool:
        """评估行动是否成功"""
        # 简化评估：如果能量增加或靠近食物则成功
        return self.energy > 50 or random.random() < 0.7
        
    def draw(self, surface):
        """绘制生物体"""
        # 绘制主体
        x, y = int(self.position[0]), int(self.position[1])
        pygame.draw.circle(surface, self.color, (x, y), self.radius)
        pygame.draw.circle(surface, BLACK, (x, y), self.radius, 2)
        
        # 绘制所有Tool（相对于生物体位置）
        for sensor in self.sensors.values():
            tool_pos = (x + sensor.position[0], y + sensor.position[1])
            original_pos = sensor.position.copy()
            sensor.position = np.array(tool_pos)
            sensor.draw(surface)
            sensor.position = original_pos
            
        for actuator in self.actuators.values():
            tool_pos = (x + actuator.position[0], y + actuator.position[1])
            original_pos = actuator.position.copy()
            actuator.position = np.array(tool_pos)
            actuator.draw(surface)
            actuator.position = original_pos
            
        # 绘制连接
        for connection in self.connections:
            source_pos = (x + connection.source.position[0], y + connection.source.position[1])
            target_pos = (x + connection.target.position[0], y + connection.target.position[1])
            
            original_source_pos = connection.source.position.copy()
            original_target_pos = connection.target.position.copy()
            
            connection.source.position = np.array(source_pos)
            connection.target.position = np.array(target_pos)
            connection.draw(surface)
            
            connection.source.position = original_source_pos
            connection.target.position = original_target_pos

class Environment:
    """简化环境"""
    def __init__(self):
        self.foods = []
        self.light_sources = []
        self.obstacles = []
        
    def add_food(self, position: Tuple[float, float]):
        self.foods.append({"position": np.array(position), "energy": 20})
        
    def add_light_source(self, position: Tuple[float, float], intensity: float = 1.0):
        self.light_sources.append({"position": np.array(position), "intensity": intensity})
        
    def add_obstacle(self, position: Tuple[float, float], radius: float):
        self.obstacles.append({"position": np.array(position), "radius": radius})
        
    def check_contact(self, position: np.ndarray, radius: float) -> Dict[str, any]:
        """检查接触"""
        for obstacle in self.obstacles:
            distance = np.linalg.norm(position - obstacle["position"])
            if distance < obstacle["radius"] + radius:
                direction = position - obstacle["position"]
                if np.linalg.norm(direction) > 0:
                    direction = direction / np.linalg.norm(direction)
                return {
                    "contacting": True,
                    "pressure": 1.0 - (distance / (obstacle["radius"] + radius)),
                    "direction": direction
                }
        return {"contacting": False, "pressure": 0.0, "direction": np.array([0.0, 0.0])}
    
    def get_light_intensity(self, position: np.ndarray) -> float:
        """获取光线强度"""
        if not self.light_sources:
            return 0.0
            
        total_intensity = 0.0
        for light in self.light_sources:
            distance = np.linalg.norm(position - light["position"])
            intensity = light["intensity"] / (1 + distance * 0.1)  # 距离衰减
            total_intensity += intensity
            
        return min(1.0, total_intensity)
    
    def consume_food(self, position: np.ndarray, radius: float) -> bool:
        """消耗食物"""
        for i, food in enumerate(self.foods):
            distance = np.linalg.norm(position - food["position"])
            if distance < radius:
                self.foods.pop(i)
                return True
        return False
    
    def get_nearby_food(self, position: np.ndarray, radius: float) -> List:
        """获取附近食物"""
        nearby = []
        for food in self.foods:
            distance = np.linalg.norm(position - food["position"])
            if distance < radius:
                nearby.append(food)
        return nearby
    
    def draw(self, surface):
        """绘制环境"""
        # 绘制食物
        for food in self.foods:
            pos = food["position"].astype(int)
            pygame.draw.circle(surface, (100, 200, 100), pos, 8)
            pygame.draw.circle(surface, (50, 150, 50), pos, 8, 2)
            
        # 绘制光源
        for light in self.light_sources:
            pos = light["position"].astype(int)
            # 光晕效果
            for radius in range(20, 5, -5):
                alpha = int(100 * (1 - radius / 20))
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 200, alpha), (radius, radius), radius)
                surface.blit(s, (pos[0]-radius, pos[1]-radius))
            pygame.draw.circle(surface, (255, 255, 100), pos, 5)
            
        # 绘制障碍物
        for obstacle in self.obstacles:
            pos = obstacle["position"].astype(int)
            pygame.draw.circle(surface, (100, 100, 100), pos, int(obstacle["radius"]))
            pygame.draw.circle(surface, (50, 50, 50), pos, int(obstacle["radius"]), 2)

class Simulation:
    """模拟器主类"""
    
    def __init__(self):
        self.organisms = []
        self.environment = Environment()
        self.selected_organism = None
        self.time = 0
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """设置测试环境"""
        # 添加食物
        for _ in range(15):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            self.environment.add_food((x, y))
            
        # 添加光源
        self.environment.add_light_source((WIDTH // 2, HEIGHT // 2), 2.0)
        self.environment.add_light_source((WIDTH // 4, HEIGHT // 4), 1.5)
        
        # 添加障碍物
        for _ in range(5):
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            self.environment.add_obstacle((x, y), random.randint(20, 40))
            
        # 创建初始生物
        self.create_test_organism()
        
    def create_test_organism(self):
        """创建测试生物"""
        org = Organism("org_1", (WIDTH // 2, HEIGHT // 2))
        
        # 添加传感器
        touch1 = TouchSensor("touch_1", (-20, 0))
        touch2 = TouchSensor("touch_2", (0, -20))
        light_sensor = LightSensor("light_1", (20, 0))
        
        org.add_sensor(touch1)
        org.add_sensor(touch2)
        org.add_sensor(light_sensor)
        
        # 添加效应器
        muscle1 = MuscleActuator("muscle_1", (-15, 15))
        muscle2 = MuscleActuator("muscle_2", (15, 15))
        muscle3 = MuscleActuator("muscle_3", (0, -15))
        cilia = CiliaActuator("cilia_1", (0, 20))
        
        org.add_actuator(muscle1)
        org.add_actuator(muscle2)
        org.add_actuator(muscle3)
        org.add_actuator(cilia)
        
        # 添加一些基础连接（非条件反射）
        org.connect_tools("touch_1", "muscle_1", 1.0)  # 左边碰到东西 -> 左边肌肉收缩
        org.connect_tools("touch_2", "muscle_3", 1.0)  # 上边碰到东西 -> 上边肌肉收缩
        org.connect_tools("light_1", "cilia_1", 0.8)   # 看到光 -> 纤毛运动
        
        # 添加基础记忆
        base_memory = MemoryGene(
            "LIGHT_high",
            {"cilia_1": 0.7, "muscle_1": 0.3, "muscle_2": 0.3},
            0.8
        )
        org.memory_bank.append(base_memory)
        
        self.organisms.append(org)
        self.selected_organism = org
        
    def update(self):
        """更新模拟"""
        self.time += 1
        
        # 更新所有生物
        for org in self.organisms[:]:  # 使用切片避免修改问题
            org.update(self.environment)
            
            # 检查繁殖条件
            if org.energy > 80 and random.random() < 0.01:
                child = org.reproduce()
                self.organisms.append(child)
                
            # 检查死亡
            if org.energy <= 0 or org.age > 1000:
                self.organisms.remove(org)
                if self.selected_organism == org:
                    self.selected_organism = None
                    
        # 偶尔添加新食物
        if random.random() < 0.02 and len(self.environment.foods) < 20:
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            self.environment.add_food((x, y))
            
    def handle_click(self, pos):
        """处理鼠标点击"""
        for org in self.organisms:
            distance = np.linalg.norm(org.position - pos)
            if distance < org.radius:
                self.selected_organism = org
                return
                
        # 点击空白处添加食物
        self.environment.add_food(pos)
        
    def draw(self, surface):
        """绘制整个模拟"""
        # 清屏
        surface.fill((20, 20, 30))
        
        # 绘制环境
        self.environment.draw(surface)
        
        # 绘制所有生物
        for org in self.organisms:
            org.draw(surface)
            
        # 高亮选中的生物
        if self.selected_organism:
            pos = self.selected_organism.position.astype(int)
            pygame.draw.circle(surface, WHITE, pos, 
                             self.selected_organism.radius + 5, 2)
            
            # 绘制选中生物的信息
            self.draw_organism_info(surface, self.selected_organism)
            
        # 绘制模拟信息
        self.draw_simulation_info(surface)
        
    def draw_organism_info(self, surface, org):
        """绘制选中生物的信息"""
        info_lines = [
            f"生物: {org.id}",
            f"世代: {org.generation}",
            f"能量: {org.energy:.1f}",
            f"年龄: {org.age}",
            f"行动: {org.current_action}",
            f"记忆数: {len(org.memory_bank)}遗传 + {len(org.learned_memories)}学习",
            f"传感器: {len(org.sensors)} 效应器: {len(org.actuators)}"
        ]
        
        # 绘制背景
        info_rect = pygame.Rect(10, 10, 250, len(info_lines) * 25 + 10)
        pygame.draw.rect(surface, (0, 0, 0, 180), info_rect)
        pygame.draw.rect(surface, WHITE, info_rect, 2)
        
        # 绘制文本
        for i, line in enumerate(info_lines):
            text = font.render(line, True, WHITE)
            surface.blit(text, (20, 15 + i * 25))
            
        # 绘制控制信号
        control_y = info_rect.bottom + 10
        if org.control_signals:
            control_text = font.render("控制信号:", True, WHITE)
            surface.blit(control_text, (20, control_y))
            
            for j, (tool_id, signal) in enumerate(org.control_signals.items()):
                signal_text = font.render(f"  {tool_id}: {signal:.2f}", True, 
                                        GREEN if signal > 0 else RED)
                surface.blit(signal_text, (20, control_y + 25 + j * 20))
                
    def draw_simulation_info(self, surface):
        """绘制模拟信息"""
        info_lines = [
            f"时间: {self.time}",
            f"生物数量: {len(self.organisms)}",
            f"食物数量: {len(self.environment.foods)}",
            "点击生物选择，点击空地添加食物"
        ]
        
        # 绘制在右上角
        for i, line in enumerate(info_lines):
            text = font.render(line, True, WHITE)
            surface.blit(text, (WIDTH - 250, 10 + i * 25))

def main():
    """主函数"""
    simulation = Simulation()
    running = True
    
    print("Tool继承算法模拟器启动!")
    print("功能说明:")
    print("- 绿色圆圈: 触觉传感器")
    print("- 黄色太阳: 光感传感器") 
    print("- 红色条状: 肌肉效应器")
    print("- 青色波浪: 纤毛效应器")
    print("- 蓝色线条: Tool连接")
    print("- 点击生物查看详细信息")
    print("- 点击空地添加食物")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    simulation.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按R重置
                    simulation = Simulation()
                elif event.key == pygame.K_f:  # 按F添加食物到随机位置
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(50, HEIGHT - 50)
                    simulation.environment.add_food((x, y))
                elif event.key == pygame.K_n:  # 按N创建新生物
                    x = random.randint(100, WIDTH - 100)
                    y = random.randint(100, HEIGHT - 100)
                    simulation.create_test_organism()
                    simulation.organisms[-1].position = np.array([x, y])
        
        # 更新模拟
        simulation.update()
        
        # 绘制
        simulation.draw(screen)
        
        # 显示按键提示
        keys_text = font.render("按键: R-重置 F-加食物 N-新生物", True, WHITE)
        screen.blit(keys_text, (WIDTH // 2 - 150, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()

if __name__ == "__main__":
    main()