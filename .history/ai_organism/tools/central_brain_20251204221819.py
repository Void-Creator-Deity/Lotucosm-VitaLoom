"""中枢管理器工具实现"""

import pygame
import numpy as np
from .base import CentralBrainTool as BaseCentralBrainTool


class CentralBrainTool(BaseCentralBrainTool):
    """中枢管理器 - 作为细胞的'大脑'，实现强化学习算法
    
    中枢管理器的实现，负责AI生命体的决策和学习，
    实现了Q-learning算法和经验回放机制。
    
    属性:
        associations: Dict[str, Dict[str, float]] - 传感器-执行器关联强度
        color: Tuple[int, int, int] - 颜色
        border_color: Tuple[int, int, int] - 边框颜色
        radius: int - 半径
        active_connections: List[Connection] - 当前活动的连接列表
        is_learning: bool - 学习开关
        q_table: Dict[tuple, Dict[str, float]] - Q-learning表格
        gamma: float - 折扣因子
        epsilon: float - 探索率
        epsilon_decay: float - 探索率衰减
        epsilon_min: float - 最小探索率
        rewards: List[float] - 奖励历史
        max_reward: float - 最大奖励
        state: dict - 当前状态
        prev_state: dict - 上一状态
        prev_action: dict - 上一动作
        learning_enabled: bool - 全局学习开关
        learning_rate_min: float - 最小学习率
        learning_rate_max: float - 最大学习率
        learning_rate_decay: float - 学习率衰减
        learning_rate: float - 当前学习率
        memory: List - 经验回放记忆
        memory_size: int - 最大记忆容量
    """
    
    def __init__(self, tool_id: str, position: np.ndarray):
        """初始化中枢管理器
        
        参数:
            tool_id: str - 工具唯一标识符
            position: np.ndarray - 位置坐标
        """
        super().__init__(tool_id, position)
        self.associations = {}  # {sensor_id: {actuator_id: strength}} - 基本关联
        self.color = (255, 200, 100)  # 黄色
        self.border_color = (200, 150, 50)  # 深黄色边框
        self.radius = 20
        self.active_connections = []  # 当前活动的连接
        self.is_learning = True  # 学习开关
        
        # 强化学习参数
        self.q_table = {}  # Q-learning表格 {state: {action: value}}
        self.gamma = 0.9  # 折扣因子
        self.epsilon = 0.2  # 探索率
        self.epsilon_decay = 0.995  # 探索率衰减
        self.epsilon_min = 0.01  # 最小探索率
        self.rewards = []  # 奖励历史
        self.max_reward = 0  # 最大奖励
        
        # 状态表示和奖励函数
        self.state = {}  # 当前状态
        self.prev_state = {}  # 上一状态
        self.prev_action = {}  # 上一动作
        self.learning_enabled = True  # 全局学习开关
        
        # 学习率调度
        self.learning_rate_min = 0.001
        self.learning_rate_max = 0.1
        self.learning_rate_decay = 0.999
        self.learning_rate = self.learning_rate_max
        
        # 记忆系统
        self.memory = []  # 经验回放记忆
        self.memory_size = 1000  # 最大记忆容量
    
    def learn_association(self, sensor_id: str, actuator_id: str, success: bool):
        """学习传感器和执行器的关联
        
        根据成功与否调整传感器和执行器之间的关联强度。
        
        参数:
            sensor_id: str - 传感器ID
            actuator_id: str - 执行器ID
            success: bool - 行动是否成功
        """
        if not self.is_learning:
            return  # 学习开关关闭，直接返回
            
        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}  # 初始化传感器关联
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5  # 初始强度设置为0.5
        
        # 根据成功与否调整关联强度
        if success:
            # 成功时增强关联强度
            self.associations[sensor_id][actuator_id] = min(1.0, self.associations[sensor_id][actuator_id] + self.learning_rate)
        else:
            # 失败时减弱关联强度
            self.associations[sensor_id][actuator_id] = max(0.0, self.associations[sensor_id][actuator_id] - self.learning_rate * 0.5)
    
    def _extract_state(self, sensor_values: dict) -> tuple:
        """从传感器值中提取状态
        
        将传感器值字典转换为可哈希的元组，用于Q-learning表格的索引。
        
        参数:
            sensor_values: dict - 传感器值字典
        
        返回:
            tuple - 提取的状态，格式为排序后的(传感器ID, 值)元组
        """
        # 将传感器值转换为离散状态，排序确保相同传感器值生成相同状态
        state = tuple(sorted(sensor_values.items()))
        return state
    
    def _choose_action(self, state: tuple, sensor_values: dict) -> dict:
        """基于Q-learning选择动作"""
        # 探索
        if self.learning_enabled and random.random() < self.epsilon:
            # 随机选择动作
            return self._random_action(sensor_values)
        # 利用
        else:
            return self._greedy_action(state, sensor_values)
    
    def _random_action(self, sensor_values: dict) -> dict:
        """生成随机动作"""
        control_signals = {}
        actuator_ids = list(self.associations.values())[0].keys() if self.associations else []
        for actuator_id in actuator_ids:
            control_signals[actuator_id] = random.uniform(-1.0, 1.0)
        return control_signals
    
    def _greedy_action(self, state: tuple, sensor_values: dict) -> dict:
        """基于当前Q值选择最优动作"""
        # 首先使用基本关联机制生成动作
        control_signals = {}
        for sensor_id, value in sensor_values.items():
            if sensor_id in self.associations:
                for actuator_id, strength in self.associations[sensor_id].items():
                    if actuator_id not in control_signals:
                        control_signals[actuator_id] = 0.0
                    control_signals[actuator_id] += value * strength
        
        # 如果Q表中有当前状态的信息，使用Q值调整动作
        if state in self.q_table:
            q_values = self.q_table[state]
            # 这里需要将Q值映射到控制信号，简化处理
            for actuator_id in control_signals:
                if actuator_id in q_values:
                    # 使用Q值调整控制信号强度
                    control_signals[actuator_id] *= (1 + q_values[actuator_id] * 0.5)
        
        # 归一化控制信号
        for actuator_id in control_signals:
            control_signals[actuator_id] = max(-1.0, min(1.0, control_signals[actuator_id]))
        
        return control_signals
    
    def generate_control_signals(self, sensor_values: dict) -> dict:
        """根据传感器输入生成控制信号，使用强化学习"""
        # 提取状态
        self.prev_state = self.state
        self.state = self._extract_state(sensor_values)
        
        # 选择动作
        action = self._choose_action(self.state, sensor_values)
        
        # 保存动作
        self.prev_action = action.copy()
        
        return action
    
    def learn(self, reward: float):
        """强化学习核心算法"""
        if not self.learning_enabled or not self.prev_state or not self.prev_action:
            return
        
        # 更新学习率
        self.learning_rate = max(self.learning_rate_min, self.learning_rate * self.learning_rate_decay)
        
        # 更新探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # 保存经验
        self.memory.append((self.prev_state, self.prev_action, reward, self.state))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        
        # 更新Q表
        if self.prev_state not in self.q_table:
            self.q_table[self.prev_state] = {}
        if self.state not in self.q_table:
            self.q_table[self.state] = {}
        
        # Q-learning更新公式：Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        max_next_q = max(self.q_table[self.state].values()) if self.q_table[self.state] else 0
        
        for actuator_id, action_value in self.prev_action.items():
            # 计算当前Q值
            current_q = self.q_table[self.prev_state].get(actuator_id, 0)
            
            # 计算新Q值
            new_q = current_q + self.learning_rate * (reward + self.gamma * max_next_q - current_q)
            
            # 更新Q表
            self.q_table[self.prev_state][actuator_id] = new_q
        
        # 保存奖励
        self.rewards.append(reward)
        if len(self.rewards) > 100:
            self.rewards.pop(0)
        
        # 更新最大奖励
        if reward > self.max_reward:
            self.max_reward = reward
    
    def calculate_reward(self, organism, environment) -> float:
        """计算奖励"""
        # 基础奖励：生存和能量
        reward = organism.energy / 100  # 能量越高奖励越高
        
        # 位置奖励：靠近食物
        food_nearby = len(environment.get_nearby_food(organism.position, 50))
        reward += food_nearby * 0.5
        
        # 避免碰撞
        for obstacle in environment.obstacles:
            if np.linalg.norm(organism.position - obstacle.position) < organism.radius + obstacle.radius:
                reward -= 0.5
                break
        
        # 探索奖励：访问新区域
        # 这里可以添加更复杂的探索奖励机制
        
        # 保持平衡
        if organism.velocity is not None and hasattr(organism.velocity, 'norm'):
            speed = organism.velocity.norm()
            if speed > 5:
                reward -= 0.1  # 速度过快惩罚
        
        return reward
    
    def update(self):
        """更新中枢管理器状态"""
        super().update()
        
        # 更新活动连接列表
        self.active_connections.clear()
        for connection in self.connections:
            if connection.signal_active:
                self.active_connections.append(connection)
    
    def get_associations(self) -> dict:
        """获取所有关联"""
        return self.associations.copy()
    
    def set_associations(self, associations: dict):
        """设置关联，用于遗传"""
        self.associations = associations
    
    def draw(self, surface: pygame.Surface):
        """绘制中枢管理器"""
        pos = self.position.astype(int)
        
        # 根据激活状态改变颜色
        if self.activation > self.signal_threshold:
            current_color = (255, 220, 120)  # 激活状态颜色
        else:
            current_color = self.color  # 正常状态颜色
            
        # 绘制主体
        pygame.draw.circle(surface, current_color, pos, self.radius)
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, 2)
        # 绘制"大脑"图标
        font = pygame.font.Font(None, 24)
        text = font.render("🧠", True, (0, 0, 0))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)
        
        # 绘制激活状态效果
        if self.activation > self.signal_threshold:
            # 绘制脉冲环
            pulse_radius = int(self.radius + 5 * abs(self.activation))
            pygame.draw.circle(surface, (255, 255, 100, 100), pos, pulse_radius, 2)
    
    def process(self, input_value: float) -> float:
        """处理输入，返回输出值"""
        # 调用父类的process方法更新状态
        super().process(input_value)
        return self.output_signal
    
    def update(self):
        """更新中枢管理器状态"""
        super().update()
        
        # 更新活动连接列表
        self.active_connections.clear()
        for connection in self.connections:
            if connection.signal_active:
                self.active_connections.append(connection)
    
    def get_icon(self) -> str:
        """获取工具图标"""
        return "🧠"