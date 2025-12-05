"""中枢管理器工具实现"""

import pygame
import numpy as np
from .base import CentralBrainTool as BaseCentralBrainTool


class CentralBrainTool(BaseCentralBrainTool):
    """中枢管理器 - 作为细胞的'大脑'"""
    def __init__(self, tool_id: str, position: np.ndarray):
        super().__init__(tool_id, position)
        self.associations = {}  # {sensor_id: {actuator_id: strength}}
        self.color = (255, 200, 100)  # 黄色
        self.border_color = (200, 150, 50)  # 深黄色边框
        self.radius = 20
        self.active_connections = []  # 当前活动的连接
        self.is_learning = True  # 学习开关
    
    def learn_association(self, sensor_id: str, actuator_id: str, success: bool):
        """学习传感器和效应器的关联"""
        if not self.is_learning:
            return
            
        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5  # 初始强度
        
        # 根据成功与否调整关联强度
        if success:
            self.associations[sensor_id][actuator_id] = min(1.0, self.associations[sensor_id][actuator_id] + self.learning_rate)
        else:
            self.associations[sensor_id][actuator_id] = max(0.0, self.associations[sensor_id][actuator_id] - self.learning_rate * 0.5)
    
    def generate_control_signals(self, sensor_values: dict) -> dict:
        """根据传感器输入生成控制信号"""
        control_signals = {}
        for sensor_id, value in sensor_values.items():
            if sensor_id in self.associations:
                for actuator_id, strength in self.associations[sensor_id].items():
                    if actuator_id not in control_signals:
                        control_signals[actuator_id] = 0.0
                    control_signals[actuator_id] += value * strength
        return control_signals
    
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
        """获取中枢管理器图标"""
        return "🧠"
    
    def get_icon(self) -> str:
        """获取工具图标"""
        return "🧠"