"""PS 体外组件获取：漂浮物并入 Organism.components。

排错: 见 `builtin/README.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

import numpy as np

from core.VitaLoom.core.logger import get_logger

if TYPE_CHECKING:
    from builtin.components.components_base import ComponentBase
    from builtin.entity_types.organism import Organism
    from core.Lotucosm.pond import Pond

logger = get_logger("ComponentAcquisition")

__all__ = [
    "acquire_floating_component",
    "list_floating_near",
    "evaluate_floating_value",
    "select_best_floating_near",
    "try_acquire_best_floating_near",
]


def list_floating_near(
    pond: "Pond",
    position: np.ndarray,
    radius: float,
) -> List[Any]:
    """返回半径内漂浮组件（依赖组件具备 position 向量）。"""
    out: List[Any] = []
    pos = np.asarray(position, dtype=float)
    for item in list(getattr(pond, "floating_components", []) or []):
        comp = _unwrap_floating_entry(item)
        if comp is None or not hasattr(comp, "position"):
            continue
        if float(np.linalg.norm(np.asarray(comp.position, dtype=float) - pos)) <= radius:
            out.append(comp)
    return out


def _unwrap_floating_entry(item: object) -> Optional["ComponentBase"]:
    if item is None:
        return None
    if isinstance(item, dict) and "component" in item:
        candidate = item.get("component")
        return candidate if candidate is not None else None
    return item  # type: ignore[return-value]


def acquire_floating_component(
    organism: "Organism",
    pond: "Pond",
    component: Union[str, "ComponentBase"],
    *,
    radius: float = 48.0,
) -> bool:
    """将漂浮组件并入 organism：可传入实例或组件 id。

    成功则从 pond.floating_components 移除并 organism.add_component。
    """
    try:
        target: Optional[ComponentBase] = None
        if isinstance(component, str):
            for item in list(pond.floating_components):
                comp = _unwrap_floating_entry(item)
                if comp is not None and getattr(comp, "id", None) == component:
                    target = comp
                    break
        else:
            target = component

        if target is None:
            return False

        pos = np.asarray(organism.position, dtype=float)
        if hasattr(target, "position"):
            d = float(np.linalg.norm(np.asarray(target.position, dtype=float) - pos))
            if d > radius:
                logger.info("体外获取失败：距离过远 %.2f > %.2f", d, radius)
                return False

        # 从漂浮列表移除（兼容裸组件或漂浮系统 dict）
        new_list = []
        for item in pond.floating_components:
            comp = _unwrap_floating_entry(item)
            if comp is target:
                continue
            new_list.append(item)
        pond.floating_components[:] = new_list

        target.organism_id = organism.id
        organism.add_component(target)
        logger.info("体外获取成功: organism=%s component=%s", organism.id, target.id)
        return True
    except Exception as exc:
        logger.warning("体外获取失败: %s", exc)
        return False

def evaluate_floating_value(organism: "Organism", component: Any) -> float:
    """旧版式价值评估：按组件类型与 organism 偏好加权（默认 0.5）。"""
    prefs = getattr(organism, "component_preferences", None) or {}
    ctype = getattr(component, "component_type", None) or type(component).__name__
    key = str(ctype)
    return float(prefs.get(key, 0.5))


def select_best_floating_near(
    organism: "Organism",
    pond: "Pond",
    radius: float,
    *,
    min_value: float = 0.0,
) -> Optional[Any]:
    """在半径内选评估分最高的漂浮组件；低于 min_value 则返回 None。"""
    cands = list_floating_near(pond, organism.position, radius)
    if not cands:
        return None
    best = max(cands, key=lambda c: evaluate_floating_value(organism, c))
    if evaluate_floating_value(organism, best) < min_value:
        return None
    return best


def try_acquire_best_floating_near(
    organism: "Organism",
    pond: "Pond",
    *,
    radius: float = 48.0,
    min_value: float = 0.0,
    capture_cost: float = 0.0,
    max_components: int = 32,
) -> bool:
    """可选策略：挑最有价值组件再并入；capture_cost>0 时从 energy 扣除。"""
    comps = getattr(organism, "components", None)
    n = len(comps) if hasattr(comps, "__len__") else 0
    if n >= max_components:
        return False
    best = select_best_floating_near(organism, pond, radius, min_value=min_value)
    if best is None:
        return False
    if capture_cost > 0:
        e = float(getattr(organism, "energy", 0.0) or 0.0)
        if e < capture_cost:
            return False
        organism.energy = e - capture_cost
    return acquire_floating_component(organism, pond, best, radius=radius)

