# -*- coding: utf-8
"""低分辨率 2D 扩散场（营养 + 环境），可选替代解析势梯度。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class SrFieldGridConfig:
    enabled: bool = False
    cell_size: float = 48.0
    diffusion: float = 0.22
    decay: float = 0.04
    source_strength: float = 1.0

    @classmethod
    def from_scene(cls, raw: Mapping[str, Any] | None) -> "SrFieldGridConfig":
        if not isinstance(raw, dict):
            return cls()
        kwargs: dict[str, Any] = {}
        if "enabled" in raw:
            kwargs["enabled"] = bool(raw["enabled"])
        for key, default in (
            ("cell_size", cls.cell_size),
            ("diffusion", cls.diffusion),
            ("decay", cls.decay),
            ("source_strength", cls.source_strength),
        ):
            try:
                kwargs[key] = float(raw[key])
            except (KeyError, TypeError, ValueError):
                kwargs[key] = default
        return cls(**kwargs)

    @classmethod
    def from_scene_data(cls, scene_data: Mapping[str, Any]) -> "SrFieldGridConfig":
        raw = scene_data.get("sr_field_grid")
        if isinstance(raw, dict):
            return cls.from_scene(raw)
        pond = scene_data.get("pond_config")
        if isinstance(pond, dict):
            nested = pond.get("sr_field_grid")
            if isinstance(nested, dict):
                return cls.from_scene(nested)
        return cls()


class SrFieldGrid:
    """双通道标量场：nutrient / ambient。"""

    def __init__(self, width: float, height: float, config: SrFieldGridConfig) -> None:
        self.config = config
        self.enabled = bool(config.enabled)
        cs = max(16.0, float(config.cell_size))
        self.cell_size = cs
        self.width = float(width)
        self.height = float(height)
        self.cols = max(4, int(math.ceil(width / cs)))
        self.rows = max(4, int(math.ceil(height / cs)))
        n = self.cols * self.rows
        self._nut = [0.0] * n
        self._amb = [0.0] * n
        self._nut_next = [0.0] * n
        self._amb_next = [0.0] * n

    def _idx(self, ix: int, iy: int) -> int:
        ix = max(0, min(self.cols - 1, ix))
        iy = max(0, min(self.rows - 1, iy))
        return iy * self.cols + ix

    def _world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        ix = int(x / self.cell_size)
        iy = int(y / self.cell_size)
        return ix, iy

    def _sample(self, grid: list[float], x: float, y: float) -> float:
        fx = x / self.cell_size - 0.5
        fy = y / self.cell_size - 0.5
        ix = int(math.floor(fx))
        iy = int(math.floor(fy))
        tx = fx - ix
        ty = fy - iy
        i00 = self._idx(ix, iy)
        i10 = self._idx(ix + 1, iy)
        i01 = self._idx(ix, iy + 1)
        i11 = self._idx(ix + 1, iy + 1)
        v00 = grid[i00]
        v10 = grid[i10]
        v01 = grid[i01]
        v11 = grid[i11]
        top = v00 * (1 - tx) + v10 * tx
        bot = v01 * (1 - tx) + v11 * tx
        return top * (1 - ty) + bot * ty

    def _gradient(self, grid: list[float], x: float, y: float, eps: float = 12.0) -> tuple[float, float]:
        c = self._sample(grid, x, y)
        gx = (self._sample(grid, x + eps, y) - self._sample(grid, x - eps, y)) / (2 * eps)
        gy = (self._sample(grid, x, y + eps) - self._sample(grid, x, y - eps)) / (2 * eps)
        return c, gx, gy

    def nutrient_gradient_at(self, x: float, y: float) -> tuple[float, float, float]:
        return self._gradient(self._nut, x, y)

    def ambient_gradient_at(self, x: float, y: float) -> tuple[float, float, float]:
        return self._gradient(self._amb, x, y)

    def step(
        self,
        entities: Sequence[Any],
        emissions_prev: Mapping[str, float],
        dt: float,
        *,
        niche_pressure: float = 0.0,
    ) -> None:
        if not self.enabled or dt <= 0.0:
            return
        from core.Lotucosm.scene_runtime_world_state import well_scale_from_niche_pressure

        diff = max(0.0, min(0.49, float(self.config.diffusion)))
        decay = max(0.0, min(1.0, float(self.config.decay) * dt))
        strength = max(0.0, float(self.config.source_strength))
        well_q = well_scale_from_niche_pressure(niche_pressure)

        for row in range(self.rows):
            for col in range(self.cols):
                i = row * self.cols + col
                self._nut_next[i] = self._nut[i] * (1.0 - decay)
                self._amb_next[i] = self._amb[i] * (1.0 - decay)

        for ent in entities:
            et = str(getattr(ent, "entity_type", ""))
            px = float(ent.position[0])
            py = float(ent.position[1])
            col, row = self._world_to_cell(px, py)
            i = self._idx(col, row)
            rr = max(4.0, float(getattr(ent, "radius", 12.0)))
            eid = str(getattr(ent, "id", ""))
            q = float(emissions_prev.get(eid, getattr(ent, "emission_strength", 0.0)))
            depl = float(getattr(ent, "_sr_field_depletion", 0.0))
            if et == "nutrient":
                mod = max(0.05, 1.0 - depl * 0.9)
                self._nut_next[i] += strength * mod * (rr / 24.0) ** 2
            elif et == "environment_well":
                self._amb_next[i] += strength * well_q * (rr / 30.0) ** 2
            elif et == "actuator" and q > 0.05:
                self._amb_next[i] += strength * q * 0.35

        for row in range(self.rows):
            for col in range(self.cols):
                i = row * self.cols + col
                acc_n = self._nut_next[i] * (1.0 - 4 * diff)
                acc_a = self._amb_next[i] * (1.0 - 4 * diff)
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    j = self._idx(col + dc, row + dr)
                    acc_n += diff * self._nut_next[j]
                    acc_a += diff * self._amb_next[j]
                self._nut[i] = max(0.0, acc_n)
                self._amb[i] = max(0.0, acc_a)
