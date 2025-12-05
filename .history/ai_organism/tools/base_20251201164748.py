"""Tool系统的基类定义"""

from typing import Tuple, Optional
import numpy as np
import random


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
