"""组件连接实现"""

from typing import Any, Tuple, Optional
import pygame
from .components_base import ComponentBase

class Connection:
    """组件之间的连接

    实现组件之间的信号传递连接，支持单向和双向连接，
    可以是兴奋性连接（蓝色）或抑制性连接（红色）。

    属性:
        source: ComponentBase - 信号源组件
        target: ComponentBase - 信号目标组件
        weight: float - 连接权重，正值为兴奋性，负值为抑制性
        is_bidirectional: bool - 是否为双向连接
        signal_active: bool - 信号激活状态
        last_signal_time: int - 最后一次信号传递时间
    """

    def __init__(self, source: ComponentBase, target: ComponentBase, weight: float = 1.0, is_bidirectional: bool = False, id: Optional[str] = None, connection_type: Optional[str] = None):
        """初始化连接

        参数:
            source: ComponentBase - 信号源组件
            target: ComponentBase - 信号目标组件
            weight: float - 连接权重，正值为兴奋性，负值为抑制性
            is_bidirectional: bool - 是否为双向连接
            id: str - 连接ID（可选）
            connection_type: str - 连接类型（可选）
        """
        self.source = source  # 信号源组件
        self.target = target  # 信号目标组件
        self.weight = weight  # 连接权重
        self.is_bidirectional = is_bidirectional  # 是否为双向连接
        self.signal_active = False  # 信号激活状态
        self.last_signal_time = 0  # 最后一次信号传递时间
        self.id = id  # 连接ID
        self.connection_type = connection_type  # 连接类型

    def transmit_signal(self, signal_value: float) -> float:
        """传递信号，返回传递后的信号值

        参数:
            signal_value: float - 输入信号值

        返回:
            float - 传递后的信号值
        """
        # 标记信号激活
        self.signal_active = True
        self.last_signal_time = pygame.time.get_ticks()

        # 计算传递后的信号值，信号值乘以权重
        return signal_value * self.weight

    def update(self):
        """更新连接状态

        信号激活状态持续一段时间后恢复为非激活状态。
        """
        # 信号激活状态持续一段时间后恢复
        if self.signal_active and (pygame.time.get_ticks() - self.last_signal_time > 100):
            self.signal_active = False

    def draw(self, surface: Any):
        """绘制连接

        在指定表面上绘制连接，包括线条、箭头和信号传递效果。

        参数:
            surface - 绘制表面
        """
        start_pos = tuple(self.source.position.astype(int))  # 源位置
        end_pos = tuple(self.target.position.astype(int))  # 目标位置

        # 根据权重决定颜色和宽度
        if self.weight > 0:
            color = (100, 100, 255)  # 兴奋性连接 - 蓝色
        else:
            color = (255, 100, 100)  # 抑制性连接 - 红色

        line_width = max(1, int(2 * abs(self.weight)))  # 线宽与权重绝对值成正比

        # 绘制连接线条
        pygame.draw.line(surface, color, start_pos, end_pos, line_width)

        # 如果是双向连接，绘制双向箭头标记
        if self.is_bidirectional:
            # 绘制双向箭头
            self._draw_arrow(surface, start_pos, end_pos, color)
            self._draw_arrow(surface, end_pos, start_pos, color)
        else:
            # 绘制单向箭头
            self._draw_arrow(surface, start_pos, end_pos, color)

        # 信号传递效果：沿连接移动的白色圆点
        if self.signal_active:
            progress = (pygame.time.get_ticks() // 30) % 100 / 100.0  # 计算进度
            pulse_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            pulse_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
            pygame.draw.circle(surface, (255, 255, 255), (pulse_x, pulse_y), 3)

    def _draw_arrow(self, surface: Any, start_pos: Tuple[int, int], end_pos: Tuple[int, int], color: Tuple[int, int, int]):
        """绘制箭头

        在连接线条上绘制箭头，指示信号传递方向。

        参数:
            surface - 绘制表面
            start_pos - 箭头起始位置
            end_pos - 箭头结束位置
            color - 箭头颜色
        """
        # 计算箭头方向
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = (dx ** 2 + dy ** 2) ** 0.5

        if length == 0:
            return  # 位置相同，无法绘制箭头

        # 箭头单位向量
        unit_dx = dx / length
        unit_dy = dy / length

        # 箭头位置（在线条末尾，留出箭头长度）
        arrow_pos = (int(end_pos[0] - unit_dx * 10), int(end_pos[1] - unit_dy * 10))

        # 绘制箭头三角形
        pygame.draw.polygon(surface, color, [
            end_pos,
            (int(arrow_pos[0] + unit_dy * 5), int(arrow_pos[1] - unit_dx * 5)),
            (int(arrow_pos[0] - unit_dy * 5), int(arrow_pos[1] + unit_dx * 5))
        ])
