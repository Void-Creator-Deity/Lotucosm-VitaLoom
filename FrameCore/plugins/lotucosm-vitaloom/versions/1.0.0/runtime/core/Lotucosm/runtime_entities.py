"""运行时实体工厂：按类型字符串在莲池中实例化并注册（供 ScriptBase 等脚本层调用）。

架构数据流::

    ScriptBase.instantiate → instantiate_entity → pond.add_organism / add_entity

勿依赖编辑器插件或 builtin 以外的隐式注册；未知类型回退 EntityBase。
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

import numpy as np

from core.VitaLoom.core.logger import get_logger

logger = get_logger("RuntimeEntities")

__all__ = ["instantiate_entity"]


def instantiate_entity(
    entity_type: str,
    pond: Any,
    position: Optional[Tuple[float, float]] = None,
    **kwargs: Any,
):
    """根据类型字符串在指定莲池中创建实体并注册。

    职责:
        解析 entity_type（organism/intelligent/simple/其他），构造实体并写入 pond。

    时机:
        ScriptBase.instantiate、项目脚本动态生成单位时。

    不变量:
        成功时 entity.pond 指向入参 pond；Organism 走 add_organism，其余走 add_entity。

    排错:
        返回 None → 日志「未知类型」或注册异常；先确认 pond 非空、类型拼写与 builtin 实体可导入。
    """
    from core.Lotucosm.entity import EntityBase
    from builtin.entity_types.organism import Organism

    pos = position if position is not None else (50.0, 50.0)
    entity_id = kwargs.pop("id", None) or kwargs.pop("entity_id", None)
    identity_source = kwargs.pop("identity_source", None)
    if identity_source is None:
        identity_source = getattr(pond, "identity_source", None)
    if identity_source is not None and not callable(getattr(identity_source, "next", None)):
        raise TypeError("identity_source must expose next(domain)")
    identity_snapshot = (
        identity_source.snapshot() if identity_source is not None else None
    )

    def compensate_identity() -> None:
        if identity_source is None or identity_snapshot is None:
            return
        try:
            identity_source.restore(identity_snapshot)
        except Exception as exc:
            logger.error("instantiate_entity: identity compensation failed: %s", exc)

    def generated_id(prefix: str) -> str:
        if identity_source is not None:
            return identity_source.next("entity")
        return f"{prefix}_{abs(hash((et, pos))) % 10_000_000}"

    entity = None
    et = (entity_type or "").strip().lower()

    if et in ("organism",):
        from builtin.entity_types.organism import Organism as O

        oid = entity_id or generated_id("organism")
        try:
            entity = O(organism_id=oid, position=pos, **kwargs)
        except Exception:
            compensate_identity()
            raise
    elif et in ("intelligent_organism", "smart", "intelligent"):
        from builtin.entity_types.intelligent_organism import IntelligentOrganism

        oid = entity_id or generated_id("intelligent")
        try:
            entity = IntelligentOrganism(organism_id=oid, position=pos, **kwargs)
        except Exception:
            compensate_identity()
            raise
    elif et in ("simple_organism", "simple"):
        try:
            from builtin.entity_types.simple_organism import SimpleOrganism

            oid = entity_id or generated_id("simple")
            entity = SimpleOrganism(organism_id=oid, position=pos, **kwargs)
        except Exception:
            compensate_identity()
            entity = None
    else:
        eid = entity_id or generated_id("entity")
        try:
            entity = EntityBase(entity_id=eid, position=pos, **kwargs)
        except Exception:
            compensate_identity()
            raise

    if entity is None:
        logger.warning("instantiate_entity: 未知类型 %s", entity_type)
        return None

    if hasattr(entity, "pond"):
        entity.pond = pond

    try:
        if isinstance(entity, Organism):
            pond.add_organism(entity)
        else:
            pond.add_entity(entity)
    except Exception as exc:
        if isinstance(entity, Organism):
            remove = getattr(pond, "remove_organism", None)
            if callable(remove):
                remove(str(getattr(entity, "id", "")))
        else:
            remove = getattr(pond, "remove_entity", None)
            if callable(remove):
                remove(entity)
        compensate_identity()
        logger.exception("instantiate_entity: 注册实体失败: %s", exc)
        return None

    return entity
