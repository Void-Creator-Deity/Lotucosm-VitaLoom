"""Tool连接实现"""

import pygame
from .base import Tool


class Connection:
    """Tool之间的连接"""
    def __init__(self, source: Tool, target: Tool, weight: float = 1.0):
        self.source = source
        self.target = target
        self.weight = weight
        self.signal_active = False
        
    def draw(self, surface):
        """绘制连接"""
        start_pos = self.source.position.astype(int)
        end_pos = self.target.position.astype(int)
        
        # 根据权重决定颜色和宽度
        if self.weight > 0:
            color = (100, 100, 255)  # 兴奋性连接 - 蓝色
        else:
            color = (255, 100, 100)  # 抑制性连接 - 红色
            
        line_width = max(1, int(2 * abs(self.weight)))
        pygame.draw.line(surface, color, start_pos, end_pos, line_width)
        
        # 信号传递效果
        if self.signal_active:
            progress = (pygame.time.get_ticks() // 30) % 100 / 100.0
            pulse_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            pulse_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
            pygame.draw.circle(surface, (255, 255, 255), (pulse_x, pulse_y), 3)
