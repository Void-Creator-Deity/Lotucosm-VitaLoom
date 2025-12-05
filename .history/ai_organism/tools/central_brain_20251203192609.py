"""中枢管理器工具实现"""

import pygame
import numpy as np
from .base import Tool


class CentralBrainTool(Tool):
    """中枢管理器 - 作为细胞的"大脑""""
    def __init__(self, tool_id: str, position: np.ndarray):
        super().__init__(tool_id, position)
        self.associations = {}  # {sensor_id: {actuator_id: strength}}
        self.color = (255, 200, 100)  # 黄色
        self.border_color = (200, 150, 50)  # 深黄色边框
        self.radius = 20
    
    def learn_association(self, sensor_id: str, actuator_id: str, success: bool):
        """学习传感器和效应器的关联"""
        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5  # 初始强度
        
        # 根据成功与否调整关联强度
        if success:
            self.associations[sensor_id][actuator_id] = min(1.0, self.associations[sensor_id][actuator_id] + 0.1)
        else:
            self.associations[sensor_id][actuator_id] = max(0.0, self.associations[sensor_id][actuator_id] - 0.05)
    
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
        # 绘制主体
        pygame.draw.circle(surface, self.color, pos, self.radius)
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, 2)
        # 绘制"大脑"图标
        font = pygame.font.Font(None, 24)
        text = font.render("🧠", True, (0, 0, 0))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)
    
    def process(self, input_value: float) -> float:
        """处理输入，作为工具接口"""
        return input_value
    
    def get_icon(self) -> str:
        """获取工具图标"""
        return "🧠"