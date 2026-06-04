# -*- coding: utf-8
"""SR 实体视觉组件：Unity SpriteRenderer 式 sprite/flip/anim 字段。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class SrEntityVisual:
    sprite: str = ""
    flip_x: bool = False
    alpha: float = 1.0
    anim: str = ""
    frame: int = -1


def parse_sr_visual(raw: Any, *, sprite_path: Optional[str] = None) -> SrEntityVisual:
    """从 .pond 实体 sr_visual 或编辑器 sprite_path 解析。"""
    vis = SrEntityVisual()
    if isinstance(raw, Mapping):
        sp = raw.get("sprite")
        if isinstance(sp, str) and sp.strip():
            vis.sprite = sp.strip()
        if raw.get("flip_x") is True:
            vis.flip_x = True
        try:
            vis.alpha = max(0.0, min(1.0, float(raw.get("alpha", 1.0))))
        except (TypeError, ValueError):
            pass
        an = raw.get("anim")
        if isinstance(an, str) and an.strip():
            vis.anim = an.strip()
        try:
            vis.frame = int(raw.get("frame", -1))
        except (TypeError, ValueError):
            vis.frame = -1
    if not vis.sprite and sprite_path:
        vis.sprite = str(sprite_path).replace("\\", "/")
    return vis


def ensure_entity_visual(entity: Any) -> SrEntityVisual:
    vis = getattr(entity, "sr_visual", None)
    if isinstance(vis, SrEntityVisual):
        return vis
    vis = SrEntityVisual()
    entity.sr_visual = vis
    return vis
