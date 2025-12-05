"""细胞膜工具实现"""

import pygame
import numpy as np
from .base import Tool


class MembraneTool(Tool):
    """细胞膜工具 - 作为细胞的物理边界"""
    def __init__(self, tool_id: str, position: np.ndarray, radius: float):
        super().__init__(tool_id, position)
        self.radius = radius
        self.color = (200, 200, 255, 100)  # 半透明蓝色
        self.border_color = (100, 100, 255)  # 蓝色边框
        self.border_width = 2
        self.auto_ingest_threshold = radius * 0.3  # 自动吞噬阈值
    
    def is_inside(self, position: np.ndarray) -> bool:
        """检查位置是否在细胞膜内"""
        distance = np.linalg.norm(position - self.position)
        return distance <= self.radius
    
    def auto_ingest(self, objects: list) -> list:
        """自动吞噬小型物体
        
        Args:
            objects: 待检查的物体列表，每个物体需有position和radius属性
            
        Returns:
            未被吞噬的物体列表
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
        return input_value * 0.5  # 简单的信号处理
    
    def draw(self, surface: pygame.Surface):
        """绘制细胞膜"""
        pos = self.position.astype(int)
        # 绘制半透明细胞膜
        pygame.draw.circle(surface, self.color, pos, self.radius)
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, self.border_width)
    
    def get_icon(self) -> str:
        """获取细胞膜图标"""
        return "🔵"
    
    def update_position(self, new_position: np.ndarray):
        """更新细胞膜位置"""
        self.position = new_position
