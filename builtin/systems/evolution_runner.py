"""PS 莲池世代边界：达 `evolution_generation_interval` 时调用 PVAECOrchestrator 替换种群。

架构数据流::

    Pond.update → EvolutionRunner.apply_generation → PVAECOrchestrator.run_cycle

排错: 见 `builtin/README.md`（世代不触发）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.VitaLoom.core.logger import get_logger

if TYPE_CHECKING:
    from builtin.systems.pvaec_orchestrator import PVAECOrchestrator
    from core.Lotucosm.pond import Pond

logger = get_logger("EvolutionRunner")


class EvolutionRunner:
    """在 Pond.update 达到世代间隔时，运行编排器并原子替换 organisms。"""

    @staticmethod
    def apply_generation(pond: "Pond", orchestrator: "PVAECOrchestrator") -> None:
        """EvolutionRunner.apply_generation。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        orgs = list(pond.organisms.values())
        if not orgs:
            return
        try:
            new_orgs = orchestrator.run_cycle(orgs, pond)
        except Exception as exc:
            logger.warning("世代推进失败: %s", exc)
            return

        for oid in list(pond.organisms.keys()):
            pond.remove_organism(oid)
        for o in new_orgs:
            pond.add_organism(o)

        pond.iteration = int(getattr(pond, "iteration", 0) or 0) + 1
        logger.info("莲池世代已推进: iteration=%s 种群=%s", pond.iteration, len(pond.organisms))
