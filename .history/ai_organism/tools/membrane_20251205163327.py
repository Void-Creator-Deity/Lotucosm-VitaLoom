"""细胞膜工具实现 - AI生命体的物理边界和交互界面

本模块实现了AI生命体的细胞膜工具，作为细胞的物理边界，负责：
1. 分隔细胞内外环境
2. 实现自动吞噬功能
3. 处理细胞间通信
4. 信号传递与处理
5. 可视化绘制

细胞膜是AI生命体的重要组成部分，所有传感器、效应器等工具都必须位于细胞膜内才能正常工作。
"""

import pygame
import numpy as np
from typing import List, Tuple, Any
from .base import Membrane as BaseMembrane


class Membrane(BaseMembrane):
    """细胞膜工具 - 作为细胞的物理边界和功能界面
    
    细胞膜工具是AI生命体的核心组件之一，负责管理细胞的物理边界，
    实现环境交互、自动吞噬、细胞间通信等关键功能。
    
    设计思路：
    - 采用圆形边界模型，便于距离计算和碰撞检测
    - 支持半透明可视化效果，增强用户体验
    - 实现信号处理机制，控制细胞内外信号传递
    - 支持细胞间通信，实现群体智能行为
    
    属性详解:
        color: Tuple[int, int, int, int] - 细胞膜主体颜色，使用半透明蓝色
        border_color: Tuple[int, int, int] - 细胞膜边框颜色，使用蓝色
        border_width: int - 细胞膜边框宽度
        auto_ingest_threshold: float - 自动吞噬阈值，物体半径小于此值可能被吞噬
        permeability: float - 细胞膜通透性(0-1)，影响信号传递效率
        cell_communication_enabled: bool - 细胞间通信功能开关
        
    继承自BaseMembrane的核心属性:
        tool_id: str - 工具唯一标识符
        position: np.ndarray - 细胞膜中心位置坐标
        radius: float - 细胞膜半径
        activation: float - 细胞膜激活状态值(-1到1)
        state: str - 细胞膜当前状态("idle", "active", "inactive")
        output_signal: float - 输出信号值
    """
    
    def __init__(self, tool_id: str, position: np.ndarray, radius: float):
        """初始化细胞膜工具
        
        创建细胞膜对象，设置初始属性和状态。
        
        参数详解:
            tool_id: str - 工具唯一标识符，建议格式："organism_id_membrane"
            position: np.ndarray - 细胞膜中心位置坐标，格式：[x, y]
            radius: float - 细胞膜半径，决定细胞大小
        
        示例:
            >>> membrane = Membrane("organism_1_membrane", np.array([400, 300]), 30)
        """
        super().__init__(tool_id, position, radius)
        
        # 可视化属性
        self.color = (200, 200, 255, 100)  # 半透明蓝色，增强视觉层次感
        self.border_color = (100, 100, 255)  # 蓝色边框，清晰界定边界
        self.border_width = 2  # 边框宽度，平衡视觉效果和性能
        
        # 功能属性
        self.auto_ingest_threshold = radius * 0.3  # 自动吞噬阈值，设为半径的30%
        self.permeability = 0.5  # 通透性默认值0.5，中等信号传递效率
        self.cell_communication_enabled = True  # 默认启用细胞间通信
    
    def is_inside(self, position: np.ndarray) -> bool:
        """检查位置是否在细胞膜内
        
        使用欧几里得距离公式计算给定位置与细胞膜中心的距离，
        判断该位置是否在细胞膜范围内。
        
        算法原理:
            1. 计算给定位置与细胞膜中心的欧几里得距离
            2. 将距离与细胞膜半径比较
            3. 返回比较结果
        
        参数:
            position: np.ndarray - 待检查的位置坐标，格式：[x, y]
        
        返回:
            bool - True表示位置在细胞膜内，False表示在膜外
        
        示例:
            >>> membrane = Membrane("test", np.array([0, 0]), 10)
            >>> membrane.is_inside(np.array([5, 0]))  # 在膜内
            True
            >>> membrane.is_inside(np.array([15, 0]))  # 在膜外
            False
        """
        distance = np.linalg.norm(position - self.position)  # 计算欧几里得距离
        return distance <= self.radius  # 距离小于等于半径则在膜内
    
    def auto_ingest(self, objects: List[Any]) -> Tuple[List[Any], List[Any]]:
        """自动吞噬小型物体
        
        自动检测并吞噬在细胞膜内且大小小于阈值的物体，
        实现细胞的基本营养获取功能。
        
        吞噬条件:
            1. 物体位置在细胞膜内
            2. 物体半径小于自动吞噬阈值
        
        参数:
            objects: List[Any] - 待检查的物体列表，每个物体必须包含:
                              - position: np.ndarray - 物体位置
                              - radius: float - 物体半径
        
        返回:
            Tuple[List[Any], List[Any]] - 元组包含两个列表:
                - 第一个列表: 未被吞噬的物体
                - 第二个列表: 被成功吞噬的物体
        
        示例:
            >>> class Food:
            ...     def __init__(self, pos, rad):
            ...         self.position = pos
            ...         self.radius = rad
            >>> membrane = Membrane("test", np.array([0, 0]), 20)
            >>> foods = [
            ...     Food(np.array([5, 5]), 5),   # 会被吞噬
            ...     Food(np.array([25, 0]), 3),  # 在膜外，不会被吞噬
            ...     Food(np.array([5, 0]), 8)     # 半径太大，不会被吞噬
            ... ]
            >>> remaining, ingested = membrane.auto_ingest(foods)
            >>> len(remaining), len(ingested)
            (2, 1)
        """
        remaining_objects = []  # 未被吞噬的物体列表
        ingested_objects = []  # 被吞噬的物体列表
        
        # 遍历所有物体，检查吞噬条件
        for obj in objects:
            # 检查物体是否同时满足在膜内和半径小于阈值的条件
            if (self.is_inside(obj.position) and 
                obj.radius <= self.auto_ingest_threshold):
                ingested_objects.append(obj)  # 满足条件，添加到被吞噬列表
            else:
                remaining_objects.append(obj)  # 不满足条件，保留在原列表
        
        return remaining_objects, ingested_objects
    
    def process(self, input_value: float) -> float:
        """处理输入信号
        
        实现细胞膜的信号处理逻辑，根据细胞膜通透性调整信号强度。
        
        信号处理流程:
            1. 接收外部输入信号
            2. 根据细胞膜通透性调整信号强度
            3. 更新输出信号属性
            4. 返回处理后的信号
        
        参数:
            input_value: float - 输入信号值，范围通常为-1到1
        
        返回:
            float - 处理后的输出信号值，范围：input_value * permeability
        
        示例:
            >>> membrane = Membrane("test", np.array([0, 0]), 10)
            >>> membrane.permeability = 0.5
            >>> membrane.process(1.0)  # 输入信号1.0，输出0.5
            0.5
            >>> membrane.permeability = 0.8
            >>> membrane.process(1.0)  # 输入信号1.0，输出0.8
            0.8
        """
        # 信号处理核心逻辑：输入信号乘以通透性系数
        self.output_signal = input_value * self.permeability
        return self.output_signal
    
    def draw(self, surface: pygame.Surface):
        """绘制细胞膜
        
        在指定的Pygame表面上绘制细胞膜，包括主体、边框和状态效果。
        
        绘制层次:
            1. 半透明主体 - 显示细胞膜的基本形态
            2. 边框 - 清晰界定细胞膜边界
            3. 激活状态效果 - 显示细胞膜的动态状态
        
        参数:
            surface: pygame.Surface - Pygame绘制表面对象
        
        注意事项:
            - 绘制前会将位置坐标转换为整数，提高绘制效率
            - 激活状态下会绘制脉冲效果，增强视觉反馈
        """
        # 将浮点数坐标转换为整数，提高绘制性能
        pos = self.position.astype(int)
        
        # 绘制半透明细胞膜主体
        pygame.draw.circle(surface, self.color, pos, self.radius)
        
        # 绘制细胞膜边框
        pygame.draw.circle(surface, self.border_color, pos, self.radius, self.border_width)
        
        # 绘制激活状态效果
        if self.state == "active":
            # 计算脉冲半径：基础半径 + 5 * 激活强度绝对值
            # 激活强度范围为-1到1，因此脉冲半径变化范围为±5像素
            pulse_radius = int(self.radius + 5 * abs(self.activation))
            
            # 创建半透明脉冲效果，使用Alpha通道实现渐变效果
            # 绘制单层半透明圆圈，模拟细胞膜脉动
            pygame.draw.circle(surface, (200, 200, 255, 50), pos, pulse_radius, 1)
    
    def cell_to_cell_communication(self, other_cell) -> bool:
        """细胞间通信
        
        实现细胞间的通信功能，检查两个细胞是否在通信范围内。
        
        通信条件:
            1. 细胞间通信功能已启用
            2. 两个细胞间距离小于通信阈值
        
        通信阈值计算:
            通信阈值 = 细胞膜1半径 + 细胞膜2半径 + 10像素缓冲
            (10像素缓冲确保细胞接近但未接触时即可通信)
        
        参数:
            other_cell: Any - 另一个细胞对象，必须包含membrane属性
        
        返回:
            bool - 通信是否成功建立
        
        注意事项:
            - 目前仅实现通信可达性检查
            - 可扩展为实现实际的数据交换逻辑
        """
        # 检查通信功能是否启用
        if not self.cell_communication_enabled:
            return False  # 通信功能未启用，直接返回失败
        
        # 计算两个细胞中心之间的距离
        distance = np.linalg.norm(other_cell.membrane.position - self.position)
        
        # 计算通信阈值：两个细胞膜半径之和 + 10像素缓冲
        communication_threshold = self.radius + other_cell.membrane.radius + 10
        
        # 检查距离是否小于通信阈值
        if distance <= communication_threshold:
            # 通信条件满足，此处可扩展实际通信逻辑
            # 例如：交换遗传信息、传递环境数据等
            return True  # 通信成功
        
        return False  # 距离过远，通信失败
    
    def get_icon(self) -> str:
        """获取细胞膜图标
        
        返回代表细胞膜的图标，用于可视化和用户界面显示。
        
        返回:
            str - 细胞膜图标，使用蓝色圆圈emoji
        
        示例:
            >>> membrane = Membrane("test", np.array([0, 0]), 10)
            >>> membrane.get_icon()
            "🔵"
        """
        return "🔵"  # 使用蓝色圆圈emoji代表细胞膜
    
    def update_position(self, new_position: np.ndarray):
        """更新细胞膜位置
        
        更新细胞膜的中心位置坐标，用于实现细胞的移动功能。
        
        参数:
            new_position: np.ndarray - 新的位置坐标，格式：[x, y]
        
        示例:
            >>> membrane = Membrane("test", np.array([0, 0]), 10)
            >>> membrane.update_position(np.array([10, 10]))
            >>> membrane.position
            array([10, 10])
        """
        self.position = new_position  # 直接更新位置坐标

