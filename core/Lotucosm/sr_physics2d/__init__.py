# -*- coding: utf-8
"""SR 2D 物理引擎（vitalloom.engine.sr2d 官方能力）。

与 PS 莲池 ``builtin/systems/physics_engine.py`` 分离：本包只服务 GameViewport 场景运行时。
PVAEC 轨：弹簧网络 + 圆体接触 + 冲量；游戏轨：墙 AABB + mover 分离。
"""

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.mode import infer_physics2d_mode
from core.Lotucosm.sr_physics2d.world import Physics2DMode, SrPhysics2DWorld

__all__ = [
    "SrPhysics2DConfig",
    "SrPhysics2DWorld",
    "Physics2DMode",
    "infer_physics2d_mode",
]
