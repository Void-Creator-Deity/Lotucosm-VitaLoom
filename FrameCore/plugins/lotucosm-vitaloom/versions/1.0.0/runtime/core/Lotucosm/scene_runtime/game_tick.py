# -*- coding: utf-8
"""游戏模式瘦 tick：跳过 PVAEC 膜/chemo/生物圈管道。"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport

logger = logging.getLogger(__name__)


def step_game_runtime(host: "GameViewport", dt: float) -> None:
    """ScriptBase 游戏轨单帧：仅 game_actor/game_prop + 物理 + 碰撞 + HUD。"""
    host._scene_runtime_time += dt
    sw, sh = host._scene_bounds()
    w, h = int(sw), int(sh)
    all_e = list(host.scene_runtime_entities)
    spawn_list: list[Any] = []
    remove_ids: list[str] = []
    damage_list: list[tuple[str, float]] = []
    fx_list: list[Any] = []
    project_path = getattr(host.editor_context, "current_project_path", None)

    for entity in all_e:
        entity.emission_strength = 0.0
        entity.sr_channel_out = {}

    input_snap = host._sr_input_snapshot()
    batch_common = dict(
        all_e=all_e,
        dt=dt,
        spawn_list=spawn_list,
        remove_ids=remove_ids,
        damage_list=damage_list,
        fx_list=fx_list,
        niche_p=0.0,
        deriv=0.0,
        load_before=0.0,
        peer_scale=14.0,
        min_horizon=340.0,
        sr_caps=host._sr_caps_game(),
        w=w,
        h=h,
        input_snap=input_snap,
    )
    game_entities = [
        e
        for e in all_e
        if str(getattr(e, "entity_type", "")) in ("game_actor", "game_prop")
    ]
    host._run_script_tick_batch(entities_batch=game_entities, use_prev_inbound=False, **batch_common)

    try:
        host._process_sr_damage_requests(damage_list, remove_ids)
    except Exception as e:
        logger.warning("游戏伤害处理失败: %s", e)
    try:
        from core.Lotucosm.sr_game_effects import create_fx_state, ingest_fx_requests

        if getattr(host, "_sr_game_fx", None) is None:
            host._sr_game_fx = create_fx_state()
        ingest_fx_requests(host._sr_game_fx, fx_list)
    except Exception as e:
        logger.warning("游戏特效入队失败: %s", e)

    try:
        host._process_sr_removal_requests(remove_ids)
    except Exception as e:
        logger.warning("SR 移除实体失败: %s", e)

    try:
        host._process_sr_spawn_requests(spawn_list, project_path)
    except Exception as e:
        logger.warning("SR 动态生成实体失败: %s", e)

    all_e = list(host.scene_runtime_entities)
    world = getattr(host, "_sr_physics_world", None)
    if world is None:
        from core.Lotucosm.sr_physics2d import SrPhysics2DConfig, SrPhysics2DWorld

        cfg = getattr(host, "_sr_physics_cfg", None)
        if not isinstance(cfg, SrPhysics2DConfig):
            cfg = SrPhysics2DConfig()
        world = SrPhysics2DWorld(cfg)
    try:
        world.step_for_viewport(host, all_e, dt, float(w), float(h))
    except Exception as e:
        logger.warning("游戏 2D 物理步进失败: %s", e)

    try:
        from core.Lotucosm.sr_game_effects import update_game_fx

        if getattr(host, "_sr_game_fx", None) is not None:
            update_game_fx(host._sr_game_fx, dt)
    except Exception as e:
        logger.debug("游戏特效更新失败: %s", e)

    host._scene_runtime_emissions_prev = {}
    host._refresh_sr_hud(list(host.scene_runtime_entities))
    host._maybe_log_scene_episode(dt)
