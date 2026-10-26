# -*- coding: utf-8
"""SR 2D 物理引擎（vitalloom.engine.sr2d 官方能力）。

与 PS 莲池 ``builtin/systems/physics_engine.py`` 分离：本包只服务 GameViewport 场景运行时。
PVAEC 轨：弹簧网络 + 圆体接触 + 冲量；游戏轨：墙 AABB + mover 分离。
"""

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.adapter import (
    CppSrPhysics2DAdapter,
    PythonSrPhysics2DAdapter,
    RustSrPhysics2DAdapter,
    SrPhysics2DAdapter,
    describe_sr2d_adapter,
    SR2D_ABI_VERSION,
    SR2D_INPUT_CONTRACT,
    build_sr2d_runtime_provenance,
    is_cpp_sr2d_available,
    is_native_sr2d_available,
    is_rust_sr2d_available,
    make_default_adapter,
)
from core.Lotucosm.sr_physics2d.mode import Physics2DMode, infer_physics2d_mode
from core.Lotucosm.sr_physics2d.world import SrPhysics2DWorld

__all__ = [
    "SrPhysics2DConfig",
    "SrPhysics2DAdapter",
    "CppSrPhysics2DAdapter",
    "PythonSrPhysics2DAdapter",
    "RustSrPhysics2DAdapter",
    "describe_sr2d_adapter",
    "SR2D_ABI_VERSION",
    "SR2D_INPUT_CONTRACT",
    "build_sr2d_runtime_provenance",
    "is_cpp_sr2d_available",
    "is_native_sr2d_available",
    "is_rust_sr2d_available",
    "make_default_adapter",
    "SrPhysics2DWorld",
    "Physics2DMode",
    "infer_physics2d_mode",
]
