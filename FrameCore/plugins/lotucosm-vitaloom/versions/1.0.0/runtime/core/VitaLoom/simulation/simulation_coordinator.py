# -*- coding: utf-8
"""多轨模拟会话协调（C.3）：SR Play 与 PS 批实验并行策略。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Set

from core.VitaLoom.core.logger import get_logger

logger = get_logger("SimulationCoordinator")

EVENT_SNAPSHOT = "simulation_coordinator_state"

_coordinator: Optional["SimulationCoordinator"] = None


class SimulationLane(str, Enum):
    SR_PLAY = "sr_play"
    PS_BATCH = "ps_batch"
    PS_REPLAY = "ps_replay"


@dataclass
class CoordinatorState:
    active_lanes: Set[str] = field(default_factory=set)
    disallow_parallel_sr_ps: bool = False


class SimulationCoordinator:
    def __init__(self, editor_context: Any):
        self._ctx = editor_context
        self._active: Set[SimulationLane] = set()

    def _project_disallow_parallel(self) -> bool:
        cfg = getattr(self._ctx, "current_project_config", None) or {}
        if not isinstance(cfg, dict):
            return False
        return bool(cfg.get("disallow_parallel_sr_ps", False))

    def can_start_lane(self, lane: SimulationLane) -> bool:
        if not self._project_disallow_parallel():
            return True
        if lane == SimulationLane.SR_PLAY:
            return SimulationLane.PS_BATCH not in self._active
        if lane == SimulationLane.PS_BATCH:
            return SimulationLane.SR_PLAY not in self._active
        return True

    def register_lane_start(self, lane: SimulationLane) -> bool:
        if not self.can_start_lane(lane):
            logger.info("协调器拒绝启动 %s（工程禁止 SR+PS 并行）", lane.value)
            return False
        self._active.add(lane)
        self._emit()
        return True

    def register_lane_stop(self, lane: SimulationLane) -> None:
        self._active.discard(lane)
        self._emit()

    def snapshot(self) -> CoordinatorState:
        return CoordinatorState(
            active_lanes={l.value for l in self._active},
            disallow_parallel_sr_ps=self._project_disallow_parallel(),
        )

    def _emit(self) -> None:
        bus = getattr(self._ctx, "event_bus", None)
        if bus is not None and hasattr(bus, "publish"):
            try:
                bus.publish(EVENT_SNAPSHOT, self.snapshot())
            except Exception as exc:
                logger.debug("发布 coordinator 状态失败: %s", exc)


def init_simulation_coordinator(editor_context: Any) -> SimulationCoordinator:
    global _coordinator
    _coordinator = SimulationCoordinator(editor_context)
    editor_context.simulation_coordinator = _coordinator
    return _coordinator


def get_simulation_coordinator() -> Optional[SimulationCoordinator]:
    return _coordinator
