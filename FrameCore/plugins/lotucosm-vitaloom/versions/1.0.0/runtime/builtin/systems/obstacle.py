"""PS 障碍物实体：环境中的阻挡体（演示碰撞/查询）。

排错: 见 `builtin/README.md`。
"""

from typing import Dict, Any
import numpy as np
from core.Lotucosm.entity import EntityBase


class Obstacle(EntityBase):
    """障碍物实体类

    障碍物是环境中的静态或动态障碍，生物体无法穿过障碍物。
    障碍物可以是静态的（如石头）或动态的（如移动的障碍）。

    属性:
        solid: bool - 障碍物是否为固体（不可穿过）
        damage: float - 障碍物造成的伤害值
        movable: bool - 障碍物是否可移动
        mass: float - 障碍物质量（用于物理计算）
    """

    def __init__(self, obstacle_id: str = None, **kwargs: Any):
        """初始化障碍物实体。

        
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
        kwargs.setdefault('entity_type', 'obstacle')
        kwargs.setdefault('size', 20.0)
        kwargs.setdefault('color', (100, 100, 100))

        # 调用父类初始化
        super().__init__(obstacle_id, **kwargs)

        # 障碍物特有属性
        self.solid = kwargs.get('solid', True)
        self.damage = float(kwargs.get('damage', 0.0))
        self.movable = kwargs.get('movable', False)
        self.mass = float(kwargs.get('mass', 10.0))

        # 如果不可移动，将速度和加速度设为0
        if not self.movable:
            self.velocity = np.array([0.0, 0.0])
            self.acceleration = np.array([0.0, 0.0])

    def update(self, delta_time: float = 1.0) -> None:
        """更新障碍物状态。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.movable:
            # 可移动障碍物调用父类更新
            super().update(delta_time)
        else:
            # 静态障碍物只更新年龄
            self.age += 1

    def apply_force(self, force: np.ndarray) -> None:
        """施加力到障碍物。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.movable:
            # 根据质量计算加速度（F = ma，所以 a = F/m）
            acceleration = force / self.mass
            self.acceleration += acceleration

    def draw(self, surface: Any) -> None:
        """渲染显示障碍物。

        
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

            # 绘制障碍物主体（多层圆圈模拟立体感）
            for i in range(3, 0, -1):
                alpha = int(80 + i * 40)
                radius = int(self.radius - i * 2)
                if radius > 0:
                    # 创建半透明表面
                    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
                    surface.blit(s, (pos[0] - radius, pos[1] - radius))

            # 绘制障碍物边框
            border_color = (50, 50, 50) if self.solid else (150, 50, 50)
            border_width = 3 if self.solid else 2
            pygame.draw.circle(surface, border_color, pos, int(self.radius), border_width)

            # 绘制纹理效果（简单的点状纹理）
            texture_positions = [
                (int(pos[0] - self.radius * 0.3), int(pos[1] - self.radius * 0.3)),
                (int(pos[0] + self.radius * 0.2), int(pos[1] - self.radius * 0.4)),
                (int(pos[0] - self.radius * 0.2), int(pos[1] + self.radius * 0.3)),
                (int(pos[0] + self.radius * 0.3), int(pos[1] + self.radius * 0.2))
            ]
            for tex_pos in texture_positions:
                pygame.draw.circle(surface, (70, 70, 70), tex_pos, 2)

            # 绘制高光效果
            highlight_pos = (int(pos[0] - self.radius * 0.4), int(pos[1] - self.radius * 0.4))
            pygame.draw.circle(surface, (150, 150, 150), highlight_pos, 3)

            # 如果有伤害，绘制警告标识
            if self.damage > 0:
                warning_pos = (int(pos[0]), int(pos[1] - self.radius - 5))
                pygame.draw.circle(surface, (255, 0, 0), warning_pos, 4)

        except ImportError:
            pass

    def check_collision_with_circle(self, position: np.ndarray, radius: float) -> bool:
        """检测与圆形的碰撞。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.active or not self.solid:
            return False

        distance = np.linalg.norm(self.position - position)
        return distance < (self.radius + radius)

    def get_collision_info(self, position: np.ndarray, radius: float) -> Dict[str, Any]:
        """获取碰撞信息。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.active or not self.solid:
            return {
                'colliding': False,
                'pressure': 0.0,
                'direction': np.array([0.0, 0.0]),
                'damage': 0.0
            }

        distance = np.linalg.norm(self.position - position)

        if distance < (self.radius + radius):
            # 计算碰撞方向（从障碍物指向碰撞物体）
            direction = position - self.position
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)

            # 计算碰撞压力（距离越近压力越大）
            total_radius = self.radius + radius
            pressure = 1.0 - (distance / total_radius)

            return {
                'colliding': True,
                'pressure': pressure,
                'direction': direction,
                'damage': self.damage
            }

        return {
            'colliding': False,
            'pressure': 0.0,
            'direction': np.array([0.0, 0.0]),
            'damage': 0.0
        }

    def get_status(self) -> Dict[str, Any]:
        """获取障碍物状态信息。

        
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
            'solid': self.solid,
            'damage': self.damage,
            'movable': self.movable,
            'mass': self.mass
        })
        return status

    def __repr__(self) -> str:
        """返回障碍物的字符串表示

        返回:
            str - 障碍物的字符串表示
        """
        return f"Obstacle(id={self.id}, pos={self.position}, solid={self.solid})"
