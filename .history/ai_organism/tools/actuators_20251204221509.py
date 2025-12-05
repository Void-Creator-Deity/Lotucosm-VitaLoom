"""效应器实现"""

from typing import Tuple
import math
import numpy as np
from .base import ActuatorTool


class MuscleActuator(ActuatorTool):
    """肌肉执行器 - 收缩产生力
    
    肌肉执行器的实现，通过收缩产生力，力的方向垂直于其位置向量。
    
    属性:
        contraction: float - 收缩程度，范围0-1
    """
    
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        """初始化肌肉执行器
        
        参数:
            tool_id: str - 工具唯一标识符
            position: Tuple[float, float] - 位置坐标
        """
        super().__init__(tool_id, position, force_strength=8.0)
        self.contraction = 0.0  # 收缩程度 0-1
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量
        
        根据控制信号计算收缩程度，并生成垂直于位置向量的力。
        
        参数:
            control_signal: float - 控制信号，范围0-1
        
        返回:
            np.ndarray - 力向量
        """
        self.contraction = np.clip(control_signal, 0, 1)  # 限制收缩程度在0-1之间
        self.current_force = self.contraction * self.force_strength  # 计算当前力
        
        # 肌肉产生的力方向垂直于其位置向量（简化模型）
        force_dir = np.array([-self.position[1], self.position[0]])
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)  # 归一化
            
        return force_dir * self.current_force  # 返回力向量
        
    def process(self, input_value: float):
        """处理输入，返回输出值
        
        肌肉执行器不处理输入，只响应控制信号。
        
        参数:
            input_value: float - 输入值
        
        返回:
            None - 肌肉不处理输入
        """
        # 肌肉不处理输入，只响应控制信号
        return None
        
    def draw(self, surface):
        """绘制肌肉执行器
        
        在指定表面上绘制肌肉执行器，根据收缩程度改变外观。
        
        参数:
            surface - 绘制表面
        """
        x, y = int(self.position[0]), int(self.position[1])
        
        # 根据收缩程度改变颜色
        base_red = 150 + int(105 * self.contraction)  # 收缩程度越高，颜色越红
        color = (base_red, 50, 50) if self.contraction > 0 else (150, 50, 50)
        
        # 肌肉图标 - 条状，收缩时变短变粗
        length = 20 - 8 * self.contraction  # 收缩程度越高，长度越短
        width = 8 + 4 * self.contraction  # 收缩程度越高，宽度越宽
        
        # 绘制肌肉纤维
        import pygame
        angle = math.atan2(self.position[1], self.position[0])  # 计算角度
        end_x = x + length * math.cos(angle)  # 计算终点x坐标
        end_y = y + length * math.sin(angle)  # 计算终点y坐标
        
        # 绘制肌肉主体
        pygame.draw.line(surface, color, (x, y), (end_x, end_y), int(width))
        
        # 收缩时的纹理
        if self.contraction > 0.3:  # 只有在收缩程度超过0.3时才绘制纹理
            for i in range(3):  # 绘制3条纹理线
                progress = (i + 1) / 4  # 纹理线位置
                mid_x = x + progress * length * math.cos(angle)  # 纹理线中点x坐标
                mid_y = y + progress * length * math.sin(angle)  # 纹理线中点y坐标
                perp_x = -math.sin(angle) * width * 0.3  # 垂直于肌肉的x偏移
                perp_y = math.cos(angle) * width * 0.3  # 垂直于肌肉的y偏移
                pygame.draw.line(surface, (200, 100, 100), 
                               (mid_x - perp_x, mid_y - perp_y),
                               (mid_x + perp_x, mid_y + perp_y), 2)
            
    def get_icon(self):
        """获取工具类型图标
        
        返回肌肉执行器的类型图标。
        
        返回:
            str - 工具类型图标
        """
        return "MUSCLE"


class CiliaActuator(ActuatorTool):
    """纤毛效应器 - 摆动产生推进力"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position, force_strength=4.0)
        self.swing_phase = 0.0  # 摆动相位
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量"""
        self.swing_phase = (self.swing_phase + control_signal * 0.1) % (2 * math.pi)
        self.current_force = control_signal * self.force_strength
        
        # 纤毛产生的力方向与其位置方向相反（推进）
        force_dir = -self.position
        if np.linalg.norm(force_dir) > 0:
            force_dir = force_dir / np.linalg.norm(force_dir)
            
        return force_dir * self.current_force
        
    def process(self, input_value: float):
        """处理输入，返回输出值"""
        return None
        
    def draw(self, surface):
        """绘制Tool"""
        x, y = int(self.position[0]), int(self.position[1])
        color = (100, 255, 255) if self.current_force > 0 else (50, 150, 150)
        
        # 纤毛图标 - 波浪状
        import pygame
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
        """获取Tool类型图标"""
        return "CILIA"
