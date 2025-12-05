"""细胞膜工具实现"""

import pygame
import numpy as np
from .base import MembraneTool as BaseMembraneTool


class MembraneTool(BaseMembraneTool):
    """细胞膜工具 - 作为细胞的物理边界"""
    def __init__(self, tool_id: str, position: np.ndarray, radius: float):
        super().__init__(tool_id, position, radius)
        self.color = (200, 200, 255, 100)  # 半透明蓝色
        self.border_color = (100, 100, 255)  # 蓝色边框
        self.border_width = 2
        self.auto_ingest_threshold = radius * 0.3  # 自动吞噬阈值
        self.permeability = 0.5  # 通透性
        self.cell_communication_enabled = True  # 细胞间通信启用标志
    
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
        self.output_signal = input_value * self.permeability
        return self.output_signal
    
    def draw(self, surface: pygame.Surface):
        """绘制细胞膜"""
        pos = self.position.astype(int)
        # 绘制半透明细胞膜
        pygame.draw.circle(surface, self.color, pos, self.radius)
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, self.border_width)
        
        # 绘制细胞膜状态指示器
        if self.state == "active":
            # 绘制激活状态的脉冲效果
            pulse_radius = int(self.radius + 5 * abs(self.activation))
            pygame.draw.circle(surface, (200, 200, 255, 50), pos, pulse_radius, 1)
    
    def cell_to_cell_communication(self, other_cell) -> bool:
        """细胞间通信
        
        Args:
            other_cell: 另一个细胞对象
            
        Returns:
            通信是否成功
        """
        if not self.cell_communication_enabled:
            return False
        
        # 检查两个细胞是否足够接近
        distance = np.linalg.norm(other_cell.membrane.position - self.position)
        if distance <= self.radius + other_cell.membrane.radius + 10:
            # 这里可以实现更复杂的通信逻辑
            return True
        return False
    
    def get_icon(self) -> str:
        """获取细胞膜图标"""
        return "🔵"
    
    def update_position(self, new_position: np.ndarray):
        """更新细胞膜位置"""
        self.position = new_position
