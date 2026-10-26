# -*- coding: utf-8
"""2D 物理参数：来自 .pond ``sr_physics2d`` 或 ``pond_config.sr_physics2d``。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class SrPhysics2DConfig:
    linear_damping: float = 0.98
    boundary_bounce: float = 0.85
    restitution: float = 0.34
    friction: float = 0.18
    contact_slop: float = 0.85
    contact_correction: float = 0.42
    contact_iterations: int = 4
    pvaec_broadphase: str = "bruteforce"
    game_contact_iterations: int = 3
    game_mover_padding: float = 8.0
    max_speed: float = 420.0

    @classmethod
    def from_scene(cls, raw: Mapping[str, Any] | None) -> "SrPhysics2DConfig":
        if not isinstance(raw, dict):
            return cls()
        kwargs: dict[str, Any] = {}

        def _float(key: str, default: float) -> float:
            try:
                return float(raw[key])
            except (KeyError, TypeError, ValueError):
                return default

        def _int(key: str, default: int) -> int:
            try:
                return int(raw[key])
            except (KeyError, TypeError, ValueError):
                return default

        kwargs["linear_damping"] = _float("linear_damping", cls.linear_damping)
        kwargs["boundary_bounce"] = _float("boundary_bounce", cls.boundary_bounce)
        kwargs["restitution"] = _float("restitution", cls.restitution)
        kwargs["friction"] = _float("friction", cls.friction)
        kwargs["contact_slop"] = _float("contact_slop", cls.contact_slop)
        kwargs["contact_correction"] = _float("contact_correction", cls.contact_correction)
        kwargs["contact_iterations"] = _int("contact_iterations", cls.contact_iterations)
        broadphase = str(raw.get("pvaec_broadphase", cls.pvaec_broadphase)).strip().lower()
        kwargs["pvaec_broadphase"] = (
            broadphase if broadphase in {"spatial_hash", "bruteforce"} else cls.pvaec_broadphase
        )
        kwargs["game_contact_iterations"] = _int(
            "game_contact_iterations", cls.game_contact_iterations
        )
        kwargs["game_mover_padding"] = _float("game_mover_padding", cls.game_mover_padding)
        kwargs["max_speed"] = _float("max_speed", cls.max_speed)
        return cls(**kwargs)

    @classmethod
    def from_scene_data(cls, scene_data: Mapping[str, Any]) -> "SrPhysics2DConfig":
        raw = scene_data.get("sr_physics2d")
        if isinstance(raw, dict):
            return cls.from_scene(raw)
        pond = scene_data.get("pond_config")
        if isinstance(pond, dict):
            nested = pond.get("sr_physics2d")
            if isinstance(nested, dict):
                return cls.from_scene(nested)
        return cls()
