# -*- coding: utf-8
"""SR 2D 物理世界：单入口 step（弹簧 → 积分 → 接触）。"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Sequence, TYPE_CHECKING

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.integrator import integrate_all
from core.Lotucosm.sr_physics2d.pvaec_contacts import resolve_pvaec_contacts

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport


class Physics2DMode(str, Enum):
    PVAEC = "pvaec"
    GAME = "game"


class SrPhysics2DWorld:
    """官方 2D 物理步进（``vitalloom.engine.sr2d`` / ``sr.physics2d``）。

    **通用**：同一套引擎服务
    - ``projects/pvaec-细胞演化``（``Physics2DMode.PVAEC``）
    - ``projects/织机教程-*``（``Physics2DMode.GAME``）

    由 ``GameViewport`` 按 ``sr_game_mode`` 自动选 mode；``.pond`` 可选 ``sr_physics2d`` 调参。
    """

    def __init__(self, config: SrPhysics2DConfig | None = None) -> None:
        self.config = config or SrPhysics2DConfig()

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

        ent_list = list(entities)

        if mode == Physics2DMode.PVAEC and springs:
            from core.Lotucosm.sr_link_physics import step_spring_network

            step_spring_network(ent_list, springs, dt)

        integrate_all(ent_list, dt, width, height, self.config)

        if mode == Physics2DMode.PVAEC:
            resolve_pvaec_contacts(
                ent_list,
                width=width,
                height=height,
                config=self.config,
            )
        else:
            from core.Lotucosm.sr_physics2d.game_contacts import resolve_game_contacts

            resolve_game_contacts(ent_list, config=self.config)

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
