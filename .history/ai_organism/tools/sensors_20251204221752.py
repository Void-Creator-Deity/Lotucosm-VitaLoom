"""传感器实现"""

from typing import Tuple
import math
from .base import SensorTool


class TouchSensor(SensorTool):
    """触觉传感器 - 检测接触
    
    触觉传感器的实现，用于检测环境中的接触压力。
    """
    
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        """初始化触觉传感器
        
        参数:
            tool_id: str - 工具唯一标识符
            position: Tuple[float, float] - 位置坐标
        """
        super().__init__(tool_id, position, sense_range=15)  # 感知范围15
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值
        
        检测环境中的接触压力，并返回感知值。
        
        参数:
            environment - 环境对象
            organism_position - 生物体位置
        
        返回:
            float - 接触压力值
        """
        world_pos = organism_position + self.position  # 计算世界坐标
        contact_info = environment.check_contact(world_pos, self.sense_range)  # 检查接触
        self.sensed_value = contact_info["pressure"]  # 获取压力值
        return self.sensed_value  # 返回感知值
        
    def process(self, input_value: float) -> float:
        """处理输入，返回输出值
        
        处理输入值并返回输出值，触觉传感器直接返回感知值。
        
        参数:
            input_value: float - 输入值
        
        返回:
            float - 处理后的输出值
        """
        return self.sensed_value  # 直接返回感知值
        
    def draw(self, surface):
        """绘制触觉传感器
        
        在指定表面上绘制触觉传感器，根据激活状态改变外观。
        
        参数:
            surface - 绘制表面
        """
        x, y = int(self.position[0]), int(self.position[1])
        color = (100, 255, 100) if self.activation > 0 else (50, 150, 50)
        
        # 触觉传感器图标 - 波纹状
        import pygame
        pygame.draw.circle(surface, color, (x, y), 12)  # 绘制传感器主体
        
        # 激活时的波纹效果
        if self.activation > 0.3:  # 只有在激活程度超过0.3时才显示波纹
            wave_radius = int(12 + 8 * self.activation)  # 波纹半径
            pygame.draw.circle(surface, (100, 255, 100, 100), (x, y), wave_radius, 2)  # 绘制波纹
            
    def get_icon(self):
        """获取工具类型图标
        
        返回触觉传感器的类型图标。
        
        返回:
            str - 工具类型图标
        """
        return "TOUCH"


class LightSensor(SensorTool):
    """光感传感器 - 检测光线
    
    光感传感器的实现，用于检测环境中的光线强度。
    """
    
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        """初始化光感传感器
        
        参数:
            tool_id: str - 工具唯一标识符
            position: Tuple[float, float] - 位置坐标
        """
        super().__init__(tool_id, position, sense_range=80)  # 感知范围80
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值
        
        检测环境中的光线强度，并返回感知值。
        
        参数:
            environment - 环境对象
            organism_position - 生物体位置
        
        返回:
            float - 光线强度值
        """
        world_pos = organism_position + self.position  # 计算世界坐标
        light_level = environment.get_light_intensity(world_pos)  # 获取光线强度
        self.sensed_value = light_level  # 保存感知值
        return self.sensed_value  # 返回感知值
        
    def process(self, input_value: float) -> float:
        """处理输入，返回输出值
        
        处理输入值并返回输出值，光感传感器直接返回感知值。
        
        参数:
            input_value: float - 输入值
        
        返回:
            float - 处理后的输出值
        """
        return self.sensed_value  # 直接返回感知值
        
    def draw(self, surface):
        """绘制光感传感器
        
        在指定表面上绘制光感传感器，根据激活状态改变外观。
        
        参数:
            surface - 绘制表面
        """
        x, y = int(self.position[0]), int(self.position[1])
        color = (255, 255, 100) if self.activation > 0 else (150, 150, 50)
        
        # 光感传感器图标 - 太阳状
        import pygame
        pygame.draw.circle(surface, color, (x, y), 10)  # 绘制传感器主体
        
        # 光线效果
        for i in range(8):  # 绘制8条光线
            angle = i * math.pi / 4  # 每条光线的角度
            end_x = x + 15 * math.cos(angle)  # 光线终点x坐标
            end_y = y + 15 * math.sin(angle)  # 光线终点y坐标
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)  # 绘制光线
            
    def get_icon(self):
        """获取工具类型图标
        
        返回光感传感器的类型图标。
        
        返回:
            str - 工具类型图标
        """
        return "LIGHT"
