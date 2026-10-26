# -*- coding: utf-8
"""SR 视口宿主接缝：replay / ecology 经 services 访问。"""
from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable

from core.VitaLoom.core.service_keys import SIMULATION_SR_HOST


@runtime_checkable
class ISimulationSrHost(Protocol):
    def set_ps_replay_overlay_points(self, points: List[Tuple[float, float]]) -> None: ...
    def get_sr_ecology_snapshot(self) -> Dict[str, Any]: ...
    def is_sr_playing(self) -> bool: ...
    def refresh_canvas(self) -> None: ...


class _NullSrHost:
    def set_ps_replay_overlay_points(self, points: List[Tuple[float, float]]) -> None:
        pass

    def get_sr_ecology_snapshot(self) -> Dict[str, Any]:
        return {}

    def is_sr_playing(self) -> bool:
        return False

    def refresh_canvas(self) -> None:
        pass


def get_sr_host(source: Any = None) -> ISimulationSrHost:
    """Resolve SR Host from explicit registry/context or legacy editor state."""
    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    registry = resolve_runtime_capability_registry(source)
    if registry is None and source is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(get_existing_editor_context())
        except Exception:
            registry = None
    host = registry.get(SIMULATION_SR_HOST) if registry is not None else None
    if isinstance(host, ISimulationSrHost):
        return host
    return _NullSrHost()
