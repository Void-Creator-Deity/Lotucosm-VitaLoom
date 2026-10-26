# -*- coding: utf-8 -*-
"""世界/莲池画布视口（OrganismCanvas）：非 SR 的 2D 实体绘制占位。

排错: 与 scene_viewport 分工；SR 运行时优先 game_viewport。
"""

from core.VitaLoom.viewports.scene_viewport import SceneViewport

OrganismCanvas = SceneViewport

__all__ = ["OrganismCanvas"]
