"""传感器实现"""

from typing import Tuple
import math
from .base import SensorTool


class TouchSensor(SensorTool):
    """触觉传感器 - 检测接触"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, sense_range=15)
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值"""
        world_pos = organism_position + self.position
        contact_info = environment.check_contact(world_pos, self.sense_range)
        self.sensed_value = contact_info["pressure"]
        return self.sensed_value
        
    def process(self, input_value: float) -> float:
        """处理输入，返回输出值"""
        return self.sensed_value
        
    def draw(self, surface):
        """绘制Tool"""
        x, y = int(self.position[0]), int(self.position[1])
        color = (100, 255, 100) if self.activation > 0 else (50, 150, 50)
        
        # 触觉传感器图标 - 波纹状
        import pygame
        pygame.draw.circle(surface, color, (x, y), 12)
        
        # 激活时的波纹效果
        if self.activation > 0.3:
            wave_radius = int(12 + 8 * self.activation)
            pygame.draw.circle(surface, (100, 255, 100, 100), (x, y), wave_radius, 2)
            
    def get_icon(self):
        """获取Tool类型图标"""
        return "TOUCH"


class LightSensor(SensorTool):
    """光感传感器 - 检测光线"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, sense_range=80)
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值"""
        world_pos = organism_position + self.position
        light_level = environment.get_light_intensity(world_pos)
        self.sensed_value = light_level
        return self.sensed_value
        
    def process(self, input_value: float) -> float:
        """处理输入，返回输出值"""
        return self.sensed_value
        
    def draw(self, surface):
        """绘制Tool"""
        x, y = int(self.position[0]), int(self.position[1])
        color = (255, 255, 100) if self.activation > 0 else (150, 150, 50)
        
        # 光感传感器图标 - 太阳状
        import pygame
        pygame.draw.circle(surface, color, (x, y), 10)
        
        # 光线效果
        for i in range(8):
            angle = i * math.pi / 4
            end_x = x + 15 * math.cos(angle)
            end_y = y + 15 * math.sin(angle)
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)
            
    def get_icon(self):
        """获取Tool类型图标"""
        return "LIGHT"
