# -*- coding: utf-8 -*-
"""PS 实验用生物体装配：传感器/执行器/记忆/PVAEC 引擎一键挂载。

排错: 见 docs/experiment_guide.md。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from builtin.components.component_factory import ComponentFactory
from core.Lotucosm.memory import MemorySystem

if TYPE_CHECKING:
    from builtin.entity_types.organism import Organism


def equip_ps_organism(
    organism: "Organism",
    *,
    enable_pvaec_cycle: bool = True,
    with_pvaec_engine: bool = False,
) -> None:
    """为生物体挂载标准 PS 闭环组件（感知→行动→内稳态学习）。"""
    factory = ComponentFactory()
    oid = organism.id

    sensor = factory.create_component("Sensor", f"{oid}_sensor", organism_id=oid, name="sensor")
    actuator = factory.create_component("Actuator", f"{oid}_actuator", organism_id=oid, name="actuator")
    organism.add_component(sensor)
    organism.add_component(actuator)

    if with_pvaec_engine:
        engine = factory.create_component("PVAECEngine", f"{oid}_pvaec", organism_id=oid, name="pvaec")
        organism.add_component(engine)

    if enable_pvaec_cycle:
        organism.memory_system = MemorySystem()
        organism.enable_pvaec_cycle_per_tick = True
