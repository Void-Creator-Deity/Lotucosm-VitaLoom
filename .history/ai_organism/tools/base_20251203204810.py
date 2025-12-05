"""Tool系统的基类定义"""

from typing import Tuple, Optional, List, Dict
import numpy as np
import random
import pygame


class Tool:
    """Tool基类 - 所有具体Tool的父类"""
    
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        self.tool_id = tool_id
        self.position = np.array(position, dtype=float)
        self.connections: List['Connection'] = []  # 连接的Connection对象
        self.activation = 0.0
        self.state = "idle"  # 状态标识: idle, active, processing
        
        # 遗传特性
        self.genetic_strength = 1.0
        self.mutation_rate = 0.1
        
        # 信号处理
        self.input_signals: Dict[str, float] = {}  # 输入信号字典
        self.output_signal: float = 0.0  # 输出信号
        self.signal_threshold = 0.1  # 信号激活阈值
        self.transmitting = False  # 防止信号传递循环的标志
        
    def process(self, input_value: float) -> Optional[float]:
        """处理输入，返回输出值"""
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"
        
        # 基础处理逻辑，子类可以重写
        self.output_signal = input_value
        return self.output_signal
        
    def update(self):
        """每帧更新"""
        # 更新所有连接
        for connection in self.connections:
            connection.update()
        
        # 重置输入信号
        self.input_signals.clear()
        
        # 如果没有活动，恢复到闲置状态
        if self.state == "active" and abs(self.activation) < self.signal_threshold:
            self.state = "idle"
        
    def transmit_signals(self):
        """向所有连接的目标传递信号"""
        # 避免重复传递信号
        if self.transmitting:
            return
        
        try:
            self.transmitting = True
            for connection in self.connections:
                # 只向目标Tool传递信号
                if connection.source == self:
                    # 检查目标Tool是否已经在传递信号，避免循环
                    if not connection.target.transmitting:
                        # 传递信号
                        transmitted_value = connection.transmit_signal(self.output_signal)
                        # 更新目标Tool的输入信号
                        connection.target.input_signals[self.tool_id] = transmitted_value
        finally:
            self.transmitting = False
        
    def mutate(self):
        """变异"""
        if random.random() < self.mutation_rate:
            self.genetic_strength = np.clip(self.genetic_strength + random.gauss(0, 0.1), 0.5, 2.0)
            # 变异信号阈值
            self.signal_threshold = np.clip(self.signal_threshold + random.gauss(0, 0.05), 0.01, 0.5)
            
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
        self.sense_time = 0  # 上次感知时间
        self.sense_interval = 50  # 感知间隔（毫秒）
        
    def sense(self, environment, organism_position) -> float:
        """感知环境，返回感知值"""
        raise NotImplementedError("传感器子类必须实现sense方法")
    
    def update(self):
        """更新传感器状态"""
        super().update()
        # 传感器特有更新逻辑
        self.state = "active" if abs(self.sensed_value) > self.signal_threshold else "idle"


class ActuatorTool(Tool):
    """效应器Tool基类"""
    def __init__(self, tool_id: str, position: Tuple[float, float], force_strength: float):
        super().__init__(tool_id, position)
        self.force_strength = force_strength
        self.current_force = 0.0
        self.last_force = 0.0
        self.force_decay_rate = 0.1  # 力衰减率
        
    def apply_force(self, control_signal: float) -> np.ndarray:
        """根据控制信号施加力，返回力向量"""
        raise NotImplementedError("效应器子类必须实现apply_force方法")
    
    def update(self):
        """更新效应器状态"""
        super().update()
        # 效应器特有更新逻辑
        # 力的衰减
        if abs(self.current_force) > 0:
            self.current_force *= (1 - self.force_decay_rate)
            if abs(self.current_force) < 0.01:
                self.current_force = 0.0


class CentralBrainTool(Tool):
    """中枢管理器Tool基类"""
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        super().__init__(tool_id, position)
        self.associations: Dict[str, Dict[str, float]] = {}  # {sensor_id: {actuator_id: strength}}
        self.learning_rate = 0.1  # 学习率
        self.success_threshold = 0.5  # 成功阈值
        self.exploration_rate = 0.3  # 探索率
        
    def learn_association(self, sensor_id: str, actuator_id: str, success: bool):
        """学习传感器和效应器的关联"""
        if sensor_id not in self.associations:
            self.associations[sensor_id] = {}
        if actuator_id not in self.associations[sensor_id]:
            self.associations[sensor_id][actuator_id] = 0.5  # 初始强度
        
        # 根据成功与否调整关联强度
        if success:
            self.associations[sensor_id][actuator_id] = min(1.0, self.associations[sensor_id][actuator_id] + self.learning_rate)
        else:
            self.associations[sensor_id][actuator_id] = max(0.0, self.associations[sensor_id][actuator_id] - self.learning_rate * 0.5)
    
    def generate_control_signals(self, sensor_values: Dict[str, float]) -> Dict[str, float]:
        """根据传感器输入生成控制信号"""
        control_signals: Dict[str, float] = {}
        
        # 根据关联生成控制信号
        for sensor_id, value in sensor_values.items():
            if sensor_id in self.associations:
                for actuator_id, strength in self.associations[sensor_id].items():
                    if actuator_id not in control_signals:
                        control_signals[actuator_id] = 0.0
                    control_signals[actuator_id] += value * strength
        
        # 添加探索行为
        if random.random() < self.exploration_rate:
            # 随机选择一些效应器添加随机信号
            for actuator_id in control_signals:
                if random.random() < 0.5:
                    control_signals[actuator_id] += random.uniform(-0.5, 0.5)
        
        # 归一化控制信号
        for actuator_id in control_signals:
            control_signals[actuator_id] = max(-1.0, min(1.0, control_signals[actuator_id]))
        
        return control_signals
    
    def update(self):
        """更新中枢管理器状态"""
        super().update()
        # 中枢管理器特有更新逻辑
        # 可以添加记忆衰减、关联优化等逻辑


class MembraneTool(Tool):
    """细胞膜Tool基类"""
    def __init__(self, tool_id: str, position: Tuple[float, float], radius: float):
        super().__init__(tool_id, position)
        self.radius = radius
        self.color = (200, 200, 255, 100)  # 半透明蓝色
        self.border_color = (100, 100, 255)  # 蓝色边框
        self.border_width = 2
        self.auto_ingest_threshold = radius * 0.3  # 自动吞噬阈值
        self.ingestion_rate = 1.0  # 吞噬速率
        
    def is_inside(self, position: np.ndarray) -> bool:
        """检查位置是否在细胞膜内"""
        distance = np.linalg.norm(position - self.position)
        return distance <= self.radius
    
    def auto_ingest(self, objects: list) -> tuple[list, list]:
        """自动吞噬小型物体
        
        Args:
            objects: 待检查的物体列表，每个物体需有position和radius属性
            
        Returns:
            (未被吞噬的物体列表, 被吞噬的物体列表)
        """
        remaining_objects = []
        ingested_objects = []
        
        for obj in objects:
            # 检查物体是否在细胞膜内且大小小于阈值
            if (self.is_inside(obj.position) and 
                obj.radius <= self.auto_ingest_threshold):
                ingested_objects.append(obj)
            else:
                remaining_objects.append(obj)
        
        return remaining_objects, ingested_objects
    
    def process(self, input_value: float) -> float:
        """处理输入信号
        
        细胞膜作为特殊工具，处理环境信息并返回控制信号
        """
        # 细胞膜处理逻辑
        self.output_signal = input_value * 0.5  # 简单的信号处理
        return self.output_signal
    
    def update(self):
        """更新细胞膜状态"""
        super().update()
        # 细胞膜特有更新逻辑
        # 可以添加细胞膜的动态变化、修复机制等
