# -*- coding: utf-8 -*-
"""场景运行时 tick 上下文（GameViewport._run_script_tick_batch 构造）。

职责: 只读 peers/environment/inbound_signals；可变 spawn_requests / removal_requests。
时机: 每帧按 organism → sensor → actuator 分批调用 entity.step_scripts(ctx)。

inbound_signals:
    organism/sensor 批 use_prev=True（上帧 sr_channel_out_prev）；
    actuator 批 use_prev=False（当帧 sensor 输出）。见 game_viewport tick 顺序契约。

environment 键（宿主注入）:
    ambient_field, ambient_grad_x/y, nutrient_potential, nutrient_grad_x/y,
    world_load, niche_pressure, world_load_derivative, chemo_gain_scale。

排错: 膜 chemo 异常 → 先查宿主 tick 顺序与 sr_membrane_topology.aggregate_channel_signals。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, List, Mapping, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.VitaLoom.viewports.sr_input_state import SrInputSnapshot
else:
    SrInputSnapshot = Any  # noqa: N806


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class RuntimePeerSnapshot:
    id: str
    entity_type: str
    position: Tuple[float, float]
    radius: float
    distance: float
    surface_gap: float


@dataclass(frozen=True)
class SceneRuntimeTickContext:
    owner_id: str
    owner_type: str
    owner_position: Tuple[float, float]
    owner_radius: float
    bounds: Tuple[int, int]
    simulation_time: float
    delta_time: float
    peers: Tuple[RuntimePeerSnapshot, ...]
    environment: Mapping[str, Any] = field(default_factory=_empty_mapping)
    topology_neighbor_ids: frozenset[str] = field(default_factory=frozenset)
    # 可变列表：由 GameViewport 每帧注入同一实例，脚本可 append 生成请求（SR 内动态实体）。
    spawn_requests: List[Any] = field(default_factory=list)
    # 本帧待移除的实体 id（如营养颗粒被吞噬）；由 GameViewport 在脚本阶段后统一处理。
    removal_requests: List[str] = field(default_factory=list)
    # 游戏模式：对目标 id 扣血（ScriptBase 教程战斗）。
    damage_requests: List[tuple[str, float]] = field(default_factory=list)
    # 游戏模式：飘字 / 挥砍弧等视觉请求。
    fx_requests: List[Any] = field(default_factory=list)
    # SR 能力标记（只读）；例如 dynamic_spawn / dynamic_despawn。
    capabilities: Mapping[str, Any] = field(default_factory=_empty_mapping)
    # 拓扑聚合后的入站通道信号（只读），如 chemo。
    inbound_signals: Mapping[str, float] = field(default_factory=_empty_mapping)
    input: SrInputSnapshot = field(default_factory=lambda: _empty_input())
    # Host-owned diagnostic sink; deliberately excluded from serialized state.
    # It lets the phase runner record runtime script failures without making
    # scripts depend on the Qt host or a second error authority.
    runtime_failure_sink: Any = None


def _empty_input() -> Any:
    from core.VitaLoom.viewports.sr_input_state import SrInputState

    return SrInputState.empty_snapshot()


def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return float(math.hypot(ax - bx, ay - by))


def build_scene_runtime_tick_context(
    *,
    owner: Any,
    peers: Iterable[Any],
    bounds: Tuple[int, int],
    simulation_time: float,
    delta_time: float,
    neighbor_radius_scale: float = 6.0,
    min_horizon: float = 0.0,
    environment: Mapping[str, Any] | None = None,
    topology_neighbor_ids: Iterable[str] | None = None,
    spawn_requests: List[Any] | None = None,
    removal_requests: List[str] | None = None,
    damage_requests: List[tuple[str, float]] | None = None,
    fx_requests: List[Any] | None = None,
    capabilities: Mapping[str, Any] | None = None,
    inbound_signals: Mapping[str, float] | None = None,
    input: Any | None = None,
    runtime_failure_sink: Any = None,
) -> SceneRuntimeTickContext:
    ox = float(owner.position[0])
    oy = float(owner.position[1])
    r = float(getattr(owner, "radius", 18.0))
    horizon = max(r * neighbor_radius_scale, 120.0)
    if min_horizon > 0:
        horizon = max(horizon, min_horizon)

    topo = frozenset(str(x) for x in topology_neighbor_ids) if topology_neighbor_ids else frozenset()

    snap_list: List[RuntimePeerSnapshot] = []
    for other in peers:
        if other is owner:
            continue
        px = float(other.position[0])
        py = float(other.position[1])
        d = _dist(ox, oy, px, py)
        if d > horizon:
            continue
        r_peer = float(getattr(other, "radius", 18.0))
        surface_gap = max(0.0, d - r - r_peer)
        snap_list.append(
            RuntimePeerSnapshot(
                id=str(getattr(other, "id", "")),
                entity_type=str(getattr(other, "entity_type", "")),
                position=(px, py),
                radius=r_peer,
                distance=d,
                surface_gap=surface_gap,
            )
        )
    snap_list.sort(key=lambda s: (s.surface_gap, s.distance))

    env_map: dict[str, Any] = {
        "ambient_field": 0.0,
        "ambient_grad_x": 0.0,
        "ambient_grad_y": 0.0,
    }
    if environment:
        env_map.update(dict(environment))

    cap_map: dict[str, Any] = {}
    if capabilities:
        cap_map.update(dict(capabilities))

    in_map: dict[str, float] = {}
    if inbound_signals:
        for k, v in inbound_signals.items():
            try:
                in_map[str(k)] = float(v)
            except (TypeError, ValueError):
                pass

    if input is None:
        from core.VitaLoom.viewports.sr_input_state import SrInputState

        input_snap = SrInputState.empty_snapshot()
    else:
        input_snap = input

    return SceneRuntimeTickContext(
        owner_id=str(getattr(owner, "id", "")),
        owner_type=str(getattr(owner, "entity_type", "")),
        owner_position=(ox, oy),
        owner_radius=r,
        bounds=(int(bounds[0]), int(bounds[1])),
        simulation_time=float(simulation_time),
        delta_time=float(delta_time),
        peers=tuple(snap_list),
        environment=MappingProxyType(env_map),
        topology_neighbor_ids=topo,
        spawn_requests=spawn_requests if spawn_requests is not None else [],
        removal_requests=removal_requests if removal_requests is not None else [],
        damage_requests=damage_requests if damage_requests is not None else [],
        fx_requests=fx_requests if fx_requests is not None else [],
        capabilities=MappingProxyType(cap_map),
        inbound_signals=MappingProxyType(in_map),
        input=input_snap,
        runtime_failure_sink=runtime_failure_sink,
    )
