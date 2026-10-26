"""PS 食物实体：可消耗资源，由 Membrane.auto_ingest / Environment 管理（非 SR 梯度源）。

排错: SR 营养场见 `nutrient_gradient_at`；见 `builtin/README.md`。
"""

from typing import Dict, Any
import numpy as np
from core.Lotucosm.entity import EntityBase


class Food(EntityBase):
    """食物实体类

    食物是环境中的可消耗资源，具有能量值和位置信息。
    生物体可以通过接触食物来获取能量，食物被消耗后会从环境中移除。

    属性:
        energy: float - 食物提供的能量值
        consumed: bool - 食物是否已被消耗
        decay_rate: float - 食物衰减率（随时间减少）
        max_age: int - 食物最大存在时间
    """

    def __init__(self, food_id: str = None, **kwargs: Any):
        """初始化食物实体。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 设置默认参数
        kwargs.setdefault('entity_type', 'food')
        kwargs.setdefault('size', 8.0)
        kwargs.setdefault('color', (100, 200, 100))

        # 调用父类初始化
        super().__init__(food_id, **kwargs)

        # 食物特有属性
        self.energy = float(kwargs.get('energy', 20.0))
        self.consumed = False
        self.decay_rate = float(kwargs.get('decay_rate', 0.001))
        self.max_age = int(kwargs.get('max_age', 1000))

        # 初始能量（用于计算衰减）
        self.initial_energy = self.energy

    def update(self, delta_time: float = 1.0) -> None:
        """更新食物状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 调用父类更新
        super().update(delta_time)

        # 能量衰减
        if not self.consumed:
            self.energy -= self.initial_energy * self.decay_rate * delta_time

            # 能量耗尽或超过最大年龄时停用
            if self.energy <= 0 or self.age >= self.max_age:
                self.deactivate()

    def consume(self) -> float:
        """消耗食物，返回能量值。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.consumed or not self.active:
            return 0.0

        self.consumed = True
        self.deactivate()
        return self.energy

    def draw(self, surface: Any) -> None:
        """渲染显示食物。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.visible or not self.active:
            return

        try:
            import pygame
            pos = self.position.astype(int)

            # 绘制食物主体（多层圆圈模拟立体感）
            for i in range(3, 0, -1):
                alpha = int(100 + i * 50)
                radius = int(self.radius - i)
                if radius > 0:
                    # 创建半透明表面
                    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
                    surface.blit(s, (pos[0] - radius, pos[1] - radius))

            # 绘制食物边框
            pygame.draw.circle(surface, (50, 150, 50), pos, int(self.radius), 2)

            # 绘制高光效果
            highlight_pos = (int(pos[0] - self.radius * 0.3), int(pos[1] - self.radius * 0.3))
            pygame.draw.circle(surface, (150, 255, 150), highlight_pos, 2)

        except ImportError:
            pass

    def get_status(self) -> Dict[str, Any]:
        """获取食物状态信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        status = super().get_status()
        status.update({
            'energy': self.energy,
            'consumed': self.consumed,
            'energy_percentage': (self.energy / self.initial_energy * 100) if self.initial_energy > 0 else 0
        })
        return status

    def __repr__(self) -> str:
        """返回食物的字符串表示

        返回:
            str - 食物的字符串表示
        """
        return f"Food(id={self.id}, pos={self.position}, energy={self.energy:.1f})"
