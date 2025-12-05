"""细胞膜工具实现"""

import pygame
import numpy as np
from .base import Tool


class MembraneTool(Tool):
    """细胞膜工具 - 作为细胞的边界"""
    def __init__(self, tool_id: str, position: np.ndarray, radius: float):
        super().__init__(tool_id, position)
        self.radius = radius
        self.color = (150, 150, 255, 100)  # 半透明蓝色
        self.border_color = (100, 100, 255)  # 蓝色边框
    
    def is_inside(self, position: np.ndarray) -> bool:
        """检查位置是否在细胞膜内"""
        distance = np.linalg.norm(position - self.position)
        return distance <= self.radius
    
    def auto_ingest(self, objects: list) -> list:
        """自动吞噬小型物体"""
        ingested_objects = []
        for obj in objects:
            if hasattr(obj, 'position') and hasattr(obj, 'size'):
                if self.is_inside(obj.position) and obj.size < self.radius / 3:
                    ingested_objects.append(obj)
        return ingested_objects
    
    def draw(self, surface: pygame.Surface):
        """绘制细胞膜"""
        pos = self.position.astype(int)
        # 绘制半透明细胞膜
        pygame.draw.circle(surface, self.color, pos, int(self.radius))
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, int(self.radius), 2)
    
    def process(self, input_value: float) -> float:
        """处理输入，作为工具接口"""
        return input_value
    
    def get_icon(self) -> str:
        """获取工具图标"""
        return "🧬"