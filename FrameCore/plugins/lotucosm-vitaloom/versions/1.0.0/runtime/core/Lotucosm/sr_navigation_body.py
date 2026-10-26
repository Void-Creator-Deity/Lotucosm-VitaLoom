# -*- coding: utf-8
"""NavigationBody 最小实现：place_code 网格熟悉度与导航偏置（CX-analog）。

职责: 实体 sr_navigation 状态、熟悉度 EMA、加速度偏置；S3+ 发育阶段启用。
排错: 见 docs/pvaec_developmental_research.md §19。
"""
from __future__ import annotations

import math
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple

DEFAULT_CELL_SIZE = 80.0
MAX_PLACE_CODES = 64
NAVIGATION_BLEND = 18.0
MIN_STAGE_FOR_NAVIGATION = 3


def cell_index(x: float, y: float, cell_size: float) -> Tuple[int, int]:
    size = max(8.0, float(cell_size))
    return int(math.floor(float(x) / size)), int(math.floor(float(y) / size))


def cell_key(ix: int, iy: int) -> str:
    return f"{ix},{iy}"


def ensure_navigation_state(entity: Any) -> Dict[str, Any]:
    """返回 entity.sr_navigation dict（place_familiarity + meta）。"""
    nav = getattr(entity, "sr_navigation", None)
    if isinstance(nav, dict) and isinstance(nav.get("place_familiarity"), dict):
        return nav
    nav = {"place_familiarity": {}, "cell_size": DEFAULT_CELL_SIZE}
    entity.sr_navigation = nav
    return nav


def load_navigation_from_props(entity: Any, props: Mapping[str, Any] | None) -> None:
    if entity is None or not props:
        return
    raw = props.get("initial_navigation")
    if not isinstance(raw, dict):
        return
    nav = ensure_navigation_state(entity)
    fam = raw.get("place_familiarity")
    if isinstance(fam, dict):
        nav["place_familiarity"] = {
            str(k): max(0.0, min(1.0, float(v)))
            for k, v in fam.items()
            if isinstance(k, (str, int))
        }
    try:
        nav["cell_size"] = float(raw.get("cell_size", DEFAULT_CELL_SIZE))
    except (TypeError, ValueError):
        nav["cell_size"] = DEFAULT_CELL_SIZE


def navigation_state_to_props(entity: Any) -> Dict[str, Any]:
    nav = getattr(entity, "sr_navigation", None)
    if not isinstance(nav, dict):
        return {"place_familiarity": {}, "cell_size": DEFAULT_CELL_SIZE}
    fam = nav.get("place_familiarity", {})
    if not isinstance(fam, dict):
        fam = {}
    decayed = {str(k): float(v) * 0.55 for k, v in fam.items()}
    return {"place_familiarity": decayed, "cell_size": float(nav.get("cell_size", DEFAULT_CELL_SIZE))}


def update_place_familiarity(
    entity: Any,
    ox: float,
    oy: float,
    success: float,
    *,
    cell_size: float = DEFAULT_CELL_SIZE,
    alpha: float = 0.08,
) -> None:
    """verify 成功时在所在 place_code 上累积熟悉度。"""
    if float(success) < 0.55:
        return
    nav = ensure_navigation_state(entity)
    size = float(nav.get("cell_size", cell_size))
    ix, iy = cell_index(ox, oy, size)
    key = cell_key(ix, iy)
    fam: Dict[str, float] = nav["place_familiarity"]
    prev = float(fam.get(key, 0.0))
    fam[key] = min(1.0, prev + alpha * float(success))
    if len(fam) > MAX_PLACE_CODES:
        weakest = min(fam.keys(), key=lambda k: float(fam[k]))
        if weakest != key:
            del fam[weakest]


def navigation_acceleration_bias(
    entity: Any,
    ox: float,
    oy: float,
    *,
    cell_size: Optional[float] = None,
    blend: float = NAVIGATION_BLEND,
) -> Tuple[float, float]:
    """朝高熟悉度邻近格子施加弱偏置（route familiarity）。"""
    nav = getattr(entity, "sr_navigation", None)
    if not isinstance(nav, dict):
        return 0.0, 0.0
    fam: Mapping[str, float] = nav.get("place_familiarity", {})
    if not fam:
        return 0.0, 0.0
    size = float(cell_size or nav.get("cell_size", DEFAULT_CELL_SIZE))
    cix, ciy = cell_index(ox, oy, size)
    best_dx, best_dy = 0.0, 0.0
    best_score = 0.0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            key = cell_key(cix + dx, ciy + dy)
            score = float(fam.get(key, 0.0))
            if score > best_score:
                best_score = score
                best_dx, best_dy = float(dx), float(dy)
    if best_score <= 0.05:
        return 0.0, 0.0
    mag = math.hypot(best_dx, best_dy)
    if mag <= 1e-6:
        return 0.0, 0.0
    return best_dx / mag * blend * best_score, best_dy / mag * blend * best_score


def navigation_enabled_for_stage(developmental_ladder_enabled: bool, developmental_stage: int) -> bool:
    if not developmental_ladder_enabled:
        return True
    return int(developmental_stage) >= MIN_STAGE_FOR_NAVIGATION


def top_place_code(entity: Any) -> Optional[str]:
    nav = getattr(entity, "sr_navigation", None)
    if not isinstance(nav, dict):
        return None
    fam = nav.get("place_familiarity", {})
    if not isinstance(fam, dict) or not fam:
        return None
    return max(fam.keys(), key=lambda k: float(fam[k]))
