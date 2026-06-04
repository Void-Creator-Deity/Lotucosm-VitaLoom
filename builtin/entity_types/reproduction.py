"""PS 繁殖策略辅助：能量阈值与代数递增（非 SR 膜繁殖模板）。

排错: SR 繁殖见 `sr_membrane_topology`；见 `builtin/README.md`。
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from core.VitaLoom.core.logger import get_logger

if TYPE_CHECKING:
    from builtin.entity_types.organism import Organism
    from builtin.systems.inheritance import InheritanceSystem
    from core.Lotucosm.pond import Pond

logger = get_logger("Reproduction")

__all__ = ["try_simple_reproduction"]


def try_simple_reproduction(
    parent: "Organism",
    pond: "Pond",
    *,
    min_energy_ratio: float = 0.55,
    cost_ratio: float = 0.35,
    use_inheritance: bool = False,
    inheritance_system: Optional["InheritanceSystem"] = None,
    min_age: int | None = None,
    min_health_ratio: float | None = None,
) -> Optional["Organism"]:
    """在能量充足时为 parent 生成一个后代并加入莲池。

    use_inheritance=False：沿用原 IntelligentOrganism 直建后代。
    use_inheritance=True：通过 InheritanceSystem.inherit 走组件/记忆基因继承（子类类型与 inherit 返回一致，一般为 Organism）。
    """
    try:
        max_e = float(getattr(parent, "max_energy", 100.0) or 100.0)
        energy = float(getattr(parent, "energy", 0.0) or 0.0)
        if energy < max_e * min_energy_ratio:
            return None
        if min_age is not None and int(getattr(parent, "age", 0) or 0) < int(min_age):
            return None
        if min_health_ratio is not None:
            mh = float(getattr(parent, "max_health", 0.0) or 0.0)
            if mh > 0:
                hr = float(getattr(parent, "health", 0.0) or 0.0) / mh
                if hr < float(min_health_ratio):
                    return None

        jitter = np.random.randn(2).astype(float) * 8.0
        pos = np.asarray(parent.position, dtype=float) + jitter
        pos[0] = float(np.clip(pos[0], 0.0, max(1.0, pond.size[0] - 1)))
        pos[1] = float(np.clip(pos[1], 0.0, max(1.0, pond.size[1] - 1)))
        pos_tuple = (float(pos[0]), float(pos[1]))

        parent.energy = max(0.0, energy - max_e * cost_ratio)
        parent.offspring_count = int(getattr(parent, "offspring_count", 0) or 0) + 1

        if use_inheritance:
            from builtin.systems.inheritance import InheritanceSystem

            inh = inheritance_system or InheritanceSystem()
            child = inh.inherit(parent, pos_tuple)
            child.energy = min(float(getattr(child, "max_energy", max_e) or max_e), max_e * 0.45)
        else:
            from builtin.entity_types.intelligent_organism import IntelligentOrganism

            nid = f"offspring_{uuid.uuid4().hex[:8]}"
            gen = int(getattr(parent, "generation", 1) or 1) + 1
            child = IntelligentOrganism(
                organism_id=nid,
                position=pos_tuple,
                name=f"offspring_{nid}",
                generation=gen,
                energy=max_e * 0.45,
            )

        if hasattr(child, "pond"):
            child.pond = pond  # type: ignore[attr-defined]

        pond.add_organism(child)
        logger.info("繁殖成功: parent=%s child=%s", parent.id, child.id)
        return child
    except Exception as exc:
        logger.warning("繁殖失败: %s", exc)
        return None
