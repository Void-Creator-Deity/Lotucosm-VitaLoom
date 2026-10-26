# -*- coding: utf-8 -*-
"""PS 精灵渲染组件：绑定资源路径供场景/视口绘制（非 SR Pvaec 膜拓扑）。

职责: 加载 sprite_path 并在 draw 中 blit 到 Pygame surface。
时机: Organism/场景绘制阶段调用 draw(surface, position)。
不变量: 无 pygame 时仅 warning，不抛异常中断主循环。
排错: 不显示 → 查路径与 pygame 是否安装；见 builtin/README.md。
"""
from typing import Optional, Any

from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger


logger = get_logger("SpriteRenderer")


class SpriteRenderer(ComponentBase):
    """PS 精灵渲染：缓存 pygame Surface，支持翻转与透明度。"""

    def __init__(self, sprite_path: Optional[str] = None):
        """SpriteRenderer.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__(component_id="sprite_renderer", component_type="renderer")
        self.sprite_path = sprite_path
        self.flip_x = False
        self.flip_y = False
        self.opacity = 1.0
        self._cached_sprite = None

    def update(self, delta_time: float):
        """每帧更新（当前无时间驱动逻辑，兼容系统调度）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        _ = delta_time

    def draw(self, surface: Any, position: Any):
        """在 surface 上绘制精灵；position 为 (x, y) 中心。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if not self.sprite_path:
            return

        try:
            import pygame

            if self._cached_sprite is None:
                self._cached_sprite = pygame.image.load(self.sprite_path).convert_alpha()

            sprite = self._cached_sprite
            if self.flip_x or self.flip_y:
                sprite = pygame.transform.flip(sprite, self.flip_x, self.flip_y)
            if self.opacity < 1.0:
                sprite = sprite.copy()
                sprite.set_alpha(int(max(0.0, min(1.0, self.opacity)) * 255))

            pos_x, pos_y = int(position[0]), int(position[1])
            rect = sprite.get_rect(center=(pos_x, pos_y))
            surface.blit(sprite, rect)
        except ImportError:
            logger.warning("SpriteRenderer 绘制跳过：pygame 不可用")
        except Exception as e:
            logger.warning("SpriteRenderer 绘制失败: %s", e)
