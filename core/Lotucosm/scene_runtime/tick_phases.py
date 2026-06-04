# -*- coding: utf-8
"""SR 脚本 tick 批次：从 GameViewport 抽出的单批 step_scripts 编排。"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.VitaLoom.viewports.game_viewport import GameViewport

logger = logging.getLogger(__name__)


def run_script_tick_batch(
    host: "GameViewport",
    *,
    entities_batch: list[Any],
    all_e: list[Any],
    dt: float,
    spawn_list: list[Any],
    remove_ids: list[str],
    damage_list: list[tuple[str, float]],
    fx_list: list[Any],
    niche_p: float,
    deriv: float,
    load_before: float,
    peer_scale: float,
    min_horizon: float,
    sr_caps: Any,
    w: int,
    h: int,
    input_snap: Any,
    use_prev_inbound: bool,
) -> None:
    """单批实体脚本 tick；膜 sensor/actuator chemo_gain_scale 继承 hub。"""
    from core.Lotucosm.scene_runtime_ambient import ambient_field_and_gradient, nutrient_gradient_at
    from core.Lotucosm.scene_runtime_context import build_scene_runtime_tick_context

    for entity in entities_batch:
        try:
            peers = [e for e in all_e if e is not entity]
            ox = float(entity.position[0])
            oy = float(entity.position[1])
            field, gx, gy = ambient_field_and_gradient(
                ox,
                oy,
                all_e,
                host._scene_runtime_emissions_prev,
                niche_pressure=niche_p,
            )
            n_pot, ngx, ngy = nutrient_gradient_at(
                ox,
                oy,
                all_e,
                host._scene_runtime_emissions_prev,
                field_grid=getattr(host, "_sr_field_grid", None),
            )
            try:
                entity._sr_last_ambient_field = float(field)
            except Exception as e:
                logger.debug("缓存环境场强失败: %s", e)
            chemo_scale = float(getattr(entity, "sr_chemo_gain_scale", 1.0))
            if str(entity.entity_type) in ("sensor", "actuator"):
                parent = host._parent_organism_for_membrane_child(entity.id)
                if parent is not None:
                    chemo_scale = float(getattr(parent, "sr_chemo_gain_scale", 1.0))
            env = {
                "ambient_field": field,
                "ambient_grad_x": gx,
                "ambient_grad_y": gy,
                "nutrient_potential": n_pot,
                "nutrient_grad_x": ngx,
                "nutrient_grad_y": ngy,
                "world_load": load_before,
                "niche_pressure": niche_p,
                "world_load_derivative": deriv,
                "chemo_gain_scale": chemo_scale,
            }
            if getattr(host, "_sr_game_mode", False):
                env["game_proc_seed"] = int(getattr(host, "_sr_proc_seed", 12345))
                env["game_proc_obstacles"] = int(getattr(host, "_sr_proc_obstacles", 5))
                env["game_player_id"] = str(getattr(host, "_sr_player_id", "player_rl"))
            try:
                from core.Lotucosm.sr_interoception import interoception_for_entity

                env.update(interoception_for_entity(entity))
            except Exception:
                pass
            mh = max(min_horizon, float(entity.radius) * 6.0)
            topo = host._scene_runtime_neighbor_ids.get(entity.id, frozenset())
            inbound = host._sr_inbound_for_entity(entity.id, use_prev=use_prev_inbound)
            ctx = build_scene_runtime_tick_context(
                owner=entity,
                peers=peers,
                bounds=(w, h),
                simulation_time=host._scene_runtime_time,
                delta_time=dt,
                neighbor_radius_scale=peer_scale,
                min_horizon=mh,
                environment=env,
                topology_neighbor_ids=topo,
                spawn_requests=spawn_list,
                removal_requests=remove_ids,
                damage_requests=damage_list,
                fx_requests=fx_list,
                capabilities=sr_caps,
                inbound_signals=inbound,
                input=input_snap,
            )
            entity.step_scripts(ctx)
        except Exception as exc:
            logger.warning("更新场景实体失败: %s", exc)
