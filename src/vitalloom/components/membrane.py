"""细胞膜组件实现 - AI生命体的物理边界和交互界面

本模块实现了AI生命体的细胞膜组件，作为细胞的物理边界，负责：
1. 分隔细胞内外环境
2. 实现自动吞噬功能
3. 处理细胞间通信
4. 信号传递与处理
5. 可视化绘制

细胞膜是AI生命体的重要组成部分，所有传感器、执行器等组件都必须位于细胞膜内才能正常工作。
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from .components_base import ComponentBase

class Membrane(ComponentBase):
    """细胞膜组件 - 作为细胞的物理边界和功能界面

    细胞膜组件是AI生命体的核心组件之一，负责管理细胞的物理边界，
    实现环境交互、自动吞噬、细胞间通信等关键功能。

    设计思路：
    - 采用圆形边界模型，便于距离计算和碰撞检测
    - 支持半透明可视化效果，增强用户体验
    - 实现信号处理机制，控制细胞内外信号传递
    - 支持细胞间通信，实现群体智能行为

    属性详解:
        radius: float - 细胞膜半径
        color: Tuple[int, int, int, int] - 细胞膜主体颜色，使用半透明蓝色
        border_color: Tuple[int, int, int] - 细胞膜边框颜色，使用蓝色
        border_width: int - 细胞膜边框宽度
        auto_ingest_threshold: float - 自动吞噬阈值，物体半径小于此值可能被吞噬
        permeability: float - 细胞膜通透性(0-1)，影响信号传递效率
        cell_communication_enabled: bool - 细胞间通信功能开关
    """

    def __init__(self, component_id: str, organism_id: str, **kwargs: Any):
        """
        初始化细胞膜组件

        创建细胞膜对象，设置初始属性和状态。

        参数详解:
            component_id: str - 组件唯一标识符，建议格式："organism_id_membrane"
            organism_id: str - 所属生物体ID
            kwargs: 其他参数
                - radius: float - 细胞膜半径，决定细胞大小
                - position: np.ndarray - 细胞膜中心位置坐标，格式：[x, y]
        """
        super().__init__(component_id, organism_id, **kwargs)

        # 细胞膜核心属性
        self._radius = kwargs.get('radius', 30.0)  # 细胞膜半径，使用下划线前缀表示私有属性

        # 可视化属性
        self.color = (200, 200, 255, 100)  # 半透明蓝色，增强视觉层次感
        self.border_color = (100, 100, 255)  # 蓝色边框，清晰界定边界
        self.border_width = 2  # 边框宽度，平衡视觉效果和性能

        # 功能属性
        self.auto_ingest_threshold = kwargs.get('auto_ingest_threshold', self._radius * 0.3)  # 自动吞噬阈值，设为半径的30%
        self.permeability = kwargs.get('permeability', 0.5)  # 通透性默认值0.5，中等信号传递效率
        self.cell_communication_enabled = kwargs.get('cell_communication_enabled', True)  # 默认启用细胞间通信

        # 位置属性
        self.location = kwargs.get('location', 'external')  # 细胞膜位于外部
        self.congenital = kwargs.get('congenital', True)  # 通常是先天组件

    def is_inside(self, position: np.ndarray) -> bool:
        """
        检查位置是否在细胞膜内

        使用欧几里得距离公式计算给定位置与细胞膜中心的距离，
        判断该位置是否在细胞膜范围内。

        参数:
            position: np.ndarray - 待检查的位置坐标，格式：[x, y]

        返回:
            bool - True表示位置在细胞膜内，False表示在膜外
        """
        distance = np.linalg.norm(position - self.position)  # 计算欧几里得距离
        return bool(distance <= self._radius)  # 距离小于等于半径则在膜内，转换为Python bool类型

    def auto_ingest(self, objects: List[Any]) -> Tuple[List[Any], List[Any]]:
        """
        自动吞噬小型物体

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
        """
        remaining_objects: List[Any] = []  # 未被吞噬的物体列表
        ingested_objects: List[Any] = []  # 被吞噬的物体列表

        # 遍历所有物体，检查吞噬条件
        for obj in objects:
            # 检查物体是否同时满足在膜内和半径小于阈值的条件
            if (hasattr(obj, 'position') and hasattr(obj, 'radius') and
                self.is_inside(obj.position) and 
                obj.radius <= self.auto_ingest_threshold):
                ingested_objects.append(obj)  # 满足条件，添加到被吞噬列表
            else:
                remaining_objects.append(obj)  # 不满足条件，保留在原列表

        return remaining_objects, ingested_objects

    def process(self, input_value: float) -> float:
        """处理输入信号

        实现细胞膜的信号处理逻辑，根据细胞膜通透性调整信号强度。

        参数:
            input_value: float - 输入信号值，范围通常为-1到1

        返回:
            float - 处理后的输出信号值，范围：input_value * permeability
        """
        # 更新激活状态
        self.activation = input_value
        self.state = "active" if abs(input_value) > self.signal_threshold else "idle"

        # 信号处理核心逻辑：输入信号乘以通透性系数
        self.output_signal = input_value * self.permeability
        return self.output_signal

    def cell_to_cell_communication(self, other_cell: Any) -> Dict[str, Any]:
        """
        细胞间通信

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
            Dict[str, Any] - 通信结果
        """
        # 检查通信功能是否启用
        if not self.cell_communication_enabled or not hasattr(other_cell, 'membrane'):
            return {
                'success': False,
                'reason': '通信功能未启用或细胞无效'
            }

        # 计算两个细胞中心之间的距离
        distance = np.linalg.norm(other_cell.membrane.position - self.position)

        # 计算通信阈值：两个细胞膜半径之和 + 10像素缓冲
        communication_threshold = self._radius + other_cell.membrane._radius + 10

        # 检查距离是否小于通信阈值
        if distance <= communication_threshold:
            # 通信条件满足，此处可扩展实际通信逻辑
            # 例如：交换遗传信息、传递环境数据等
            return {
                'success': True,
                'distance': distance,
                'communication_threshold': communication_threshold
            }

        return {
            'success': False,
            'reason': '距离过远',
            'distance': distance,
            'communication_threshold': communication_threshold
        }

    def update(self):
        """
        更新细胞膜状态
        """
        super().update()
        # 细胞膜特有更新逻辑
        # 可以添加细胞膜的动态变化、修复机制等

    def get_status(self) -> Dict[str, Any]:
        """
        获取细胞膜状态

        返回:
            Dict[str, Any] - 细胞膜状态信息
        """
        status = super().get_status()
        status.update({
            'radius': self._radius,
            'permeability': self.permeability,
            'auto_ingest_threshold': self.auto_ingest_threshold,
            'cell_communication_enabled': self.cell_communication_enabled
        })
        return status
