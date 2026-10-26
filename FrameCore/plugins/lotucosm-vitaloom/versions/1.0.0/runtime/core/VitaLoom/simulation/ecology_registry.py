# -*- coding: utf-8 -*-
"""织机侧生态观测聚合：从 EditorContext 收集各官方轨道的 EcologySnapshot。"""
from __future__ import annotations

from typing import Any, List

from core.Lotucosm.runtime.ecology_observation import (
    EcologyLane,
    EcologySnapshot,
    snapshot_from_ps,
    snapshot_from_sr,
)
from core.VitaLoom.core.service_keys import PS_EXPERIMENT


def collect_ecology_snapshots(editor_context: Any) -> List[EcologySnapshot]:
    """聚合 SR + PS（及未来 PS_REPLAY）只读快照。

    官方插件（EcologyDashboard、社区 HUD）应优先调用本函数，而非直接读 GameViewport 字段。
    """
    out: List[EcologySnapshot] = []
    from core.VitaLoom.simulation.sr_host import get_sr_host

    host = get_sr_host(editor_context)
    try:
        out.append(snapshot_from_sr(host.get_sr_ecology_snapshot()))
    except Exception:
        out.append(snapshot_from_sr({}))

    from core.VitaLoom.core.runtime_capability_registry import (
        resolve_runtime_capability_registry,
    )

    services = resolve_runtime_capability_registry(editor_context)
    svc = services.get(PS_EXPERIMENT) if services is not None else None
    if svc is not None and not callable(getattr(svc, "get_ecology_snapshot", None)):
        svc = None
    if svc is not None:
        try:
            out.append(snapshot_from_ps(svc.get_ecology_snapshot()))
        except Exception:
            out.append(snapshot_from_ps({"ps_active": False, "ps_has_result": False}))
    else:
        out.append(snapshot_from_ps({"ps_active": False, "ps_has_result": False, "ps_service_missing": True}))

    try:
        snap = host.get_sr_ecology_snapshot()
        n_overlay = int(snap.get("overlay_point_count", 0) or 0)
    except Exception:
        n_overlay = 0
    if n_overlay > 0:
        out.append(
            EcologySnapshot(
                lane=EcologyLane.PS_REPLAY,
                active=False,
                session_open=True,
                label="PS 快照叠加",
                population=n_overlay,
                extras={"overlay_points": n_overlay},
            )
        )
    return out
