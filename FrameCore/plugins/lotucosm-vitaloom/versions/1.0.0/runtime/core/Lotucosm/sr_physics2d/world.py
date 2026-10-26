# -*- coding: utf-8
"""SR 2D 物理世界：单入口 step（弹簧 → 积分 → 接触）。"""

from __future__ import annotations

from typing import Any, Iterable, Sequence, TYPE_CHECKING

from core.Lotucosm.sr_physics2d.adapter import (
    SrPhysics2DAdapter,
    describe_sr2d_adapter,
    make_default_adapter,
)
from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.mode import Physics2DMode

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport


class SrPhysics2DWorld:
    """官方 2D 物理步进（``vitalloom.engine.sr2d`` / ``sr.physics2d``）。

    **通用**：同一套引擎服务
    - PVAEC 示范工程（``Physics2DMode.PVAEC``）
    - 游戏/教程工程（``Physics2DMode.GAME``，``sr_engine_mode: game``）

    由 ``GameViewport`` 按 ``sr_game_mode`` 自动选 mode；``.pond`` 可选 ``sr_physics2d`` 调参。
    """

    def __init__(
        self,
        config: SrPhysics2DConfig | None = None,
        *,
        adapter: SrPhysics2DAdapter | None = None,
        backend_request: str | None = None,
    ) -> None:
        self.config = config or SrPhysics2DConfig()
        self.backend_request = (
            str(backend_request).strip().lower()
            if backend_request is not None
            else None
        )
        self.adapter = adapter or make_default_adapter(self.backend_request)

    def step(
        self,
        entities: Sequence[Any],
        dt: float,
        width: float,
        height: float,
        *,
        mode: Physics2DMode,
        springs: Iterable[Any] | None = None,
    ) -> None:
        if dt <= 0.0 or not entities:
            return

        self.adapter.step(
            entities,
            dt=dt,
            width=width,
            height=height,
            mode=mode,
            springs=springs,
            config=self.config,
        )

    def step_for_viewport(
        self,
        host: "GameViewport",
        entities: Sequence[Any],
        dt: float,
        width: float,
        height: float,
    ) -> None:
        """GameViewport / 瘦 tick 共用：按 ``host._sr_game_mode`` 选 PVAEC 或 GAME。"""
        game = bool(getattr(host, "_sr_game_mode", False))
        mode = Physics2DMode.GAME if game else Physics2DMode.PVAEC
        springs = None if game else getattr(host, "_sr_spring_links", ())
        self.step(
            entities,
            dt,
            width,
            height,
            mode=mode,
            springs=springs,
        )

    def backend_capability(self) -> dict[str, Any]:
        """Describe the selected adapter for checkpoint and parity evidence."""
        return describe_sr2d_adapter(self.adapter)
