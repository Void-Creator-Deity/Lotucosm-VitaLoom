"""细胞膜工具实现"""

import pygame
import numpy as np
from .base import MembraneTool as BaseMembraneTool


class MembraneTool(BaseMembraneTool):
    """细胞膜工具 - 作为细胞的物理边界
    
    细胞膜工具的实现，作为细胞的物理边界，负责分隔细胞内外环境，
    实现自动吞噬、细胞间通信等功能。
    
    属性:
        color: Tuple[int, int, int, int] - 颜色，半透明蓝色
        border_color: Tuple[int, int, int] - 边框颜色，蓝色
        border_width: int - 边框宽度
        auto_ingest_threshold: float - 自动吞噬阈值
        permeability: float - 通透性，影响信号传递
        cell_communication_enabled: bool - 细胞间通信启用标志
    """
    def __init__(self, tool_id: str, position: np.ndarray, radius: float):
        """初始化细胞膜工具
        
        参数:
            tool_id: str - 工具唯一标识符
            position: np.ndarray - 位置坐标
            radius: float - 细胞膜半径
        """
        super().__init__(tool_id, position, radius)
        self.color = (200, 200, 255, 100)  # 半透明蓝色
        self.border_color = (100, 100, 255)  # 蓝色边框
        self.border_width = 2  # 边框宽度
        self.auto_ingest_threshold = radius * 0.3  # 自动吞噬阈值
        self.permeability = 0.5  # 通透性，影响信号传递
        self.cell_communication_enabled = True  # 细胞间通信启用标志
    
    def is_inside(self, position: np.ndarray) -> bool:
        """检查位置是否在细胞膜内
        
        计算给定位置与细胞膜中心的距离，判断是否在细胞膜内。
        
        参数:
            position: np.ndarray - 待检查的位置坐标
        
        返回:
            bool - 位置是否在细胞膜内
        """
        distance = np.linalg.norm(position - self.position)  # 计算距离
        return distance <= self.radius  # 判断是否在半径范围内
    
    def auto_ingest(self, objects: list) -> tuple[list, list]:
        """自动吞噬小型物体
        
        自动吞噬在细胞膜内且大小小于阈值的物体。
        
        参数:
            objects: list - 待检查的物体列表，每个物体需有position和radius属性
            
        返回:
            tuple[list, list] - (未被吞噬的物体列表, 被吞噬的物体列表)
        """
        remaining_objects = []  # 未被吞噬的物体列表
        ingested_objects = []  # 被吞噬的物体列表
        
        for obj in objects:
            # 检查物体是否在细胞膜内且大小小于阈值
            if (self.is_inside(obj.position) and 
                obj.radius <= self.auto_ingest_threshold):
                ingested_objects.append(obj)  # 被吞噬
            else:
                remaining_objects.append(obj)  # 未被吞噬
        
        return remaining_objects, ingested_objects
    
    def process(self, input_value: float) -> float:
        """处理输入信号
        
        细胞膜作为特殊工具，处理环境信息并返回控制信号，
        信号强度受细胞膜通透性影响。
        
        参数:
            input_value: float - 输入信号
        
        返回:
            float - 处理后的输出信号
        """
        # 细胞膜处理逻辑，信号强度乘以通透性
        self.output_signal = input_value * self.permeability
        return self.output_signal
    
    def draw(self, surface: pygame.Surface):
        """绘制细胞膜
        
        在指定表面上绘制细胞膜，包括半透明主体、边框和激活状态效果。
        
        参数:
            surface: pygame.Surface - 绘制表面
        """
        pos = self.position.astype(int)  # 转换为整数坐标
        # 绘制半透明细胞膜主体
        pygame.draw.circle(surface, self.color, pos, self.radius)
        # 绘制边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, self.border_width)
        
        # 绘制细胞膜状态指示器
        if self.state == "active":
            # 绘制激活状态的脉冲效果，半径随激活强度变化
            pulse_radius = int(self.radius + 5 * abs(self.activation))
            pygame.draw.circle(surface, (200, 200, 255, 50), pos, pulse_radius, 1)
    
    def cell_to_cell_communication(self, other_cell) -> bool:
        """细胞间通信
        
        与其他细胞进行通信，检查细胞间距离是否在通信范围内。
        
        参数:
            other_cell: 另一个细胞对象
            
        返回:
            bool - 通信是否成功
        """
        if not self.cell_communication_enabled:
            return False  # 通信功能未启用
        
        # 检查两个细胞是否足够接近
        distance = np.linalg.norm(other_cell.membrane.position - self.position)
        if distance <= self.radius + other_cell.membrane.radius + 10:  # 通信距离阈值
            # 这里可以实现更复杂的通信逻辑
            return True  # 通信成功
        return False  # 通信失败
    
    def get_icon(self) -> str:
        """获取细胞膜图标
        
        返回细胞膜的工具图标。
        
        返回:
            str - 细胞膜图标，使用蓝色圆圈emoji
        """
        return "🔵"
    
    def update_position(self, new_position: np.ndarray):
        """更新细胞膜位置
        
        更新细胞膜的位置坐标。
        
        参数:
            new_position: np.ndarray - 新的位置坐标
        """
        self.position = new_position
